from __future__ import annotations
from dataclasses import asdict, dataclass
from datetime import datetime
from typing import Literal, Optional, Tuple
from pymongo import MongoClient

Backend = Literal["mongodb"]

@dataclass
class MongoSettings:
    uri: str
    database: str
    backup_path: str

@dataclass
class ActivationInfo:
    name: str
    email: str
    mobile: str
    key: str

@dataclass
class AppSettings:
    backend: Backend
    mongodb: MongoSettings
    createdAt: Optional[datetime] = None
    activation: Optional[ActivationInfo] = None
    authenticated_user: Optional[str] = None  # Store last authenticated username


def test_mongo_connection(mongoSettings: MongoSettings) -> Tuple[bool, str]:
    try:
        uri, database = (mongoSettings.uri, mongoSettings.database)
        client = MongoClient(uri, serverSelectionTimeoutMS=5000)
        client.admin.command("ping")
        # ensure db exists
        _ = client[database].list_collection_names()
        client.close()
        return True, "MongoDB connection OK."
    except Exception as e:
        return False, f"MongoDB connection failed: {e}"


def _save_settings_to_mongo(appSettings: AppSettings) -> None:
    if not appSettings.mongodb:
        raise ValueError("Missing MongoDB settings")
    uri, database = (appSettings.mongodb.uri, appSettings.mongodb.database)
    client = MongoClient(uri)
    try:
        db = client[database]
        col = db["appConfig"]

        # This converts the dataclass to a dict, including the nested activation field
        appSettings.createdAt = datetime.utcnow()
        appConfig = asdict(appSettings)
        # We use $set so we don't accidentally wipe existing fields like 'createdAt'
        col.update_one({"_id": "active"}, {"$set": appConfig}, upsert=True)
    finally:
        client.close()


def save_settings(appSettings: AppSettings) -> None:
    if appSettings.backend == "mongodb":
        _save_settings_to_mongo(appSettings)
    else:
        raise ValueError(f"Unsupported backend: {appSettings.backend}")