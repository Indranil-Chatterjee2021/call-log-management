from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional

from pymongo import ASCENDING, MongoClient

# --- MongoClient Singleton Cache ---
_mongo_clients = {}


def get_mongo_client(mongo_uri: str) -> MongoClient:
    """Get or create a singleton MongoClient for the given URI.

    Defensive behaviour: if the cached client was previously closed (for
    example after a logout that calls `repo.close()`), attempting to use it
    raises pymongo.errors.InvalidOperation. We detect that by issuing a
    lightweight `ping` and recreate the client if it's closed.
    """
    # Fast path: not cached -> create and store
    if mongo_uri not in _mongo_clients:
        _mongo_clients[mongo_uri] = MongoClient(mongo_uri)
        return _mongo_clients[mongo_uri]

    client = _mongo_clients[mongo_uri]
    # Check if the cached client is usable. A closed client will raise
    # InvalidOperation when used; only in that case we recreate it.
    try:
        # Use a short timeout so this check is quick in failure scenarios.
        client.admin.command("ping", serverSelectionTimeoutMS=2000)
        return client
    except Exception as e:
        # Import here to avoid adding the dependency at module import time
        # beyond the existing MongoClient import.
        from pymongo.errors import InvalidOperation

        if isinstance(e, InvalidOperation):
            # Replace closed client with a fresh one
            new_client = MongoClient(mongo_uri)
            _mongo_clients[mongo_uri] = new_client
            return new_client
        # For other exceptions (network/DNS issues), re-raise so callers
        # can observe the underlying connectivity error instead of masking it.
        raise
from pymongo.collection import Collection

from .base import CallLogRepository, CallLogRecord, DateRange, MasterRecord, UserRecord


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
        self._calllog: Collection = self._db["callLogEntries"]
        self._users: Collection = self._db["users"]

        # Ensure indexes (safe to call multiple times)
        self._master.create_index([("MobileNo", ASCENDING)], unique=True)
        self._calllog.create_index([("Date", ASCENDING)])
        self._users.create_index([("username", ASCENDING)], unique=True)

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
        docs = list(self._master.find({}, {"_id": 1, **{k: 1 for k in _MASTER_FIELDS}}).sort("MobileNo", 1))
        return [_doc_to_master(d) for d in docs]

    def master_get(self, record_id: str) -> Optional[MasterRecord]:
        from bson import ObjectId

        doc = self._master.find_one({"_id": ObjectId(record_id)})
        return _doc_to_master(doc) if doc else None

    def master_get_by_mobile(self, mobile_no: str) -> Optional[MasterRecord]:
        doc = self._master.find_one({"MobileNo": _normalize_str(mobile_no)})
        return _doc_to_master(doc) if doc else None

    def master_create(self, record: MasterRecord) -> str:
        doc = _master_to_doc(record)
        res = self._master.insert_one(doc)
        return str(res.inserted_id)

    def master_update(self, record_id: str, record: MasterRecord) -> None:
        from bson import ObjectId

        doc = _master_to_doc(record)
        doc["UpdatedDate"] = datetime.utcnow()
        self._master.update_one({"_id": ObjectId(record_id)}, {"$set": doc})

    def master_delete(self, record_id: str) -> None:
        from bson import ObjectId

        self._master.delete_one({"_id": ObjectId(record_id)})

    def master_replace_all(self, records: List[MasterRecord]) -> int:
        self._master.delete_many({})
        if not records:
            return 0
        docs = [_master_to_doc(r) for r in records]
        res = self._master.insert_many(docs, ordered=False)
        return len(res.inserted_ids)

    # ---- Call Log ----
    def calllog_create(self, record: CallLogRecord) -> str:
        doc: Dict[str, Any] = {k: _normalize_str(record.get(k)) for k in _CALLLOG_TEXT_FIELDS}
        date_val = record.get("Date")
        doc["Date"] = date_val if isinstance(date_val, datetime) else datetime.utcnow()
        doc["CreatedDate"] = datetime.utcnow()
        doc["UpdatedDate"] = datetime.utcnow()
        res = self._calllog.insert_one(doc)
        return str(res.inserted_id)

    def calllog_list(self, date_range: DateRange) -> List[CallLogRecord]:
        query: Dict[str, Any] = {}
        if date_range.start or date_range.end:
            query["Date"] = {}
            if date_range.start:
                query["Date"]["$gte"] = date_range.start
            if date_range.end:
                query["Date"]["$lte"] = date_range.end
        docs = list(self._calllog.find(query).sort("Date", -1))
        return [_doc_to_calllog(d) for d in docs]

    # ---- User Management ----
    def user_list(self) -> List[UserRecord]:
        docs = list(self._users.find({}, {"_id": 1, "username": 1, "CreatedDate": 1}))
        return [_doc_to_user(d) for d in docs]

    def user_get(self, user_id: str) -> Optional[UserRecord]:
        from bson import ObjectId
        doc = self._users.find_one({"_id": ObjectId(user_id)})
        return _doc_to_user(doc) if doc else None

    def user_get_by_username(self, username: str) -> Optional[UserRecord]:
        doc = self._users.find_one({"username": username})
        return _doc_to_user(doc) if doc else None

    def user_create(self, record: UserRecord) -> str:
        doc = {
            "username": record.get("username"),
            "password": record.get("password"),
            "CreatedDate": datetime.utcnow(),
        }
        res = self._users.insert_one(doc)
        return str(res.inserted_id)

    def user_update(self, user_id: str, record: UserRecord) -> None:
        from bson import ObjectId
        update_data = {}
        if "password" in record:
            update_data["password"] = record["password"]
        if update_data:
            update_data["UpdatedDate"] = datetime.utcnow()
            self._users.update_one({"_id": ObjectId(user_id)}, {"$set": update_data})

    def user_delete(self, user_id: str) -> None:
        from bson import ObjectId
        self._users.delete_one({"_id": ObjectId(user_id)})

    # ---- Email Configuration ----
    def email_config_get(self) -> Optional[Dict[str, Any]]:
        """Get email configuration from database."""
        doc = self._db["emailConfig"].find_one({"_id": "email_settings"})
        if doc:
            return {
                "smtp_server": doc.get("smtp_server"),
                "smtp_port": doc.get("smtp_port"),
                "smtp_user": doc.get("smtp_user"),
                "smtp_password": doc.get("smtp_password"),
            }
        return None

    def email_config_save(self, config: Dict[str, Any]) -> None:
        """Save email configuration to database."""
        self._db["emailConfig"].update_one(
            {"_id": "email_settings"},
            {"$set": {
                "smtp_server": config.get("smtp_server"),
                "smtp_port": config.get("smtp_port"),
                "smtp_user": config.get("smtp_user"),
                "smtp_password": config.get("smtp_password"),
                "UpdatedDate": datetime.utcnow()
            }},
            upsert=True
        )

    def email_config_delete(self) -> None:
        """Delete email configuration from database."""
        self._db["emailConfig"].delete_one({"_id": "email_settings"})

    # ---- Misc/Dropdown Data Configuration ----
    def misc_data_get(self) -> Optional[Dict[str, Any]]:
        """Get misc/dropdown data configuration from database."""
        doc = self._db["miscData"].find_one({"_id": "dropdown_values"})
        if doc:
            return {
                "projects": doc.get("projects", []),
                "town_types": doc.get("town_types", []),
                "requesters": doc.get("requesters", []),
                "designations": doc.get("designations", []),
                "modules": doc.get("modules", []),
                "issues": doc.get("issues", []),
                "solutions": doc.get("solutions", []),
                "solved_on": doc.get("solved_on", []),
                "call_on": doc.get("call_on", []),
                "types": doc.get("types", []),
            }
        return None

    def misc_data_save(self, data: Dict[str, Any]) -> None:
        """Save misc/dropdown data configuration to database."""
        self._db["miscData"].update_one(
            {"_id": "dropdown_values"},
            {"$set": {
                "projects": data.get("projects", []),
                "town_types": data.get("town_types", []),
                "requesters": data.get("requesters", []),
                "designations": data.get("designations", []),
                "modules": data.get("modules", []),
                "issues": data.get("issues", []),
                "solutions": data.get("solutions", []),
                "solved_on": data.get("solved_on", []),
                "call_on": data.get("call_on", []),
                "types": data.get("types", []),
                "UpdatedDate": datetime.utcnow()
            }},
            upsert=True
        )


