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
import tkinter as tk
from tkinter import filedialog
from utils import run_mongo_restore, test_mongo_connection, load_bootstrap, save_bootstrap
from utils.settings_store import AppSettings, MongoSettings 

# --- TKINTER UTILITIES ---
def _browse_folder():
    """Opens a native folder picker and returns the path."""
    root = tk.Tk()
    root.withdraw()
    root.attributes('-topmost', True)
    path = filedialog.askdirectory()
    root.destroy()
    return path


def _browse_file():
    """Opens a native file picker for ZIP files and returns the path."""
    root = tk.Tk()
    root.withdraw()
    root.attributes('-topmost', True)
    path = filedialog.askopenfilename(filetypes=[("ZIP files", "*.zip")])
    root.destroy()
    return path


def _hide_password_reveal():
    st.markdown("""
    <style>
        div[data-testid="stTextInput"] button { display: none !important; }
        button[aria-label="Show password"], 
        button[aria-label="Hide password"] { display: none !important; }
        input[type="password"] { -webkit-text-security: disc !important; }
        input:disabled {
            background-color: #262730 !important;
            color: #808495 !important;
            opacity: 1 !important;
        }
        div[data-testid="InputInstructions"] { display: none !important; }
        /* Target all buttons to have a green background */
    div.stButton > button {
        background-color: #28a745 !important; /* Standard Green */
        color: white !important;
        border-color: #28a745 !important;
    }

    /* Hover effect */
    div.stButton > button:hover {
        background-color: #218838 !important; /* Darker Green on hover */
        border-color: #1e7e34 !important;
        color: white !important;
    }

    /* Target specifically the 'primary' type buttons if needed */
    div.stButton > button[kind="primary"] {
        background-color: #28a745 !important;
        border: none !important;
    }
    
    /* Alignment fix for Browse buttons from previous step */
    div[data-testid="column"] button {
        margin-top: 0px !important;
        height: 45px !important;
    }
    [data-testid="column"] {
        display: flex;
        align-items: flex-end;
    }        
    </style>
    """, unsafe_allow_html=True)


def render_settings_page(is_cloud: bool, set_active_repo_func, save_settings_func):
    _hide_password_reveal()
    st.subheader("💾 Database settings (required)")

    active_backend = st.session_state.get("active_backend")
    settings = st.session_state.get("app_settings")

    if is_cloud:
        st.info("ℹ️ Running on Streamlit Cloud. MongoDB is required.")

    if active_backend and settings:
        st.info(f"🔒 **Currently active backend: MongoDB**")
        if not is_cloud:
            _render_backup_history(settings.mongodb.backup_path, settings.mongodb.uri)
    else:
        _render_mongodb_section(is_cloud, set_active_repo_func, save_settings_func)


