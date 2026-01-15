from __future__ import annotations

import os

from dotenv import load_dotenv

from .base import CallLogRepository


def get_repository(
    *,
    backend_override: str | None = None,
    mongo_uri_override: str | None = None,
    mongo_db_override: str | None = None,
) -> CallLogRepository:
    """
    Choose backend using env:

    - DB_BACKEND=mssql (default)
    - DB_BACKEND=mongodb
    """
    load_dotenv()
    backend = (backend_override or os.getenv("DB_BACKEND") or "mssql").strip().lower()

    if backend in {"mssql", "sqlserver", "sql"}:
        from .mssql_repo import MSSQLRepository

        return MSSQLRepository()

    if backend in {"mongodb", "mongo"}:
        mongo_uri = mongo_uri_override or os.getenv("MONGO_URI", "mongodb://localhost:27017")
        mongo_db = mongo_db_override or os.getenv("MONGO_DB", "CallLogDB")
        from .mongo_repo import MongoRepository

        return MongoRepository(mongo_uri=mongo_uri, db_name=mongo_db)

    raise ValueError(f"Unsupported DB_BACKEND={backend!r}. Use 'mssql' or 'mongodb'.")
