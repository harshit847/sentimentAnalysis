import motor.motor_asyncio

from app.config import get_settings

_settings = get_settings()

if not _settings.MONGO_URI:
    raise RuntimeError("MONGO_URI is not set. Add it to your .env file.")

client = motor.motor_asyncio.AsyncIOMotorClient(_settings.MONGO_URI)
db = client[_settings.DB_NAME]
history_collection = db[_settings.COLLECTION]
users_collection = db[_settings.USERS_COLLECTION]
