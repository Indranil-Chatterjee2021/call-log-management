"""
Settings Page Module
Handles database backend configuration (MSSQL/MongoDB)
"""
import streamlit as st
from urllib.parse import urlparse, urlunparse, quote_plus
import re
import os
import json
from pathlib import Path
from datetime import datetime

from utils.settings_store import (
    AppSettings,
    MongoSettings,
    MSSQLSettings,
    test_mongo_connection,
    test_mssql_connection,
)
from utils.bootstrap_config import save_bootstrap

def render_settings_page(is_cloud: bool, set_active_repo_func, save_settings_func):
    """
    Render the Settings page for database backend configuration.
    
    Args:
        is_cloud: Whether the app is running on Streamlit Cloud
        set_active_repo_func: Function to set the active repository
        save_settings_func: Function to save settings to database
    """
    st.subheader("💾 Database settings (required)")

    # Check if a backend is already active
    active_backend = st.session_state.get("active_backend")
    
    # Determine available backends based on environment
    if is_cloud:
        # Only MongoDB for Streamlit Cloud
        backend_options = ["MongoDB"]
        st.info("ℹ️ Running on Streamlit Cloud. Only MongoDB is available for cloud deployment.")
    else:
        # Both options for local runs
        backend_options = ["MSSQL", "MongoDB"]

    # If backend is already active, show it as disabled (locked)
    if active_backend:
        # Map backend names
        backend_display = "MongoDB" if active_backend == "mongodb" else "MSSQL"
        st.info(f"🔒 **Currently active backend: {backend_display}** (Logout to change backend)")
    else:
        backend = st.radio(
            "Backend Database *",
            options=backend_options,
            horizontal=True,
            index=None,
            help="You must select a backend before using the application.",
        )
        st.markdown("<hr style='margin: 5px 0px; opacity: 0.5;'>", unsafe_allow_html=True)

        if backend == "MSSQL":
            _render_mssql_section(set_active_repo_func, save_settings_func)
        elif backend == "MongoDB":
            _render_mongodb_section(is_cloud, set_active_repo_func, save_settings_func)

    # Show presence of .db_config.json in working directory (useful on cloud)
    try:
        if Path(".db_config.json").exists():
            st.info("`.db_config.json` found in application working directory.")
    except Exception:
        # Non-fatal: ignore filesystem errors in restrictive environments
        pass


def _render_mssql_section(is_cloud: bool, set_active_repo_func, save_settings_func):
    """Render MSSQL connection configuration section."""
    st.markdown("**MSSQL Connection Details**")
    col1, col2 = st.columns(2)
    with col1:
        mssql_server = st.text_input("Server *", value="")
        mssql_db = st.text_input("Database *", value="CALLLOG", disabled=True)
        mssql_user = st.text_input("Username *", value="sa")
    with col2:
        mssql_password = st.text_input("Password *", value="", type="password")
        mssql_driver = st.text_input("ODBC Driver", value="{ODBC Driver 17 for SQL Server}")

    mssql_settings = MSSQLSettings(
        server=mssql_server.strip(),
        database=mssql_db.strip(),
        username=mssql_user.strip(),
        password=mssql_password,
        driver=mssql_driver.strip() or "{ODBC Driver 17 for SQL Server}",
    )

    if st.button("Save & Activate MSSQL", type="primary"):
      ok, msg = test_mssql_connection(mssql_settings)
      if not ok:
          st.error(msg)
      else:
          # Auto-create tables for local MSSQL
          st.success(msg)
          with st.spinner("Initializing database tables..."):
              from utils.db_init_mssql import init_mssql_database
              table_ok, table_msg = init_mssql_database()
              if table_ok:
                  st.success(table_msg)
              else:
                  st.warning(table_msg)
          
          app_settings = AppSettings(backend="mssql", mssql=mssql_settings, mongodb=None)
          # Only save settings if this is first time setup
          if st.session_state.active_repo is None:
              save_settings_func(app_settings)  # stored into dbo.AppConfig
          # If False, then call save_bootstrap
          if not is_cloud:
              save_bootstrap(app_settings)
              print("DEBUG: Local environment detected. Bootstrap settings saved.")

          st.write(f"Cloud Detection Status: {is_cloud}")
          set_active_repo_func("mssql")
          redirect_to()


