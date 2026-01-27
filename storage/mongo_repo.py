from __future__ import annotations
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from bson import ObjectId
from pymongo import ASCENDING, MongoClient, errors
from pymongo.collection import Collection
from storage.base import CallLogRepository
from utils.data_models import CallLog, DateRange, EmailConfig, MasterRecord, MetadataConfig, User

# --- MongoClient Singleton Cache ---
_mongo_clients = {}


def get_mongo_client(mongo_uri: str) -> MongoClient:
    """Get or create a singleton MongoClient for the given URI."""
    if mongo_uri not in _mongo_clients:
        _mongo_clients[mongo_uri] = MongoClient(mongo_uri, serverSelectionTimeoutMS=2000)
        return _mongo_clients[mongo_uri]

    client = _mongo_clients[mongo_uri]
    try:
        client.admin.command("ping")
        return client
    except Exception as e:
        
        if isinstance(e, errors.InvalidOperation):
          new_client = MongoClient(mongo_uri)
          _mongo_clients[mongo_uri] = new_client
          return new_client
        raise


def _normalize_str(v: Any) -> Optional[str]:
    if v is None:
        return None
    s = str(v).strip()
    return s if s else None


class MongoRepository(CallLogRepository):
    def __init__(self, mongo_uri: str, db_name: str):
        self._client = get_mongo_client(mongo_uri)
        self._db = self._client[db_name]
        self._master: Collection = self._db["master"]
        self._metadata: Collection = self._db["metadata"]
        self._calllog: Collection = self._db["callLogs"]
        self._email_config: Collection = self._db["emailConfig"]
        self._users: Collection = self._db["users"]

        # Ensure indexes (safe to call multiple times)
        self._master.create_index([("mobile", ASCENDING), ("uid", ASCENDING)], unique=True)
        self._calllog.create_index([("Date", ASCENDING)])
        self._users.create_index([("username", ASCENDING)], unique=True)

    @staticmethod
    def _remove_none_values(data: Dict[str, Any]) -> Dict[str, Any]:
      return {k: v for k, v in data.items() if v is not None}    

    def close(self) -> None:
        """
        Close the underlying MongoClient connection pool.
        Safe to call multiple times.
        """
        # Close the client and remove it from the module-level cache so
        # future calls to get_mongo_client() will create a fresh client.
        try:
            self._client.close()
        finally:
            # Remove any cached entries that reference this closed client.
            keys_to_remove = [k for k, v in _mongo_clients.items() if v is self._client]
            for k in keys_to_remove:
                del _mongo_clients[k]

    # ---- Master ----
    def master_list(self) -> List[MasterRecord]:
        """Returns all master records as a list of dictionaries."""
        docs = list(self._master.find({}, {"_id": 0}).sort("mobile", 1))
        return [MasterRecord(**d) for d in docs]

    def master_get(self, record_id: str) -> MasterRecord | None:
        """Fetch a single master record by ID."""
        doc = self._master.find_one({"uid": record_id})
        if not doc: return None
        doc.pop("_id", None)
        return MasterRecord(**doc)

    def master_get_by_mobile(self, mobile_no: str) -> MasterRecord | None:
        doc = self._master.find_one({"mobile": _normalize_str(mobile_no)})
        if not doc: return None
        doc.pop("_id", None)
        return MasterRecord(**doc)

    def master_create(self, record: MasterRecord) -> str:
        # If record is a dataclass, call .to_dict() first
        doc = record.to_dict() if hasattr(record, 'to_dict') else record
        
        # Clean the data
        clean_doc = self._remove_none_values(doc)
        
        res = self._master.insert_one(clean_doc)
        return str(res.inserted_id)

    def master_update(self, record_id: str, record: MasterRecord) -> int:
        doc = record.to_dict() if hasattr(record, 'to_dict') else record
        clean_doc = self._remove_none_values(doc)
        result = self._master.update_one({"uid": record_id}, {"$set": clean_doc})
        return result.modified_count > 0

    def master_delete(self, record_id: str) -> None:
        self._master.delete_one({"uid": record_id})

    def master_replace_all(self, records: List[MasterRecord]) -> int:
        self._master.delete_many({})
        if not records:
            return 0
        
        # Clean every record in the list
        clean_records = [self._remove_none_values(rec.to_dict()) for rec in records]

        res = self._master.insert_many(clean_records, ordered=False)
        return len(res.inserted_ids)

    # ---- Call Log ----

    def calllog_create(self, record: CallLog) -> str:
        """
        Creates a new call log entry.
        Accepts a CallLog dataclass instance.
        """
        # 1. Convert to dict
        doc = record.to_dict()
        
        # 2. Clean None values so they aren't stored as null in Mongo
        clean_doc = self._remove_none_values(doc)

        res = self._calllog.insert_one(clean_doc)
        return str(res.inserted_id)

    def calllog_list(self, date_range: Optional[DateRange] = None) -> list[CallLog]:
        """
        Returns a list of CallLog dataclass objects.
        """
        query: dict[str, Any] = {}
        
        if date_range and (date_range.start or date_range.end):
            query["date"] = {}
            if date_range.start:
                # Ensure we start from the very beginning of the start day
                query["date"]["$gte"] = datetime.combine(date_range.start, datetime.min.time())
            if date_range.end:
                # Ensure we include everything up to the very end of the end day
                query["date"]["$lte"] = datetime.combine(date_range.end, datetime.max.time())
                
        # Projection {"_id": 0} allows us to unpack directly into CallLog(**doc)
        docs = list(self._calllog.find(query, {"_id": 0}).sort("date", -1))
        
        # Map raw dictionaries back into Dataclass objects
        return [CallLog(**d) for d in docs]
    
    # ---- User Management ----
    def user_list(self) -> list[User]:
        """Returns all users as a list of User dataclass objects."""
        # We fetch the fields that match our User dataclass
        docs = list(self._users.find({}, {"_id": 0}))
        return [User(**d) for d in docs]

    def user_get(self, user_id: str) -> User | None:
        """Fetch a single user by their MongoDB ObjectId."""
        doc = self._users.find_one({"_id": ObjectId(user_id)}, {"_id": 0})
        return User(**doc) if doc else None

    def user_get_by_username(self, username: str) -> User | None:
        """Fetch a single user by their username."""
        doc = self._users.find_one({"username": username}, {"_id": 0})
        return User(**doc) if doc else None

    def user_create(self, user_obj: User) -> str:
        """
        Creates a new user. 
        Expects a User dataclass instance.
        """
        doc = self._remove_none_values(user_obj.to_dict())
        
        res = self._users.insert_one(doc)
        return str(res.inserted_id)

    def user_update(self, user_obj: User) -> bool:
        """
        Updates specific user fields (e.g., password).
        """
        clean_updates = self._remove_none_values(user_obj.to_dict())
        
        # We use $set to only change the fields provided in the updates dict
        result = self._users.update_one(
            {"username": clean_updates["username"]},
            {"$set": clean_updates}
        )
        return result.modified_count > 0

    def user_delete(self, user_id: str) -> None:
        """Deletes a user by their MongoDB ObjectId."""
        self._users.delete_one({"_id": ObjectId(user_id)})
        
    # ---- Email Configuration ----
    def email_config_get(self) -> EmailConfig | None:
        """
        Get email configuration from database.
        Returns an EmailConfig dataclass instance or None.
        """
        # We use a fixed ID "email_settings" as there is only one config
        doc = self._email_config.find_one({"_id": "email_settings"})
        
        if doc:
            # Remove the internal MongoDB _id so it doesn't break the dataclass init
            doc.pop("_id", None)
            return EmailConfig(**doc)
        return None

    def email_config_save(self, config_obj: EmailConfig) -> None:
        """
        Save email configuration to database using EmailConfig dataclass.
        """
        doc = self._remove_none_values(config_obj.to_dict())
        
        self._email_config.update_one(
            {"_id": "email_settings"},
            {"$set": doc},
            upsert=True
        )

    def email_config_delete(self) -> None:
        """Delete email configuration from database."""
        self._email_config.delete_one({"_id": "email_settings"})
        
    # ---- Metadata Configuration ----
    def metadata_get(self) -> Optional[MetadataConfig]:
      """Get all metadata data using projection to exclude metadata."""
      doc = self._metadata.find_one({"_id": "dropdown_values"}, {"_id": 0})
      return doc

    def metadata_update(self, field_key: str, updated_array: list, username: str) -> None:
        """Atomic update: Only update the specific field array and timestamp."""
        # We use $set on the specific key (e.g., 'projects') 
        # without touching other fields like 'designations'.
        self._metadata.update_one(
            {"_id": "dropdown_values"},
            {
                "$set": {
                    field_key: updated_array,
                    "updated_by": username,
                    "updated_at": datetime.now(timezone.utc),
                }
            },
            upsert=True
        )

    def metadata_save(self, data: Dict[MetadataConfig]) -> None:
        """Save metadata configuration to database."""
        clean_data = self._remove_none_values(data)
        self._metadata.update_one(
            {"_id": "dropdown_values"},
            {"$set": clean_data},
            upsert=True
        )

    # ---- Application Activation (Licensing) ----
    def get_activation_record(self) -> Optional[Dict[str, Any]]:
        """Fetch the activation info from the appConfig collection."""
        config = self._db["appConfig"].find_one({"_id": "active"})
        if config and "activation" in config:
            return config["activation"]
        return None

    def save_activation(self, name: str, email: str, mobile: str, key: str, hwid: str):
        """Save full activation details and lock them to the HWID."""
        activation_data = {
            "name": name,
            "email": email,
            "mobile": mobile,
            "key": key,
            "hwid": hwid,
            "activated_at": datetime.utcnow()
        }
        self._db["appConfig"].update_one(
            {"_id": "active"},
            {"$set": {"activation": activation_data}},
            upsert=True
        )

    def get_trial_status(self) -> Optional[datetime]:
        """Retrieve the trial start date if it exists."""
        config = self._db["appConfig"].find_one({"_id": "active"})
        if config and "trial_start_date" in config:
            return config["trial_start_date"]
        return None
