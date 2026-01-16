from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path
from typing import Optional

from settings_store import AppSettings


BOOTSTRAP_FILE = Path(__file__).resolve().parent / ".db_config.json"


def save_bootstrap(settings: AppSettings) -> None:
    """
    Save the last active backend + connection details locally so the app can auto-connect
    on next startup (bootstrap problem).

    NOTE: This may include credentials (MSSQL password / Mongo URI). Keep the file private.
    """
    BOOTSTRAP_FILE.write_text(json.dumps(asdict(settings), indent=2, default=str), encoding="utf-8")


def load_bootstrap() -> Optional[AppSettings]:
    if not BOOTSTRAP_FILE.exists():
        return None
    data = json.loads(BOOTSTRAP_FILE.read_text(encoding="utf-8"))
    # Re-hydrate dataclasses (minimal validation)
    backend = data.get("backend")
    if backend not in ("mssql", "mongodb"):
        return None
    # settings_store.AppSettings accepts nested dataclasses, but JSON is dicts.
    # We'll import constructors lazily to avoid cycles.
    from settings_store import MongoSettings, MSSQLSettings

    mssql = data.get("mssql")
    mongodb = data.get("mongodb")
    return AppSettings(
        backend=backend,
        mssql=MSSQLSettings(**mssql) if isinstance(mssql, dict) else None,
        mongodb=MongoSettings(**mongodb) if isinstance(mongodb, dict) else None,
    )
