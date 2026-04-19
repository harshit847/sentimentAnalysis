from dataclasses import dataclass
from functools import lru_cache
import os

from dotenv import load_dotenv

load_dotenv()


def _env_str(key: str, default: str = "") -> str:
    v = os.getenv(key)
    return default if v is None else v


def _env_int(key: str, default: int) -> int:
    v = os.getenv(key)
    if v is None or v.strip() == "":
        return default
    try:
        return int(v)
    except ValueError:
        return default


@dataclass(frozen=True)
class Settings:
    MONGO_URI: str
    DB_NAME: str
    COLLECTION: str
    USERS_COLLECTION: str
    JWT_SECRET: str
    JWT_ALGORITHM: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int
    OPENAI_API_KEY: str
    OPENAI_MODEL: str
    CORS_ORIGINS: str


@lru_cache
def get_settings() -> Settings:
    return Settings(
        MONGO_URI=_env_str("MONGO_URI", ""),
        DB_NAME=_env_str("DB_NAME", "sentimentdb"),
        COLLECTION=_env_str("COLLECTION", "history"),
        USERS_COLLECTION=_env_str("USERS_COLLECTION", "users"),
        JWT_SECRET=_env_str("JWT_SECRET", "change-me-in-production"),
        JWT_ALGORITHM=_env_str("JWT_ALGORITHM", "HS256"),
        ACCESS_TOKEN_EXPIRE_MINUTES=_env_int("ACCESS_TOKEN_EXPIRE_MINUTES", 60 * 24 * 7),
        OPENAI_API_KEY=_env_str("OPENAI_API_KEY", ""),
        OPENAI_MODEL=_env_str("OPENAI_MODEL", "gpt-4o-mini"),
        CORS_ORIGINS=_env_str(
            "CORS_ORIGINS",
            "http://localhost:3000,http://127.0.0.1:3000",
        ),
    )


def cors_origin_list() -> list[str]:
    raw = get_settings().CORS_ORIGINS
    return [o.strip() for o in raw.split(",") if o.strip()]
