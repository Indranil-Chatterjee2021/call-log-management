import os
import sys
import subprocess
import shutil
import zipfile
from datetime import datetime
from pathlib import Path


def _get_external_bin_path(executable_name: str) -> str:
    """Locates an executable in a 'bin' folder relative to the app's root location."""
    if hasattr(sys, 'frozen'):
        # Works for PyInstaller .exe
        base_dir = os.path.dirname(sys.executable)
    else:
        # For development: 
        # If this file is in 'utils/', we need to go UP one level to find 'bin/'
        current_dir = os.path.dirname(os.path.abspath(__file__))
        base_dir = os.path.dirname(current_dir) # Goes from 'utils/' to project root

    return os.path.join(base_dir, "bin", executable_name)


def run_mongo_backup(uri: str, db_name: str, backup_root: str):
    """Executes the backup and compresses it into a ZIP file."""
    executable = "mongodump.exe" if os.name == 'nt' else "mongodump"
    dump_path = _get_external_bin_path(executable)

    if not os.path.exists(dump_path):
        return False, f"Backup tool not found at: {dump_path}"

    # 1. Setup Paths
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    # This is the folder where mongodump will initially put the files
    temp_dump_dir = os.path.join(backup_root, f"temp_{db_name}_{timestamp}")
    # This is the final zip file path (without the .zip extension for shutil)
    zip_base_name = os.path.join(backup_root, f"{db_name}_{timestamp}")
    
    if not os.path.exists(backup_root):
        os.makedirs(backup_root, exist_ok=True)

    try:
        c_flags = 0x08000000 if os.name == 'nt' else 0

        # 2. Run Mongodump
        # Note: We dump into temp_dump_dir
        cmd = [
            dump_path, "--uri", uri, "--db", db_name,
            "--excludeCollection", "appConfig",
            "--excludeCollection", "users",
            "--out", temp_dump_dir
        ]
        subprocess.run(cmd, check=True, text=True, capture_output=True, creationflags=c_flags)

        # 3. Create ZIP file 
        # base_name: the path/filename of the zip to create
        # format: 'zip'
        # root_dir: the folder we want to zip (the contents inside temp_dump_dir)
        shutil.make_archive(zip_base_name, 'zip', temp_dump_dir)

        # 4. Cleanup: Remove the unzipped temporary folder
        shutil.rmtree(temp_dump_dir)

        # 5. Retention Policy
        _clean_old_backups(backup_root, keep_count=3)

        return True, f"{os.path.basename(zip_base_name)}.zip"
        
    except subprocess.CalledProcessError as e:
        if os.path.exists(temp_dump_dir): shutil.rmtree(temp_dump_dir)
        return False, f"Backup failed: {e.stderr}"
    except Exception as e:
        if os.path.exists(temp_dump_dir): shutil.rmtree(temp_dump_dir)
        return False, str(e)
    

def _clean_old_backups(backup_root: str, keep_count: int = 3):
    """Deletes older .zip files, keeping only the most recent ones."""
    path = Path(backup_root)
    # Get all CLM_Backup zip files
    backups = sorted(list(path.glob("CLM_Backup_*.zip")), key=os.path.getmtime, reverse=True)
    
    if len(backups) > keep_count:
        for old_backup in backups[keep_count:]:
            os.remove(old_backup)
            

def run_mongo_restore(uri: str, db_name: str, zip_path: str):
    executable = "mongorestore.exe" if os.name == 'nt' else "mongorestore"
    restore_path = _get_external_bin_path(executable)
    extract_to = os.path.join(os.path.dirname(zip_path), "temp_restore_extract")

    try:
        # 1. Clean extraction
        if os.path.exists(extract_to): shutil.rmtree(extract_to)
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(extract_to)

        # 2. Logic to find the actual data folder
        # We look for the directory that contains .bson files
        target_dir = extract_to
        for root, dirs, files in os.walk(extract_to):
            if any(f.endswith('.bson') for f in files):
                target_dir = root
                break
        
        # Validation: If no BSON files found anywhere in the ZIP
        if target_dir == extract_to and not any(f.endswith('.bson') for f in os.listdir(extract_to)):
            return False, "Restore failed: No database files (.bson) found in the backup."

        # 3. Run Mongorestore pointing directly to where the BSON files were found
        cmd = [
            restore_path, 
            "--uri", uri, 
            "--db", db_name, 
            "--drop", # Only drops collections present in the backup
            target_dir
        ]
        
        c_flags = 0x08000000 if os.name == 'nt' else 0
        result = subprocess.run(cmd, check=True, text=True, capture_output=True, creationflags=c_flags)

        # 4. Cleanup
        shutil.rmtree(extract_to)
        return True, "Data successfully restored. 'appConfig' was preserved."

    except subprocess.CalledProcessError as e:
        if os.path.exists(extract_to): shutil.rmtree(extract_to)
        return False, f"Restore failed: {e.stderr}"
    except Exception as e:
        if os.path.exists(extract_to): shutil.rmtree(extract_to)
        return False, str(e)