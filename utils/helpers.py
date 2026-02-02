import os
import streamlit as st
from storage import get_repository
from utils.activation import verify_key
from utils.bootstrap_config import load_bootstrap
from utils.dropdown_data import get_dropdown_values
from utils.settings_store import MongoSettings, AppSettings, test_mongo_connection
            

# Utility Functions
# Function to detect Streamlit Cloud environment
def is_streamlit_cloud() -> bool:
    """Detect if the app is running on Streamlit Cloud."""
    if os.environ.get("STREAMLIT_RUNTIME_ENV") == "cloud":
        return True
    if os.environ.get("HOSTNAME") == "streamlit":
        return True
    return False

# Function to set the active repository
def set_active_repo(backend: str, mongo_uri: str | None = None, mongo_db: str | None = None, backup_path: str | None = None) -> None:
    """Set the active repository in session state (MongoDB only)."""
    st.session_state.active_backend = backend
    # Only mongodb is supported
    # 1. Create the repository
    st.session_state.active_repo = get_repository(
        backend_override="mongodb",
        mongo_uri_override=mongo_uri,
        mongo_db_override=mongo_db,
        backup_path_override=backup_path,
    )

    # 2. IMPORTANT: Store these for the Logout Backup Logic
    if mongo_uri and mongo_db and backup_path:
        
        st.session_state.app_settings = AppSettings(
            backend="mongodb",
            mongodb=MongoSettings(uri=mongo_uri, database=mongo_db, backup_path=backup_path)
        )

    # AFTER the repo is set, check for existing license in the DB
    if st.session_state.active_repo:
        try:
            act_record = st.session_state.active_repo.get_activation_record()
            if act_record:
                # Force types to string to handle Atlas 'int' types and prevent .strip() errors
                email = str(act_record.get('email', ''))
                mobile = str(act_record.get('mobile', ''))
                key = str(act_record.get('key', ''))

                if email and mobile and key and verify_key(email, mobile, key):
                    st.session_state.app_activated = True
        except Exception:
            pass  # Silent failure during bootstrap is okay

# Function to initialize session state variables
def initialize_session_state():
    """Initialize all session state variables."""
    if "active_backend" not in st.session_state:
        st.session_state.active_backend = None
    if "active_repo" not in st.session_state:
        st.session_state.active_repo = None
    if "bootstrap_attempted" not in st.session_state:
        st.session_state.bootstrap_attempted = False
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False
    if "current_user" not in st.session_state:
        st.session_state.current_user = None
    if "app_activated" not in st.session_state:
        st.session_state.app_activated = False
    if 'master_data_exists' not in st.session_state:
        st.session_state.master_data_exists = False
    if 'dropdowns' not in st.session_state:
        st.session_state.dropdowns = get_dropdown_values(st.session_state.active_repo) if st.session_state.active_repo else get_dropdown_values()

# Function to auto-bootstrap connection
def auto_bootstrap_connection():
    """Attempt to auto-connect using previously saved configuration."""
    if st.session_state.active_repo is None and not st.session_state.bootstrap_attempted:
        st.session_state.bootstrap_attempted = True
        prev = load_bootstrap()
        if prev:
            if prev.backend == "mongodb" and prev.mongodb:
                ok, _ = test_mongo_connection(prev.mongodb)
                if ok: set_active_repo("mongodb", mongo_uri=prev.mongodb.uri, mongo_db=prev.mongodb.database, backup_path=prev.mongodb.backup_path)

# Function to check if master data exists
def check_master_data_exists():
    """Check if master data exists in the database."""
    if st.session_state.active_repo is not None:
        if "master_data_checked" not in st.session_state:
            st.session_state.master_data_checked = True
            try:
                repo = st.session_state.active_repo
                st.session_state.master_data_exists = len(repo.master_list()) > 0
                st.session_state.dropdowns = get_dropdown_values(repo)
            except Exception:
                st.session_state.master_data_exists = False
                