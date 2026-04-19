import csv
import io
from datetime import datetime
from typing import Any

from bson import ObjectId
from bson.errors import InvalidId
from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import StreamingResponse

from app.db import history_collection
from app.security import CurrentUser

router = APIRouter(prefix="/history", tags=["history"])


def _serialize_doc(doc: dict[str, Any]) -> dict[str, Any]:
    out = dict(doc)
    out["id"] = str(out.pop("_id"))
    out["user_id"] = str(out.get("user_id", ""))
    return out


@router.get("")
async def list_history(
    user: CurrentUser,
    limit: int = Query(50, ge=1, le=200),
    skip: int = Query(0, ge=0),
    analysis_type: str | None = Query(None, description="Filter: text, face, or voice"),
):
    q: dict[str, Any] = {"user_id": user.id}
    if analysis_type:
        q["analysis_type"] = analysis_type

    cursor = history_collection.find(q).sort("timestamp", -1).skip(skip).limit(limit)
    items = [_serialize_doc(d) async for d in cursor]
    total = await history_collection.count_documents(q)
    return {"total": total, "limit": limit, "skip": skip, "items": items}


@router.get("/export/csv")
async def export_csv(
    user: CurrentUser,
    analysis_type: str | None = Query(None),
):
    q: dict[str, Any] = {"user_id": user.id}
    if analysis_type:
        q["analysis_type"] = analysis_type

    cursor = history_collection.find(q).sort("timestamp", -1)
    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow(
        [
            "id",
            "timestamp",
            "analysis_type",
            "dominant_label",
            "confidence",
            "text",
            "sentiment",
            "emotion",
            "faces",
            "explanation",
        ]
    )
    async for doc in cursor:
        did = str(doc.get("_id", ""))
        ts = doc.get("timestamp")
        ts_s = ts.isoformat() if isinstance(ts, datetime) else ""
        writer.writerow(
            [
                did,
                ts_s,
                doc.get("analysis_type", ""),
                doc.get("dominant_label", ""),
                doc.get("confidence", ""),
                (doc.get("text") or "")[:5000],
                doc.get("sentiment", ""),
                doc.get("emotion", ""),
                doc.get("faces", ""),
                (doc.get("explanation") or "").replace("\n", " ")[:8000],
            ]
        )

    buf.seek(0)
    filename = f"sentiment-history-{user.id[:8]}.csv"
    return StreamingResponse(
        iter([buf.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.delete("/{item_id}")
async def delete_item(user: CurrentUser, item_id: str):
    try:
        oid = ObjectId(item_id)
    except (InvalidId, TypeError):
        raise HTTPException(status_code=400, detail="Invalid id") from None

    result = await history_collection.delete_one({"_id": oid, "user_id": user.id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Not found")
    return {"deleted": True}
