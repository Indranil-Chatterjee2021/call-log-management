from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path
from typing import Optional

from utils.settings_store import AppSettings


BOOTSTRAP_FILE = Path(__file__).resolve().parent / ".db_config.json"


def save_bootstrap(settings: AppSettings) -> None:
    """
    Save the last active backend + connection details locally so the app can auto-connect
    on next startup (bootstrap problem).

    NOTE: This may include credentials (Mongo URI). Keep the file private.
    """
    BOOTSTRAP_FILE.write_text(json.dumps(asdict(settings), indent=2, default=str), encoding="utf-8")


def load_bootstrap() -> Optional[AppSettings]:
    if not BOOTSTRAP_FILE.exists():
        return None
    try:
        data = json.loads(BOOTSTRAP_FILE.read_text(encoding="utf-8"))
        backend = data.get("backend")
        if backend not in ("mongodb",):
            return None

        from utils.settings_store import MongoSettings

        mongodb_data = data.get("mongodb")
        if isinstance(mongodb_data, dict):
            # Use .get() with a default value to prevent KeyError if backup_path is missing
            mongodb = MongoSettings(
                uri=mongodb_data.get("uri", ""),
                database=mongodb_data.get("database", ""),
                backup_path=mongodb_data.get("backup_path", "") # Safely handle missing field
            )
        else:
            mongodb = None

        return AppSettings(
            backend=backend,
            mongodb=mongodb,
        )
    except Exception:
        # If the file is corrupted or schema changed drastically, return None 
        # so the user is forced to re-configure rather than the app crashing.
        return None
