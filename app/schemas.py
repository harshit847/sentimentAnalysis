from datetime import datetime

from pydantic import BaseModel, EmailStr, Field


class AnalyzeRequest(BaseModel):
    text: str = Field(..., min_length=1, description="Text to analyze for sentiment")


class SentimentScores(BaseModel):
    neg: float
    neu: float
    pos: float
    compound: float


class AnalyzeResponse(BaseModel):
    sentiment: str
    confidence: float
    scores: SentimentScores
    length: int


# Auth
class UserRegister(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=128)
    name: str = Field("", max_length=120)


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    user_id: str


class UserPublic(BaseModel):
    id: str
    email: str
    name: str
    created_at: datetime | None = None


class ProfileUpdate(BaseModel):
    name: str | None = Field(None, max_length=120)


# Analyze unified
class VoiceAnalyzeRequest(BaseModel):
    text: str = Field(..., min_length=1, description="Transcribed speech text")
    locale: str | None = Field(None, description="Optional BCP-47 locale from Web Speech API")


class TextAnalyzeResult(BaseModel):
    type: str = "text"
    sentiment: str
    confidence: float
    scores: SentimentScores
    length: int
    dominant_label: str
    explanation: str
    suggestions: list[str] = []


class FaceAnalyzeResult(BaseModel):
    type: str = "face"
    emotion: str
    confidence: float
    emotions: dict[str, float] = {}
    faces: int = 0
    dominant_label: str
    explanation: str
    suggestions: list[str] = []
    filename: str | None = None


class VoiceAnalyzeResult(BaseModel):
    type: str = "voice"
    sentiment: str
    confidence: float
    scores: SentimentScores
    length: int
    dominant_label: str
    locale: str | None = None
    explanation: str
    suggestions: list[str] = []

