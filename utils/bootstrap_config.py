from __future__ import annotations
import sys
import json
import ctypes
import platform
from dataclasses import asdict
from pathlib import Path
from typing import Optional
from utils.settings_store import AppSettings
from utils.settings_store import MongoSettings

# 1. PATH DETECTION LOGIC
if hasattr(sys, 'frozen'):
    # Path where the .exe is located
    BASE_DIR = Path(sys.executable).parent
else:
    # Path where the .py script is located (during development)
    BASE_DIR = Path(__file__).resolve().parent

BOOTSTRAP_FILE = BASE_DIR / ".db_config.json"


def _set_file_hidden(path: Path, hide: bool = True):
    """Sets or removes the Hidden attribute on Windows."""
    if platform.system() == "Windows" and path.exists():
        # 0x02 is Hidden, 0x80 is Normal/Archive
        attr = 0x02 if hide else 0x80
        try:
            ctypes.windll.kernel32.SetFileAttributesW(str(path), attr)
        except Exception:
            pass


def save_bootstrap(appSettings: AppSettings) -> None:
    # 1. Unhide the file so Python can write to it
    _set_file_hidden(BOOTSTRAP_FILE, hide=False)
    settings = {
        "backend": appSettings.backend,
        "mongodb": asdict(appSettings.mongodb) if appSettings.mongodb else None,
    }
    
    # 2. Perform the write
    BOOTSTRAP_FILE.write_text(
        json.dumps(settings, indent=2, default=str), 
        encoding="utf-8"
    )
    
    # 3. Re-hide the file
    _set_file_hidden(BOOTSTRAP_FILE, hide=True)


def load_bootstrap() -> Optional[AppSettings]:
    if not BOOTSTRAP_FILE.exists():
        return None
    try:
        data = json.loads(BOOTSTRAP_FILE.read_text(encoding="utf-8"))
        backend = data.get("backend")
        if backend not in ("mongodb"):
            return None

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

        return AppSettings(backend=backend, mongodb=mongodb)
    except Exception:
        # If the file is corrupted or schema changed drastically, return None 
        # so the user is forced to re-configure rather than the app crashing.
        return None
