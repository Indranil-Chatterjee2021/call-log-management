from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from datetime import datetime
from typing import Any, Dict, Literal, Optional, Tuple

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import pyodbc  # noqa: F401
    from pymongo import MongoClient  # noqa: F401


Backend = Literal["mssql", "mongodb"]


@dataclass
class MSSQLSettings:
    server: str
    database: str
    username: str
    password: str
    driver: str = "{ODBC Driver 17 for SQL Server}"


@dataclass
class MongoSettings:
    uri: str
    database: str


@dataclass
class AppSettings:
    backend: Backend
    mssql: Optional[MSSQLSettings] = None
    mongodb: Optional[MongoSettings] = None


def _mssql_conn_str(s: MSSQLSettings) -> str:
    return (
        f"DRIVER={s.driver};"
        f"SERVER={s.server};"
        f"DATABASE={s.database};"
        f"UID={s.username};"
        f"PWD={s.password};"
        "TrustServerCertificate=yes;"
    )


def test_mssql_connection(s: MSSQLSettings) -> Tuple[bool, str]:
    try:
        import pyodbc  # type: ignore

        conn = pyodbc.connect(_mssql_conn_str(s), timeout=5)
        cur = conn.cursor()
        cur.execute("SELECT 1")
        cur.fetchone()
        cur.close()
        conn.close()
        return True, "MSSQL connection OK."
    except Exception as e:
        return False, f"MSSQL connection failed: {e}"


def test_mongo_connection(s: MongoSettings) -> Tuple[bool, str]:
    try:
        from pymongo import MongoClient  # type: ignore

        client = MongoClient(s.uri, serverSelectionTimeoutMS=5000)
        client.admin.command("ping")
        # ensure db exists
        _ = client[s.database].list_collection_names()
        client.close()
        return True, "MongoDB connection OK."
    except Exception as e:
        return False, f"MongoDB connection failed: {e}"


def save_settings_to_mssql(app: AppSettings) -> None:
    if not app.mssql:
        raise ValueError("Missing MSSQL settings")
    s = app.mssql
    import pyodbc  # type: ignore

    conn = pyodbc.connect(_mssql_conn_str(s))
    cur = conn.cursor()
    try:
        cur.execute(
            """
            IF NOT EXISTS (SELECT * FROM sys.objects WHERE object_id = OBJECT_ID(N'[dbo].[AppConfig]') AND type in (N'U'))
            CREATE TABLE [dbo].[AppConfig] (
                [ConfigKey] NVARCHAR(100) NOT NULL PRIMARY KEY,
                [ConfigJson] NVARCHAR(MAX) NOT NULL,
                [UpdatedAt] DATETIME NOT NULL DEFAULT GETDATE()
            )
            """
        )
        payload = json.dumps(asdict(app), default=str)
        cur.execute(
            """
            MERGE [dbo].[AppConfig] AS target
            USING (SELECT ? AS ConfigKey, ? AS ConfigJson) AS source
            ON (target.ConfigKey = source.ConfigKey)
            WHEN MATCHED THEN
              UPDATE SET ConfigJson = source.ConfigJson, UpdatedAt = GETDATE()
            WHEN NOT MATCHED THEN
              INSERT (ConfigKey, ConfigJson) VALUES (source.ConfigKey, source.ConfigJson);
            """,
            "active",
            payload,
        )
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        cur.close()
        conn.close()


def save_settings_to_mongo(app: AppSettings) -> None:
    if not app.mongodb:
        raise ValueError("Missing MongoDB settings")
    s = app.mongodb
    from pymongo import MongoClient  # type: ignore

    client = MongoClient(s.uri)
    try:
        db = client[s.database]
        col = db["appConfig"]
        payload: Dict[str, Any] = asdict(app)
        payload["UpdatedAt"] = datetime.utcnow()
        col.update_one({"_id": "active"}, {"$set": payload}, upsert=True)
    finally:
        client.close()


def save_settings(app: AppSettings) -> None:
    """
    Store settings inside the chosen backend itself:
    - MSSQL: dbo.AppConfig (key 'active')
    - MongoDB: appConfig collection (_id 'active')
    """
    if app.backend == "mssql":
        save_settings_to_mssql(app)
    elif app.backend == "mongodb":
        save_settings_to_mongo(app)
    else:
        raise ValueError(f"Unsupported backend: {app.backend}")