_MASTER_FIELDS = [
    "MobileNo",
    "Project",
    "TownType",
    "Requester",
    "RDCode",
    "RDName",
    "Town",
    "State",
    "Designation",
    "Name",
    "GSTNo",
    "EmailID",
    "CreatedDate",
    "UpdatedDate",
]

_CALLLOG_TEXT_FIELDS = [
    "MobileNo",
    "Project",
    "Town",
    "Requester",
    "RDCode",
    "RDName",
    "State",
    "Designation",
    "Name",
    "Module",
    "Issue",
    "Solution",
    "SolvedOn",
    "CallOn",
    "Type",
]


def _master_to_doc(record: MasterRecord) -> Dict[str, Any]:
    now = datetime.utcnow()
    return {
        "MobileNo": _normalize_str(record.get("MobileNo")),
        "Project": _normalize_str(record.get("Project")),
        "TownType": _normalize_str(record.get("TownType")),
        "Requester": _normalize_str(record.get("Requester")),
        "RDCode": _normalize_str(record.get("RDCode")),
        "RDName": _normalize_str(record.get("RDName")),
        "Town": _normalize_str(record.get("Town")),
        "State": _normalize_str(record.get("State")),
        "Designation": _normalize_str(record.get("Designation")),
        "Name": _normalize_str(record.get("Name")),
        "GSTNo": _normalize_str(record.get("GSTNo")),
        "EmailID": _normalize_str(record.get("EmailID")),
        "CreatedDate": record.get("CreatedDate") or now,
        "UpdatedDate": record.get("UpdatedDate") or now,
    }


def _doc_to_master(doc: Dict[str, Any]) -> MasterRecord:
    if not doc:
        return {}
    out: MasterRecord = {"id": str(doc.get("_id"))}
    for k in _MASTER_FIELDS:
        out[k] = doc.get(k)
    return out


def _doc_to_calllog(doc: Dict[str, Any]) -> CallLogRecord:
    out: CallLogRecord = {"id": str(doc.get("_id"))}
    for k in ["Date", *_CALLLOG_TEXT_FIELDS]:
        out[k] = doc.get(k)
    return out


def _doc_to_user(doc: Dict[str, Any]) -> UserRecord:
    if not doc:
        return {}
    return {
        "id": str(doc.get("_id")),
        "username": doc.get("username"),
        "password": doc.get("password"),
        "CreatedDate": doc.get("CreatedDate"),
    }
