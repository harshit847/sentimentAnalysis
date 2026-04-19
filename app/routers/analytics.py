from collections import defaultdict
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Query

from app.db import history_collection
from app.security import CurrentUser

router = APIRouter(prefix="/analytics", tags=["analytics"])


@router.get("")
async def analytics(
    user: CurrentUser,
    days: int = Query(30, ge=1, le=365, description="Trend window in days"),
):
    uid = user.id
    now = datetime.now(timezone.utc)
    start = now - timedelta(days=days)

    total = await history_collection.count_documents({"user_id": uid})

    # Distribution by analysis_type
    by_type_pipeline = [
        {"$match": {"user_id": uid}},
        {"$group": {"_id": "$analysis_type", "count": {"$sum": 1}}},
    ]
    by_type_raw = await history_collection.aggregate(by_type_pipeline).to_list(None)
    by_type = {d["_id"]: d["count"] for d in by_type_raw if d.get("_id")}

    # Sentiment distribution (text + voice)
    sent_pipeline = [
        {"$match": {"user_id": uid, "analysis_type": {"$in": ["text", "voice"]}}},
        {"$group": {"_id": "$sentiment", "count": {"$sum": 1}}},
    ]
    sent_raw = await history_collection.aggregate(sent_pipeline).to_list(None)
    sentiment_dist = [
        {"label": d["_id"] or "unknown", "count": d["count"]}
        for d in sent_raw
        if d.get("_id") is not None
    ]

    # Face emotion distribution
    face_pipeline = [
        {"$match": {"user_id": uid, "analysis_type": "face"}},
        {"$group": {"_id": "$emotion", "count": {"$sum": 1}}},
    ]
    face_raw = await history_collection.aggregate(face_pipeline).to_list(None)
    emotion_dist = [
        {"label": d["_id"] or "unknown", "count": d["count"]}
        for d in face_raw
        if d.get("_id") is not None
    ]

    # Daily trend (counts per day in window)
    match_time = {
        "user_id": uid,
        "timestamp": {"$gte": start},
    }
    trend_cursor = history_collection.find(
        match_time,
        {"timestamp": 1, "analysis_type": 1},
    ).sort("timestamp", 1)

    daily: dict[str, dict[str, int]] = defaultdict(lambda: {"text": 0, "face": 0, "voice": 0})
    async for doc in trend_cursor:
        ts = doc.get("timestamp")
        if not isinstance(ts, datetime):
            continue
        day = ts.astimezone(timezone.utc).date().isoformat()
        at = doc.get("analysis_type") or "text"
        if at in daily[day]:
            daily[day][at] += 1

    trend = sorted(
        [
            {
                "date": k,
                "text": v["text"],
                "face": v["face"],
                "voice": v["voice"],
                "total": v["text"] + v["face"] + v["voice"],
            }
            for k, v in daily.items()
        ],
        key=lambda x: x["date"],
    )

    return {
        "total": total,
        "window_days": days,
        "by_type": by_type,
        "sentiment_distribution": sentiment_dist,
        "emotion_distribution": emotion_dist,
        "daily_trend": trend,
    }
