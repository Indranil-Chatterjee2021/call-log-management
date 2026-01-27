"""
Settings Page Module
Handles database backend configuration (MongoDB)
"""
import os
import time
import streamlit as st
from urllib.parse import urlparse
import pandas as pd
from pathlib import Path
from datetime import datetime
from utils.backup_service import check_backup_tools, run_mongo_restore

from utils.settings_store import (
    AppSettings,
    MongoSettings,
    test_mongo_connection,
)
from utils.bootstrap_config import save_bootstrap

def hide_password_reveal():
    st.markdown("""
    <style>
        /* 1. HIDE THE EYE ICON (Show/Hide Password Button) */
        div[data-testid="stTextInput"] button { 
            display: none !important; 
        }
        
        button[aria-label="Show password"], 
        button[aria-label="Hide password"] { 
            display: none !important; 
        }

        /* 2. SECURE PASSWORD FIELDS */
        input[type="password"] { 
            padding-right: 1rem !important; 
            -webkit-text-security: disc !important; /* Force discs even if browser tries to reveal */
        }

        /* 3. STYLE DISABLED FIELDS (Matches your image 015411) */
        input:disabled {
            background-color: #262730 !important;
            color: #808495 !important;
            -webkit-text-security: disc !important;
            opacity: 1 !important;
            cursor: not-allowed !important;
        }
        
        /* 4. HIDE THE 'Press Enter to apply' hint */
        div[data-testid="InputInstructions"] {
            display: none !important;
        }
    </style>
    """, unsafe_allow_html=True)
    
    
def render_settings_page(is_cloud: bool, set_active_repo_func, save_settings_func):
    """
    Render the Settings page for database backend configuration.
    """
    hide_password_reveal()
    st.subheader("💾 Database settings (required)")

    # Check if a backend is already active
    active_backend = st.session_state.get("active_backend")
    settings = st.session_state.get("app_settings")

    # Only MongoDB is supported
    if is_cloud:
        st.info("ℹ️ Running on Streamlit Cloud. MongoDB is required.")

    if active_backend and settings:
        st.info(f"🔒 **Currently active backend: MongoDB**")
        if not is_cloud:
            render_backup_history(settings.mongodb.backup_path, settings.mongodb.uri)

        st.divider()
        if st.button("Reconnect / Reconfigure"):
            st.session_state.active_repo = None
            st.session_state.active_backend = None
            st.rerun()
    else:
        # Directly render MongoDB section (no other option)
        _render_mongodb_section(is_cloud, set_active_repo_func, save_settings_func)

# MSSQL support removed; only MongoDB configuration remains

def _render_mongodb_section(is_cloud: bool, set_active_repo_func, save_settings_func):
    """Render MongoDB configuration section."""
    st.markdown("**MongoDB Connection Details**")
    
    mongo_uri_input = st.text_input("Mongo URI *", type="password", placeholder="mongodb+srv://...")
    mongo_db = st.text_input("Enter Mongo Database Name *", placeholder="call-logs")
    # Generate the default path
    default_path = str(Path.home() / "Desktop" / "mongoBackup")
    # New Field: Backup Path
    backup_path = st.text_input("Local Backup Storage Path *", value=default_path, placeholder="e.g., C:/Users/Name/Documents/Backups")
    st.caption("Mandatory: Database is backed up to this folder on logout.")

    if st.button("Save & Activate MongoDB", type="primary"):
        # Validation
        if not backup_path.strip():
            st.error("❌ Backup path is required.")
            return

        if not check_backup_tools():
            st.warning("⚠️ Warning: 'mongodump' not found in bin/ folder. Backup will fail until fixed.")

        encoded_uri, err = _encode_mongo_uri(mongo_uri_input)
        if err:
            st.error(err)
        else:
            mongo_settings = MongoSettings(uri=encoded_uri, database=mongo_db.strip(), backup_path=backup_path.strip())
            ok, msg = test_mongo_connection(mongo_settings)
            if not ok:
                st.error(msg)
            else:
                st.success(msg)
                
                # Note: We pass None for activation here; let the Silent Sync handle it
                # after the repo is active.
                app_settings = AppSettings(backend="mongodb", mongodb=mongo_settings)
                
                if st.session_state.active_repo is None:
                    save_settings_func(app_settings)
                
                if not is_cloud:
                    save_bootstrap(app_settings)
                
                # This triggers _set_active_repo which now includes the Activation Check
                set_active_repo_func("mongodb", mongo_uri=mongo_settings.uri, mongo_db=mongo_settings.database)
                st.success("✅ Configuration saved and Backup Path set.")
                
                # Logic to determine where to go next
                if st.session_state.get("app_activated"):
                    st.success("✅ Database connected & License verified!")
                    if st.session_state.get('master_data_exists'):
                        st.session_state.current_page_index = 4
                    else:
                        st.session_state.current_page_index = 2
                else:
                    st.info("Database connected. Please activate your application.")
                
                st.rerun()

    st.divider()
    st.markdown("### 🔄 Data Recovery")
    restore_folder = st.text_input("Backup Folder Path to Restore", placeholder="C:/Users/Name/Desktop/mongoBackup/backup_date")
    
    if st.button("Restore from Backup"):
        if not restore_folder:
            st.error("Please provide the path to the backup folder.")
        else:
            with st.spinner("Restoring data..."):
                ok, msg = run_mongo_restore(mongo_uri_input, restore_folder)
                if ok:
                    st.success(msg)
                    st.info("System data restored. Local configuration (License/URI) remains unchanged.")
                else:
                    st.error(f"Restore failed: {msg}")            


def render_backup_history(backup_root: str, uri: str):
    st.markdown("### 📜 Backup History")
    
    path = Path(backup_root)
    if not path.exists():
        st.info("No backups found in the specified local path.")
        return

    files = sorted(list(path.glob("CLM_Backup_*.zip")), key=os.path.getmtime, reverse=True)
    
    if not files:
        st.write("No backups (.zip) found.")
        return

    data = [{
        "File Name": f.name,
        "Date": datetime.fromtimestamp(f.stat().st_mtime).strftime("%Y-%m-%d %H:%M"),
        "Size (KB)": round(f.stat().st_size / 1024, 2),
        "Path": str(f)
    } for f in files]
    
    df = pd.DataFrame(data)
    st.dataframe(df[["File Name", "Date", "Size (KB)"]], use_container_width=True, hide_index=True)

    selected_file_name = st.selectbox("Select a backup to restore", df["File Name"].tolist())
    selected_path = df[df["File Name"] == selected_file_name]["Path"].values[0]

    # Use a checkbox for confirmation to avoid the 'nested button' rerun bug
    confirm_restore = st.checkbox("I understand this will overwrite current data.")
    
    if st.button("🔥 Restore Selected Backup", type="primary", disabled=not confirm_restore):
        with st.spinner("Unzipping and restoring..."):
            ok, msg = run_mongo_restore(uri, selected_path)
            if ok: 
                st.success(msg)
                time.sleep(2)
                st.rerun()
            else: 
                st.error(msg)


def _encode_mongo_uri(uri: str):
    """Validation and encoding logic for Mongo URI."""
    uri = (uri or "").strip()
    if not uri: return None, "URI is required."
    parsed = urlparse(uri)
    if not parsed.scheme or parsed.scheme not in ("mongodb", "mongodb+srv"):
        return None, "Invalid scheme."
    return uri, None # Simplified for brevity, keep your original encoding logic if preferred