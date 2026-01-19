"""
Streamlit Call Log Application - Main Entry Point
Clean architecture with modular page components
"""
import streamlit as st
import pandas as pd
from datetime import datetime
import os
from pages.about_page import render_about_page
from utils.dropdown_data import get_dropdown_values
from storage import get_repository
from utils.logout import logout
from utils.settings_store import AppSettings, save_settings
from utils.bootstrap_config import load_bootstrap
from pages.settings_page import render_settings_page
from pages.login_page import render_login_page
from pages.master_data_page import render_master_data_page
from pages.call_log_page import render_call_log_page
from pages.reports_page import render_reports_page
from pages.misc_types_page import render_misc_types_page
from pages.email_config_page import render_email_config_page
from streamlit_option_menu import option_menu

# Page configuration
st.set_page_config(page_title="Call Log Management System", page_icon="📞", layout="wide")

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
    if 'master_data_exists' not in st.session_state:
        st.session_state.master_data_exists = False
    # Initialize dropdowns from DB when repo is available
    if 'dropdowns' not in st.session_state:
        if st.session_state.active_repo is not None:
            st.session_state.dropdowns = get_dropdown_values(st.session_state.active_repo)
        else:
            st.session_state.dropdowns = get_dropdown_values()


def auto_bootstrap_connection():
    """Attempt to auto-connect using previously saved configuration."""
    if st.session_state.active_repo is None and not st.session_state.bootstrap_attempted:
        st.session_state.bootstrap_attempted = True
        prev = load_bootstrap()
        if prev:
            from utils.settings_store import test_mssql_connection, test_mongo_connection
            if prev.backend == "mssql" and prev.mssql:
                ok, _ = test_mssql_connection(prev.mssql)
                if ok:
                    _set_active_repo("mssql")
                    st.session_state.active_backend = "mssql"
                    # Restore authentication state if it exists
                    if prev.authenticated_user:
                        st.session_state.authenticated = True
                        st.session_state.current_user = prev.authenticated_user
            elif prev.backend == "mongodb" and prev.mongodb:
                ok, _ = test_mongo_connection(prev.mongodb)
                if ok:
                    _set_active_repo("mongodb", mongo_uri=prev.mongodb.uri, mongo_db=prev.mongodb.database)
                    st.session_state.active_backend = "mongodb"
                    # Restore authentication state if it exists
                    if prev.authenticated_user:
                        st.session_state.authenticated = True
                        st.session_state.current_user = prev.authenticated_user


def check_master_data_exists():
    """Check if master data exists in the database."""
    if st.session_state.active_repo is not None:
        if "master_data_checked" not in st.session_state:
            st.session_state.master_data_checked = True
            try:
                repo = st.session_state.active_repo
                master_records = repo.master_list()
                record_count = len(master_records)
                st.session_state.master_data_exists = record_count > 0
                
                # Also refresh dropdowns from DB
                st.session_state.dropdowns = get_dropdown_values(repo)
            except Exception as e:
                st.session_state.master_data_exists = False


def load_custom_css():
    """Load custom CSS styling."""
    with open("style.css") as f:
        st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)


