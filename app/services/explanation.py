import json
import re

from app.config import get_settings


def _fallback_text(sentiment: str, scores: dict[str, float]) -> tuple[str, list[str]]:
    compound = scores.get("compound", 0.0)
    expl = (
        f"The text reads as **{sentiment}** overall (compound score {compound:.2f}). "
        "VADER weighs neg/neu/pos word intensities to produce this label."
    )
    tips = [
        "Try paraphrasing to see how word choice shifts the score.",
        "Short texts can swing quickly—add context for stabler readings.",
    ]
    return expl, tips


def _fallback_face(emotion: str, emotions: dict[str, float]) -> tuple[str, list[str]]:
    expl = (
        f"The strongest face cue detected is **{emotion}** among FER probabilities: "
        f"{json.dumps(emotions, indent=0)}."
    )
    tips = [
        "Ensure good lighting and face the camera for clearer reads.",
        "Occlusions or extreme angles can reduce confidence.",
    ]
    return expl, tips


async def explain_text_sentiment(text: str, sentiment: str, scores: dict[str, float]) -> tuple[str, list[str]]:
    settings = get_settings()
    if not settings.OPENAI_API_KEY:
        return _fallback_text(sentiment, scores)

    try:
        from openai import AsyncOpenAI

        client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
        system = (
            "You help users understand sentiment analysis. Be concise, friendly, and practical. "
            "Respond with valid JSON only: {\"explanation\": string, \"suggestions\": string[] } "
            "with 2-4 short suggestions."
        )
        user = json.dumps(
            {
                "text": text[:4000],
                "label": sentiment,
                "vader_scores": scores,
            }
        )
        resp = await client.chat.completions.create(
            model=settings.OPENAI_MODEL,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            temperature=0.4,
            max_tokens=500,
        )
        raw = (resp.choices[0].message.content or "").strip()
        m = re.search(r"\{[\s\S]*\}", raw)
        if m:
            raw = m.group(0)
        data = json.loads(raw)
        expl = str(data.get("explanation", "")).strip() or _fallback_text(sentiment, scores)[0]
        sugs = data.get("suggestions") or []
        if not isinstance(sugs, list):
            sugs = []
        sugs = [str(s).strip() for s in sugs if str(s).strip()]
        if not sugs:
            sugs = _fallback_text(sentiment, scores)[1]
        return expl, sugs[:6]
    except Exception:
        return _fallback_text(sentiment, scores)


async def explain_face_emotion(
    emotion: str, emotions: dict[str, float], faces: int
) -> tuple[str, list[str]]:
    settings = get_settings()
    if not settings.OPENAI_API_KEY:
        return _fallback_face(emotion, emotions)

    try:
        from openai import AsyncOpenAI

        client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
        system = (
            "You interpret facial emotion model outputs (FER-style class probabilities). "
            "Do not claim medical or psychological diagnosis. "
            "Respond JSON only: {\"explanation\": string, \"suggestions\": string[] }."
        )
        user = json.dumps(
            {
                "dominant_emotion": emotion,
                "probabilities": emotions,
                "faces_detected": faces,
            }
        )
        resp = await client.chat.completions.create(
            model=settings.OPENAI_MODEL,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            temperature=0.3,
            max_tokens=450,
        )
        raw = (resp.choices[0].message.content or "").strip()
        m = re.search(r"\{[\s\S]*\}", raw)
        if m:
            raw = m.group(0)
        data = json.loads(raw)
        expl = str(data.get("explanation", "")).strip() or _fallback_face(emotion, emotions)[0]
        sugs = data.get("suggestions") or []
        if not isinstance(sugs, list):
            sugs = []
        sugs = [str(s).strip() for s in sugs if str(s).strip()]
        if not sugs:
            sugs = _fallback_face(emotion, emotions)[1]
        return expl, sugs[:6]
    except Exception:
        return _fallback_face(emotion, emotions)


async def explain_voice_sentiment(text: str, sentiment: str, scores: dict[str, float]) -> tuple[str, list[str]]:
    settings = get_settings()
    if not settings.OPENAI_API_KEY:
        t = _fallback_text(sentiment, scores)
        return (
            "Voice input was transcribed to text; sentiment follows the text analysis.\n\n" + t[0],
            t[1],
        )

    try:
        from openai import AsyncOpenAI

        client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
        system = (
            "The user spoke and the transcript was analyzed with VADER. "
            "Note transcription errors can affect sentiment. "
            "Respond JSON only: {\"explanation\": string, \"suggestions\": string[] }."
        )
        user = json.dumps(
            {
                "transcript": text[:4000],
                "label": sentiment,
                "vader_scores": scores,
            }
        )
        resp = await client.chat.completions.create(
            model=settings.OPENAI_MODEL,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            temperature=0.4,
            max_tokens=500,
        )
        raw = (resp.choices[0].message.content or "").strip()
        m = re.search(r"\{[\s\S]*\}", raw)
        if m:
            raw = m.group(0)
        data = json.loads(raw)
        expl = str(data.get("explanation", "")).strip()
        if not expl:
            expl = _fallback_text(sentiment, scores)[0]
        sugs = data.get("suggestions") or []
        if not isinstance(sugs, list):
            sugs = []
        sugs = [str(s).strip() for s in sugs if str(s).strip()]
        if not sugs:
            sugs = _fallback_text(sentiment, scores)[1]
        return expl, sugs[:6]
    except Exception:
        t = _fallback_text(sentiment, scores)
        return (
            "Voice input was transcribed to text; sentiment follows the text analysis.\n\n" + t[0],
            t[1],
        )
