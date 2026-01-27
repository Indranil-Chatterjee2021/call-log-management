import os
import sys
import subprocess
import shutil
import zipfile
from datetime import datetime
from pathlib import Path

def get_resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.abspath("."), relative_path)


def check_backup_tools() -> bool:
    """Verifies that mongodump exists in the bin folder."""
    # On Mac, you might name it just 'mongodump', on Windows 'mongodump.exe'
    executable = "mongodump.exe" if os.name == 'nt' else "mongodump"
    path = get_resource_path(os.path.join("bin", executable))
    return os.path.exists(path)


def run_mongo_backup(uri: str, db_name: str, backup_root: str):
    """Executes the backup to the user-defined local folder."""
    if not check_backup_tools():
        return False, "Backup tool (mongodump) not found in bin/ folder."

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    temp_folder = os.path.join(backup_root, f"temp_dump_{timestamp}")
    zip_filename = os.path.join(backup_root, f"CLM_Backup_{timestamp}.zip")
    
    # Ensure the root backup directory exists
    if not os.path.exists(backup_root):
        try:
            os.makedirs(backup_root)
        except Exception as e:
            return False, f"Could not create backup directory: {e}"

    executable = "mongodump.exe" if os.name == 'nt' else "mongodump"
    dump_path = get_resource_path(os.path.join("bin", executable))

    try:
        # We use creationflags=0x08000000 (CREATE_NO_WINDOW) only on Windows
        c_flags = 0x08000000 if os.name == 'nt' else 0

        # 1. Run Mongodump (Exclude appConfig)
        cmd = [
            dump_path, "--uri", uri, "--db", db_name,
            "--excludeCollection", "appConfig",
            "--out", temp_folder
        ]
        subprocess.run(cmd, check=True, text=True, capture_output=True, creationflags=c_flags)

        # 2. Create ZIP file
        shutil.make_archive(zip_filename.replace('.zip', ''), 'zip', temp_folder)
        
        # 3. Remove the temporary unzipped folder
        shutil.rmtree(temp_folder)

        # 4. Retention Policy: Keep only last 3 ZIP files
        clean_old_backups(backup_root, keep_count=3)

        return True, os.path.basename(zip_filename)
        
    except subprocess.CalledProcessError as e:
        return False, f"Backup failed: {e.stderr}"
    except Exception as e:
        return False, str(e)
    

def clean_old_backups(backup_root: str, keep_count: int = 3):
    """Deletes older .zip files, keeping only the most recent ones."""
    path = Path(backup_root)
    # Get all CLM_Backup zip files
    backups = sorted(list(path.glob("CLM_Backup_*.zip")), key=os.path.getmtime, reverse=True)
    
    if len(backups) > keep_count:
        for old_backup in backups[keep_count:]:
            os.remove(old_backup)
            

def run_mongo_restore(uri: str, zip_path: str):
    """Unzips a backup and restores it to MongoDB."""
    restore_path = get_resource_path(os.path.join("bin", "mongorestore.exe" if os.name == 'nt' else "mongorestore"))
    extract_to = os.path.join(os.path.dirname(zip_path), "temp_restore_extract")

    try:
        # 1. Unzip
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(extract_to)

        # 2. Run Mongorestore
        cmd = [restore_path, "--uri", uri, "--drop", extract_to]
        subprocess.run(cmd, check=True, capture_output=True)

        # 3. Cleanup extracted files
        shutil.rmtree(extract_to)
        return True, "Data successfully unzipped and restored."
    except Exception as e:
        if os.path.exists(extract_to): shutil.rmtree(extract_to)
        return False, str(e)