def main():
    """Main application entry point."""
    # Initialize session state
    initialize_session_state()
    # --- Environment-based Auto-bootstrap ---
    # Automatically loads saved database configuration ONLY if running locally.
    # On Streamlit Cloud, this is skipped to prevent cross-session configuration
    # and to respect the cloud's ephemeral/read-only filesystem.
    is_cloud = is_streamlit_cloud()
    if not is_cloud:
        auto_bootstrap_connection()
    
    # Check if master data exists (no auto-import)
    check_master_data_exists()
    
    # Load custom CSS
    load_custom_css()
    
    st.markdown(
      """
      <div class='sub-header-text'>
          <span class='side-icon'>📞</span> 
          Call Logging Management System 
          <span class='side-icon'>📞</span>
      </div>
      """, 
      unsafe_allow_html=True
  )
    # Check for logged out state first - show logged out screen without navigation
    if st.session_state.get("logged_out") is True: logout()
    
    # NOTE: Do not force the login page here. Allow the Settings page to be
    # reachable even when a backend is configured but the current session is
    # not authenticated. Authentication will be enforced when the user attempts
    # to navigate to protected pages (Master Data, Types, Call Log, Reports).
    
    # Define your options list once so you can reference it easily
    menu_options = ["Settings", "Email", "Master", "Types", "Call Log", "Reports", "About","Logout"]

    # Determine default page based on setup status
    if 'current_page_index' not in st.session_state:
        # CASE 1: Connected and Logged In
        if st.session_state.active_repo is not None and st.session_state.authenticated:
            if st.session_state.master_data_exists:
                st.session_state.current_page_index = 4  # Call Log Entry
            else:
                st.session_state.current_page_index = 2  # Master Data Management
        
        # CASE 2: Connected but NOT Logged In (This is your current issue!)
        elif st.session_state.active_repo is not None and not st.session_state.authenticated:
            # Send them to Call Log (which will trigger the Login screen automatically)
            st.session_state.current_page_index = 4 
            
        # CASE 3: Fresh start, no connection
        else:
            st.session_state.current_page_index = 0  # Settings
            
    current_index = st.session_state.current_page_index
    nav_l, nav_c, nav_r = st.columns([1, 4, 1]) 
    with nav_c:
      page = option_menu(
          menu_title=None,
            options=menu_options,
            icons=["gear", "envelope", "database", "tags", "telephone-inbound", "graph-up", 'info-circle', "box-arrow-right"],
            default_index=current_index,
            orientation='horizontal',
            styles={
            "container": {"background-color": "transparent", "padding": "0", "max-width": "100%", "margin": "-1px", "height": "40px"},
            "icon": {"color": "orange", "font-size": "16px"},
            "nav-link": {
                "font-size": "14px", 
                "color": "white", 
                "padding": "5px 15px",
                "margin": "0px 2px",
                "--hover-color": "#cf5e2eb9"  # OrangeRed hex code
            },
            "nav-link-selected": {
                "background-color": "#2e7bcf" # A slightly darker red for the active state
            },
          }
        )
    # Update current page index when navigation changes
    st.session_state.current_page_index = menu_options.index(page)

    # Handle Logout immediately
    if page == "Logout":
        # Clear authentication from bootstrap config
        from utils.bootstrap_config import load_bootstrap, save_bootstrap
        bootstrap_config = load_bootstrap()
        if bootstrap_config:
            bootstrap_config.authenticated_user = None
            save_bootstrap(bootstrap_config)
        
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
        # Remove UI widget values so they don't reappear after logout/refresh
        for k in [
            "login_username", "login_password",
            "reg_username", "reg_password", "reg_password_confirm",
            "reset_username", "reset_new_password", "reset_confirm_password",
        ]:
            if k in st.session_state:
                del st.session_state[k]

        # Remove page index if present
        if "current_page_index" in st.session_state:
            del st.session_state.current_page_index  # Remove page index so it doesn't interfere
        st.rerun()
    
    # Footer
    current_date = datetime.now().strftime("%B %d, %Y")
    st.markdown(f'<div class="fixed-footer"><b>© 2026 Call Log Management System | Version 1.0.0 | Date: {current_date}</b></div>', unsafe_allow_html=True)
    
    # We wrap the container in centered columns to position it in the middle of the 'wide' layout
    _, center_col, _ = st.columns([1, 6, 1])
    with center_col:
        with st.container(border=True, height=600, horizontal_alignment="left"):
          # Route to appropriate page
          # If a backend is configured but the session is not authenticated,
          # allow access to Settings but require login for other pages.
          if st.session_state.active_repo is not None and not st.session_state.authenticated:
              if page != "Settings":
                    render_login_page(st.session_state.active_repo)
                    st.stop()
          
          if page == "Settings":
              render_settings_page(
                  is_cloud,
                  set_active_repo_func=_set_active_repo,
                  save_settings_func=save_settings
              )
              # st.stop()

          if page == "About":
            render_about_page()    

          elif page == "Email":
            _ensure_repo_or_stop()
            render_email_config_page()    

          elif page == "Master":
              _ensure_repo_or_stop()
              render_master_data_page(st.session_state.active_repo, st.session_state.dropdowns)
          
          elif page == "Types":
              _ensure_repo_or_stop()
              render_misc_types_page(st.session_state.active_repo, st.session_state.dropdowns)
          
          elif page == "Call Log":
              _ensure_repo_or_stop()
              render_call_log_page(st.session_state.active_repo, st.session_state.dropdowns)
          
          elif page == "Reports":
              _ensure_repo_or_stop()
              render_reports_page(st.session_state.active_repo)


if __name__ == "__main__":
    main()
