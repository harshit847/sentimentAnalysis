from datetime import datetime, timezone

import cv2
import numpy as np
from fastapi import APIRouter, File, HTTPException, UploadFile

from app.db import history_collection
from app.face import analyze_face_image
from app.schemas import (
    AnalyzeRequest,
    FaceAnalyzeResult,
    SentimentScores,
    TextAnalyzeResult,
    VoiceAnalyzeRequest,
    VoiceAnalyzeResult,
)
from app.security import CurrentUser
from app.sentiment import VaderSentimentService
from app.services.explanation import (
    explain_face_emotion,
    explain_text_sentiment,
    explain_voice_sentiment,
)

router = APIRouter(prefix="/analyze", tags=["analyze"])
sentiment_service = VaderSentimentService()


def _now():
    return datetime.now(timezone.utc)


@router.post("/text", response_model=TextAnalyzeResult)
async def analyze_text(payload: AnalyzeRequest, user: CurrentUser):
    result = sentiment_service.analyze(payload.text)
    scores = result["scores"]
    expl, sugs = await explain_text_sentiment(payload.text, result["label"], scores)

    doc = {
        "user_id": user.id,
        "analysis_type": "text",
        "timestamp": _now(),
        "dominant_label": result["label"],
        "confidence": round(result["confidence"], 4),
        "scores": scores,
        "text": payload.text,
        "sentiment": result["label"],
        "length": len(payload.text),
        "explanation": expl,
        "suggestions": sugs,
    }
    await history_collection.insert_one(doc)

    return TextAnalyzeResult(
        sentiment=result["label"],
        confidence=round(result["confidence"], 4),
        scores=SentimentScores(**scores),
        length=len(payload.text),
        dominant_label=result["label"],
        explanation=expl,
        suggestions=sugs,
    )


@router.post("/face", response_model=FaceAnalyzeResult)
async def analyze_face(user: CurrentUser, file: UploadFile = File(...)):
    try:
        contents = await file.read()
        npimg = np.frombuffer(contents, np.uint8)
        img = cv2.imdecode(npimg, cv2.IMREAD_COLOR)
        if img is None:
            raise HTTPException(status_code=400, detail="Invalid image file")

        raw = analyze_face_image(img)
        emotion = raw.get("emotion") or "neutral"
        confidence = float(raw.get("confidence") or 0.0)
        emotions = raw.get("emotions") or {}
        faces = int(raw.get("faces") or 0)

        expl, sugs = await explain_face_emotion(emotion, emotions, faces)

        doc = {
            "user_id": user.id,
            "analysis_type": "face",
            "timestamp": _now(),
            "dominant_label": emotion,
            "confidence": confidence,
            "emotions": emotions,
            "emotion": emotion,
            "faces": faces,
            "filename": file.filename,
            "explanation": expl,
            "suggestions": sugs,
        }
        await history_collection.insert_one(doc)

        return FaceAnalyzeResult(
            emotion=emotion,
            confidence=confidence,
            emotions=emotions,
            faces=faces,
            dominant_label=emotion,
            explanation=expl,
            suggestions=sugs,
            filename=file.filename,
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.post("/voice", response_model=VoiceAnalyzeResult)
async def analyze_voice(payload: VoiceAnalyzeRequest, user: CurrentUser):
    result = sentiment_service.analyze(payload.text)
    scores = result["scores"]
    expl, sugs = await explain_voice_sentiment(payload.text, result["label"], scores)

    doc = {
        "user_id": user.id,
        "analysis_type": "voice",
        "timestamp": _now(),
        "dominant_label": result["label"],
        "confidence": round(result["confidence"], 4),
        "scores": scores,
        "text": payload.text,
        "sentiment": result["label"],
        "length": len(payload.text),
        "locale": payload.locale,
        "explanation": expl,
        "suggestions": sugs,
    }
    await history_collection.insert_one(doc)

    return VoiceAnalyzeResult(
        sentiment=result["label"],
        confidence=round(result["confidence"], 4),
        scores=SentimentScores(**scores),
        length=len(payload.text),
        dominant_label=result["label"],
        locale=payload.locale,
        explanation=expl,
        suggestions=sugs,
    )