def _render_mongodb_section(is_cloud: bool, set_active_repo_func, save_settings_func):
    """Render MongoDB configuration section with native browse functionality."""
    
    # 1. CSS ALIGNMENT HACK
    # This pushes the buttons down to align with text inputs when labels are collapsed
    st.markdown("""
        <style>
        /* 1. FORCE ALL BUTTONS TO GREEN */
        div.stButton > button {
            background-color: #28a745 !important; 
            color: white !important;
            border-radius: 5px !important;
            border: 1px solid #28a745 !important;
            transition: 0.3s;
        }Welcome
        
        div.stButton > button:hover {
            background-color: #218838 !important;
            border-color: #1e7e34 !important;
        }

        /* 2. ALIGNMENT FIX FOR BROWSE BUTTONS */
        div[data-testid="column"] button {
            margin-top: 0px !important;
            height: 45px !important;
        }
        [data-testid="column"] {
            display: flex;
            align-items: flex-end;
        }
        </style>
    """, unsafe_allow_html=True)

    st.markdown("**MongoDB Connection Details**")
    
    mongo_uri_input = st.text_input("Mongo URI *", type="password", placeholder="mongodb+srv://...")
    mongo_db = st.text_input("Enter Mongo Database Name *", placeholder="call-logs")
    
    st.markdown("---")
    st.markdown("**Local Backup Storage Path ***")
    
    # 2. INITIALIZE SESSION STATE FOR PATHS
    if "backup_path_val" not in st.session_state:
        st.session_state.backup_path_val = None 
        # str(Path.home() / "Desktop" / "mongoBackup")

    # 3. BACKUP PATH ROW
    col_path, col_btn = st.columns([0.8, 0.2])
    with col_path:
        # Use label_visibility="collapsed" to remove extra top spacing
        backup_path = st.text_input(
            "Backup Path", 
            value=st.session_state.backup_path_val, 
            label_visibility="collapsed"
        )
    with col_btn:
        if st.button("Browse 📁", key="browse_backup", use_container_width=True):
            folder = _browse_folder()
            if folder:
                st.session_state.backup_path_val = folder
                st.rerun()
                
    st.caption("Mandatory: Database is backed up to this folder on logout.")

    # 4. SAVE & ACTIVATE BUTTON
    if st.button("Save & Activate MongoDB", type="primary"):
        if not backup_path or not backup_path.strip():
            st.error("❌ Backup path is required.")
            return

        encoded_uri, err = _encode_mongo_uri(mongo_uri_input)
        if err:
            st.error(err)
        else:
            mongo_settings = MongoSettings(
                uri=encoded_uri, 
                database=mongo_db.strip(), 
                backup_path=backup_path.strip()
            )
            ok, msg = test_mongo_connection(mongo_settings)
            if not ok:
                st.error(msg)
            else:
                st.success(msg)
                app_settings = AppSettings(backend="mongodb", mongodb=mongo_settings)
                
                if st.session_state.active_repo is None:
                    save_settings_func(app_settings)
                
                if not is_cloud:
                    save_bootstrap(app_settings)
                
                set_active_repo_func("mongodb", mongo_uri=mongo_settings.uri, mongo_db=mongo_settings.database)
                st.success("✅ Configuration saved and Backup Path set.")
                
                if st.session_state.get("app_activated"):
                    st.session_state.current_page_index = 4 if st.session_state.get('master_data_exists') else 2
                else:
                    st.info("Database connected. Please activate your application.")
                
                st.rerun()


def _render_backup_history(backup_root: str, uri: str):
    st.markdown("### 📜 Backup History")
    path = Path(backup_root)
    if not path.exists():
        st.info("No backups found.")
        return

    files = sorted(list(path.glob("*.zip")), key=os.path.getmtime, reverse=True)
    if not files:
        st.write("No backups found.")
        return

    data = [{"File Name": f.name, "Date": datetime.fromtimestamp(f.stat().st_mtime).strftime("%Y-%m-%d %H:%M"), "Path": str(f)} for f in files]
    df = pd.DataFrame(data)
    st.dataframe(df[["File Name", "Date"]], use_container_width=True, hide_index=True)

    selected_file_name = st.selectbox("Quick Restore from History", df["File Name"].tolist())
    selected_path = df[df["File Name"] == selected_file_name]["Path"].values[0]

    confirm_restore = st.checkbox("Confirm overwrite for quick restore.")
    if st.button("🔥 Restore Selected", type="primary", disabled=not confirm_restore):
        with st.spinner("Restoring..."):
            # Use mongodb conig from bootstrap
            settings = load_bootstrap()
            mongo_uri = settings.mongodb.uri
            mongo_db = settings.mongodb.database
            ok, msg = run_mongo_restore(mongo_uri, mongo_db, selected_path)
            if ok: 
                st.success(msg) 
                time.sleep(2)
                if st.session_state.get("app_activated"):
                    st.session_state.current_page_index = 4 if st.session_state.get('master_data_exists') else 2
                st.rerun()
            else: 
                st.error(msg)


def _encode_mongo_uri(uri: str):
    uri = (uri or "").strip()
    if not uri: return None, "URI is required."
    parsed = urlparse(uri)
    if not parsed.scheme not in ("mongodb", "mongodb+srv"): return uri, None
    return uri, None