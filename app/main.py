from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import cors_origin_list
from app.db import history_collection, users_collection
from app.routers import analytics, analyze, auth, history


@asynccontextmanager
async def lifespan(_: FastAPI):
    try:
        await users_collection.create_index("email", unique=True)
    except Exception:
        pass
    try:
        await history_collection.create_index([("user_id", 1), ("timestamp", -1)])
    except Exception:
        pass
    yield


app = FastAPI(
    title="Sentiment SaaS API",
    version="2.0.0",
    description="FastAPI backend: JWT auth, VADER sentiment, FER + OpenCV faces, MongoDB history, OpenAI explanations.",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origin_list(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(analyze.router)
app.include_router(history.router)
app.include_router(analytics.router)


@app.get("/")
def root():
    return {"message": "Sentiment SaaS API", "version": "2.0.0"}


@app.get("/health")
def health():
    return {"status": "ok", "service": "Sentiment SaaS API"}


@app.get("/db-health")
async def db_health():
    try:
        doc = await history_collection.find_one()
        return {"status": "connected", "sample": bool(doc)}
    except Exception as e:
        return {"status": "error", "detail": str(e)}