def _render_mongodb_section(is_cloud: bool, set_active_repo_func, save_settings_func):
    """Render MongoDB connection configuration section."""
    st.markdown("**MongoDB Connection Details**")
    # Mask the URI in the UI so credentials don't show in plaintext.
    # Use placeholder to indicate default; if left blank we'll use the default locally.
    # Streamlit's password input shows a reveal (eye) icon which toggles visibility.
    # We intentionally hide that reveal button via a small CSS injection so the
    # value cannot be exposed by clicking the eye.
    st.markdown(
        """
        <style>
        /* Hide Streamlit's password reveal/hide button for inputs that contain 'password' in the aria-label */
        button[aria-label*="password"] {
            display: none !important;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    mongo_uri_input = st.text_input(
        "Mongo URI *",
        value="",
        placeholder="mongodb://localhost:27017",
        type="password",
    )
    mongo_db = st.text_input("Enter Mongo Database Name *", placeholder="call-logs", disabled=False)

    if st.button("Save & Activate MongoDB", type="primary"):
      encoded_uri, err = _encode_mongo_uri(mongo_uri_input)
      if err:
          st.error(err)
      else:
          mongo_settings = MongoSettings(uri=encoded_uri, database=mongo_db.strip())
          ok, msg = test_mongo_connection(mongo_settings)
          if not ok:
              st.error(msg)
          else:
              st.success(msg)
              app_settings = AppSettings(backend="mongodb", mssql=None, mongodb=mongo_settings)
              print(f"DEBUG: IS_STREAMLIT_CLOUD is {is_cloud}")
              if st.session_state.active_repo is None:
                  save_settings_func(app_settings)  # stored into appConfig collection
              # If False, then call save_bootstrap
              if not is_cloud:
                  save_bootstrap(app_settings)
                  print("DEBUG: Local environment detected. Bootstrap settings saved.")
              else:
                  print("DEBUG: Cloud environment detected. Skipping bootstrap save.")
              st.write(f"Cloud Detection Status: {is_cloud}")
              set_active_repo_func("mongodb", mongo_uri=mongo_settings.uri, mongo_db=mongo_settings.database)
              redirect_to()          


def _encode_mongo_uri(uri: str):
        """Validate and return (encoded_uri, error_message).

        Rules:
        - Empty URI -> error (we do not silently fallback to localhost)
        - Scheme must be 'mongodb' or 'mongodb+srv'
        - Hostname must be present
        - If credentials are present they will be URL-encoded (avoids double-encoding)
        - If the URI contains an '@' but username/password cannot be parsed, return an error
        """
        uri = (uri or "").strip()
        if not uri:
            return None, "Please enter the Mongo URI (e.g. mongodb://user:pass@host:27017)."

        parsed = urlparse(uri)

        # Basic validation
        if not parsed.scheme or parsed.scheme not in ("mongodb", "mongodb+srv"):
            return None, "Invalid Mongo URI: missing or unsupported scheme (expected 'mongodb://' or 'mongodb+srv://')."
        if not parsed.hostname:
            return None, "Invalid Mongo URI: missing hostname. Please include host (e.g. host:27017)."

        raw = uri
        # If there is an '@' in the netloc but parser didn't extract username/password,
        # it's likely the URI contains characters that prevented parsing.
        if "@" in parsed.netloc and (parsed.username is None and parsed.password is None):
            return None, (
                "Unable to parse credentials from the provided URI. "
                "Please URL-encode special characters in username/password or provide credentials in the form user:pass@host."
            )

        username = parsed.username
        password = parsed.password

        def _maybe_quote(s: str) -> str:
            if s is None:
                return None
            # If already contains percent-encoded octets, assume it's encoded
            if re.search(r"%[0-9A-Fa-f]{2}", s):
                return s
            return quote_plus(s)

        uq = _maybe_quote(username)
        pq = _maybe_quote(password)

        host = parsed.hostname or ""
        port = f":{parsed.port}" if parsed.port else ""

        netloc = ""
        if uq is not None:
            netloc += uq
        if pq is not None:
            netloc += f":{pq}"
        if uq is not None:
            netloc += "@"
        netloc += f"{host}{port}"

        new_parsed = parsed._replace(netloc=netloc)
        return urlunparse(new_parsed), None


def redirect_to():
  # Check if Master Data exists to decide where to send the user after login
  if st.session_state.get('master_data_exists', False):
      st.session_state.current_page_index = 4  # Send to Call Log Entry
  else:
      st.session_state.current_page_index = 2  # Send to Master Management to finish setup

  st.success("Database connected! Redirecting to Login...")
  st.rerun()