"""
Streamlit Call Log Application - Main Entry Point
Clean architecture with modular page components
"""
import streamlit as st
import pandas as pd
from datetime import datetime
import os
from utils.activation import get_hardware_id
from views.about_page import render_about_page
from utils.dropdown_data import get_dropdown_values
from storage import get_repository
from utils.logout import logout
from utils.settings_store import AppSettings, save_settings
from utils.bootstrap_config import load_bootstrap
from views.settings_page import render_settings_page
from views.login_page import render_login_page
from views.master_data_page import render_master_data_page
from views.call_log_page import render_call_log_page
from views.reports_page import render_reports_page
from views.metadata_page import render_metadata_page
from views.email_config_page import render_email_config_page
from streamlit_option_menu import option_menu
from utils.activation import render_activation_ui, verify_key
from utils.logout import logout

# Page configuration
st.set_page_config(page_title="Call Log Management System", page_icon="📞", layout="wide")

def is_streamlit_cloud() -> bool:
    """Detect if the app is running on Streamlit Cloud."""
    if os.environ.get("STREAMLIT_RUNTIME_ENV") == "cloud":
        return True
    if os.environ.get("HOSTNAME") == "streamlit":
        return True
    return False

def _set_active_repo(backend: str, mongo_uri: str | None = None, mongo_db: str | None = None, backup_path: str | None = None) -> None:
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
        from utils.settings_store import MongoSettings, AppSettings
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

def _ensure_repo_or_stop() -> None:
    """Ensure repository is configured, otherwise stop execution."""
    if st.session_state.active_repo is None:
        st.warning("Please configure your database backend in **Settings** first.")
        st.stop()

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

def auto_bootstrap_connection():
    """Attempt to auto-connect using previously saved configuration."""
    if st.session_state.active_repo is None and not st.session_state.bootstrap_attempted:
        st.session_state.bootstrap_attempted = True
        prev = load_bootstrap()
        if prev:
            from utils.settings_store import test_mongo_connection
            if prev.backend == "mongodb" and prev.mongodb:
                ok, _ = test_mongo_connection(prev.mongodb)
                if ok: _set_active_repo("mongodb", mongo_uri=prev.mongodb.uri, mongo_db=prev.mongodb.database, backup_path=prev.mongodb.backup_path)

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

def load_custom_css():
    """Load custom CSS styling."""
    if os.path.exists("style.css"):
        with open("style.css") as f:
            st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)

def logout_app():            
    """
    Triggers the logout sequence. 
    The actual clearing of data happens AFTER the backup in logout.py.
    """
    logout()

def main():
    """Main application entry point."""
    initialize_session_state()
    is_cloud = is_streamlit_cloud()
    
    # 1. Bootstrapping (Local only)
    if not is_cloud:
        auto_bootstrap_connection()
    
    load_custom_css()
    
    st.markdown("<div class='sub-header-text'><span class='side-icon'>📞</span> Call Log Management System <span class='side-icon'>📞</span></div>", unsafe_allow_html=True)

    # --- NEW LOGIC FLOW ---
    
    # STEP 1: FORCE SETTINGS IF NOT CONNECTED
    if st.session_state.active_repo is None:
        st.info("👋 Welcome! Please connect to your MongoDB database in **Settings** to begin.")
        _, center_col, _ = st.columns([1, 6, 1])
        with center_col:
            with st.container(border=True):
                render_settings_page(is_cloud, set_active_repo_func=_set_active_repo, save_settings_func=save_settings)
        return # HALT: Cannot proceed without a database

    # STEP 2: SILENT CLOUD ACTIVATION SYNC
    # If we have a repo but not activated, try to fetch from DB
    if not st.session_state.app_activated:
        try:
            record = st.session_state.active_repo.get_activation_record()
            if record:
                # Convert everything to string to handle integer fields from Atlas
                email = str(record.get('email', ''))
                mobile = str(record.get('mobile', ''))
                hwid = get_hardware_id()
                key = str(record.get('key', ''))
                
                if email and mobile and hwid and key and verify_key(email, mobile, hwid, key):
                    st.session_state.app_activated = True
                    st.rerun() # Refresh to clear any activation UI
        except Exception:
            pass

    # STEP 3: MANUAL ACTIVATION GATE
    if not st.session_state.app_activated:
        _, center_col, _ = st.columns([1, 2, 1])
        with center_col:
            render_activation_ui(st.session_state.active_repo)
        return # HALT: App must be activated to see the menu

    # STEP 4: NAVIGATION & APP CONTENT
    check_master_data_exists()
    # if st.session_state.get("logged_out") is True: logout()

    menu_options = ["Settings", "Email", "Master", "Types", "Call Log", "Reports", "About", "Logout"]
    
    # Handle Page Index
    if 'current_page_index' not in st.session_state:
        if st.session_state.authenticated:
            st.session_state.current_page_index = 4 if st.session_state.master_data_exists else 2
        else:
            st.session_state.current_page_index = 4 # Defaults to Login (via Call Log)
            
    nav_l, nav_c, nav_r = st.columns([1, 4, 1]) 
    with nav_c:
        page = option_menu(
            menu_title=None,
            options=menu_options,
            icons=["gear", "envelope", "database", "tags", "telephone-inbound", "graph-up", 'info-circle', "box-arrow-right"],
            default_index=st.session_state.current_page_index,
            orientation='horizontal',
            styles={"nav-link": {"font-size": "14px", "padding": "5px 15px"}, "nav-link-selected": {"background-color": "#2e7bcf"}}
        )
    st.session_state.current_page_index = menu_options.index(page)

    # Logout Logic
    if page == "Logout": logout_app()

    # Footer
    current_date = datetime.now().strftime("%B %d, %Y")
    st.markdown(f'<div class="fixed-footer"><b>© 2026 Call Log Management System | Version 1.0.0 | Date: {current_date}</b></div>', unsafe_allow_html=True)
    
    _, center_col, _ = st.columns([1, 6, 1])
    with center_col:
        with st.container(border=True, height=600):
            # Enforce Authentication for everything except About/Settings
            if not st.session_state.authenticated and page not in ["Settings", "About"]:
                render_login_page(st.session_state.active_repo)
            else:
                # Routing
                if page == "Settings": render_settings_page(is_cloud, _set_active_repo, save_settings)
                elif page == "About": render_about_page()    
                elif page == "Email": render_email_config_page()    
                elif page == "Master": render_master_data_page(st.session_state.active_repo, st.session_state.dropdowns)
                elif page == "Types": render_metadata_page(st.session_state.active_repo, st.session_state.dropdowns)
                elif page == "Call Log": render_call_log_page(st.session_state.active_repo, st.session_state.dropdowns)
                elif page == "Reports": render_reports_page(st.session_state.active_repo)

if __name__ == "__main__":
    main()