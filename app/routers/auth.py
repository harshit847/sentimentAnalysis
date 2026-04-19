from datetime import datetime, timezone

from bson import ObjectId
from fastapi import APIRouter, HTTPException, status

from app.db import users_collection
from app.schemas import ProfileUpdate, Token, UserLogin, UserPublic, UserRegister
from app.security import (
    create_access_token,
    CurrentUser,
    hash_password,
    verify_password,
)

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=Token)
async def register(body: UserRegister):
    existing = await users_collection.find_one({"email": body.email.lower()})
    if existing:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already registered")

    now = datetime.now(timezone.utc)
    doc = {
        "email": body.email.lower(),
        "hashed_password": hash_password(body.password),
        "name": body.name.strip(),
        "created_at": now,
    }
    result = await users_collection.insert_one(doc)
    token = create_access_token(str(result.inserted_id))
    return Token(access_token=token)


@router.post("/login", response_model=Token)
async def login(body: UserLogin):
    user = await users_collection.find_one({"email": body.email.lower()})
    if not user or not verify_password(body.password, user["hashed_password"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
        )
    token = create_access_token(str(user["_id"]))
    return Token(access_token=token)


@router.get("/me", response_model=UserPublic)
async def me(user: CurrentUser):
    return user


@router.patch("/me", response_model=UserPublic)
async def update_me(user: CurrentUser, body: ProfileUpdate):
    updates: dict = {}
    if body.name is not None:
        updates["name"] = body.name.strip()
    if updates:
        await users_collection.update_one({"_id": ObjectId(user.id)}, {"$set": updates})
    refreshed = await users_collection.find_one({"_id": ObjectId(user.id)})
    if not refreshed:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return UserPublic(
        id=str(refreshed["_id"]),
        email=refreshed["email"],
        name=refreshed.get("name") or "",
        created_at=refreshed.get("created_at"),
    )
