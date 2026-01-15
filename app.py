"""
Streamlit Call Log Application - Main Entry Point
Clean architecture with modular page components
"""
import streamlit as st
import pandas as pd
from datetime import datetime
import os
from dropdown_data import get_dropdown_values
from storage import get_repository
from settings_store import AppSettings, save_settings
from bootstrap_config import load_bootstrap
from pages.settings_page import render_settings_page
from pages.login_page import render_login_page
from pages.master_data_page import render_master_data_page
from pages.call_log_page import render_call_log_page
from pages.reports_page import render_reports_page


def is_streamlit_cloud() -> bool:
    """
    Detect if the app is running on Streamlit Cloud.
    """
    return (
        os.getenv("STREAMLIT_SHARING_MODE") is not None or
        os.getenv("HOSTNAME", "").endswith(".streamlit.app") or
        os.getenv("IS_STREAMLIT_CLOUD") == "true"
    )


def _set_active_repo(backend: str, mongo_uri: str | None = None, mongo_db: str | None = None) -> None:
    """Set the active repository in session state."""
    st.session_state.active_backend = backend
    if backend == "mongodb":
        st.session_state.active_repo = get_repository(
            backend_override="mongodb",
            mongo_uri_override=mongo_uri,
            mongo_db_override=mongo_db,
        )
    else:
        st.session_state.active_repo = get_repository(backend_override="mssql")


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
    if 'dropdowns' not in st.session_state:
        st.session_state.dropdowns = get_dropdown_values()
    if 'master_data_exists' not in st.session_state:
        st.session_state.master_data_exists = False


def auto_bootstrap_connection():
    """Attempt to auto-connect using previously saved configuration."""
    if st.session_state.active_repo is None and not st.session_state.bootstrap_attempted:
        st.session_state.bootstrap_attempted = True
        prev = load_bootstrap()
        if prev:
            from settings_store import test_mssql_connection, test_mongo_connection
            if prev.backend == "mssql" and prev.mssql:
                ok, _ = test_mssql_connection(prev.mssql)
                if ok:
                    _set_active_repo("mssql")
                    st.session_state.active_backend = "mssql"
            elif prev.backend == "mongodb" and prev.mongodb:
                ok, _ = test_mongo_connection(prev.mongodb)
                if ok:
                    _set_active_repo("mongodb", mongo_uri=prev.mongodb.uri, mongo_db=prev.mongodb.database)
                    st.session_state.active_backend = "mongodb"


def auto_import_master_data():
    """Auto-import master data on first run if database is empty."""
    if st.session_state.active_repo is not None:
        if "master_data_checked" not in st.session_state:
            st.session_state.master_data_checked = True
            try:
                repo = st.session_state.active_repo
                master_records = repo.master_list()
                record_count = len(master_records)
                
                if record_count == 0:
                    # Import from Excel automatically
                    from init_database import import_master_data
                    with st.spinner("Importing master data from Excel sheet..."):
                        result = import_master_data(repo)
                    
                    # Show import statistics
                    st.success(f"✅ Master data imported successfully! {result['imported']} records imported.")
                    if result['duplicates'] > 0:
                        with st.expander(f"⚠️ {result['duplicates']} duplicate mobile numbers found and skipped"):
                            st.write("Duplicate Mobile Numbers:")
                            st.write(result['duplicate_numbers'])
                    st.info("You can now manage master data through the Master Data Management page.")
                    st.session_state.master_data_exists = True
                else:
                    st.session_state.master_data_exists = True
            except FileNotFoundError:
                st.warning("⚠️ Excel file 'Verma R Master.xlsx' not found. Please add master data manually.")
            except Exception as e:
                st.error(f"⚠️ Error with master data: {e}")
                st.info("If you need to reimport, please clear the Master collection first from Master Data Management page.")


def load_custom_css():
    """Load custom CSS styling."""
    with open("style.css") as f:
        st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)


def main():
    """Main application entry point."""
    # Page configuration
    st.set_page_config(page_title="Call Log Management System", layout="wide")
    
    # Initialize session state
    initialize_session_state()
    
    # Auto-bootstrap from saved config
    auto_bootstrap_connection()
    
    # Auto-import master data if needed
    auto_import_master_data()
    
    # Load custom CSS
    load_custom_css()
    
    # Authentication check - show login page if DB is connected but user is not authenticated
    if st.session_state.active_repo is not None and not st.session_state.authenticated:
        render_login_page(st.session_state.active_repo)
        st.stop()
    
    # Determine default page based on setup status
    if st.session_state.active_repo is not None and st.session_state.authenticated and st.session_state.master_data_exists:
        default_index = 2  # Call Log Entry
    else:
        default_index = 0  # Settings
    
    # Create title bar with embedded navigation using HTML
    st.markdown('<div class="title-bar">📞  Implementors Call Log Management System  📞</div>', unsafe_allow_html=True)
    
    # Navigation bar right below title
    page_options = ["Settings", "Master Data Management", "Call Log Entry", "Reports", "Logout"]
    page = st.radio(
        "Navigation",
        page_options,
        index=default_index,
        horizontal=True,
        label_visibility="collapsed"
    )
    
    st.divider()
    
    # Handle Logout immediately
    if page == "Logout":
        # Close DB connections for this repo if supported
        repo_obj = st.session_state.active_repo
        if hasattr(repo_obj, "close") and callable(getattr(repo_obj, "close")):
            try:
                repo_obj.close()
            except Exception:
                # Best-effort; ignore errors on close
                pass
        st.session_state.active_backend = None
        st.session_state.active_repo = None
        st.session_state.authenticated = False
        st.session_state.current_user = None
        st.session_state.bootstrap_attempted = True  # avoid immediate auto-bootstrapping in same session
        st.session_state.logged_out = True
        st.rerun()
    
    # Footer
    current_date = datetime.now().strftime("%B %d, %Y")
    st.markdown(f"""
        <div class="footer">
            <p style="margin: 0;">Developed by <b>Indranil Chatterjee</b> | Version 1.0.0 | Date: {current_date}</p>
        </div>
    """, unsafe_allow_html=True)
    
    # Logged out screen
    if st.session_state.get("logged_out") is True:
        st.title("Logged out")
        st.info("This session is closed. You can safely close this browser tab.")
        st.stop()
    
    # Route to appropriate page
    if page == "Settings":
        render_settings_page(
            is_cloud=is_streamlit_cloud(),
            set_active_repo_func=_set_active_repo,
            save_settings_func=save_settings
        )
        st.stop()
    
    elif page == "Master Data Management":
        _ensure_repo_or_stop()
        render_master_data_page(st.session_state.active_repo, st.session_state.dropdowns)
    
    elif page == "Call Log Entry":
        _ensure_repo_or_stop()
        render_call_log_page(st.session_state.active_repo, st.session_state.dropdowns)
    
    elif page == "Reports":
        _ensure_repo_or_stop()
        render_reports_page(st.session_state.active_repo)


if __name__ == "__main__":
    main()
