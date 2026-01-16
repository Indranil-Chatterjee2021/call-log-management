"""
Settings Page Module
Handles database backend configuration (MSSQL/MongoDB)
"""
import streamlit as st
from urllib.parse import urlparse, urlunparse, quote_plus
import re

from settings_store import (
    AppSettings,
    MongoSettings,
    MSSQLSettings,
    test_mongo_connection,
    test_mssql_connection,
)
from bootstrap_config import save_bootstrap


def render_settings_page(is_cloud: bool, set_active_repo_func, save_settings_func):
    """
    Render the Settings page for database backend configuration.
    
    Args:
        is_cloud: Whether the app is running on Streamlit Cloud
        set_active_repo_func: Function to set the active repository
        save_settings_func: Function to save settings to database
    """
    st.title("Settings")
    st.subheader("Choose database backend (required)")

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
        
        st.divider()

        if backend == "MSSQL":
            _render_mssql_section(set_active_repo_func, save_settings_func)
        elif backend == "MongoDB":
            _render_mongodb_section(set_active_repo_func, save_settings_func)

    st.divider()
    
    # Email Configuration Section (only if backend is active)
    if st.session_state.active_repo is not None:
        _render_email_config_section()


def _render_mssql_section(set_active_repo_func, save_settings_func):
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

    col_btn1, col_btn2 = st.columns(2)
    with col_btn1:
        if st.button("Test MSSQL Connection", type="secondary"):
            ok, msg = test_mssql_connection(mssql_settings)
            (st.success if ok else st.error)(msg)
    with col_btn2:
        if st.button("Save & Activate MSSQL", type="primary"):
            ok, msg = test_mssql_connection(mssql_settings)
            if not ok:
                st.error(msg)
            else:
                # Auto-create tables for local MSSQL
                with st.spinner("Initializing database tables..."):
                    from db_init_mssql import init_mssql_database
                    table_ok, table_msg = init_mssql_database()
                    if table_ok:
                        st.success(table_msg)
                    else:
                        st.warning(table_msg)
                
                app_settings = AppSettings(backend="mssql", mssql=mssql_settings, mongodb=None)
                # Only save settings if this is first time setup
                if st.session_state.active_repo is None:
                    save_settings_func(app_settings)  # stored into dbo.AppConfig
                save_bootstrap(app_settings)  # local bootstrap for next startup
                set_active_repo_func("mssql")
                st.success("Database connected! Please login to continue.")
                st.rerun()


def _render_mongodb_section(set_active_repo_func, save_settings_func):
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
    mongo_db = st.text_input("Mongo Database *", value="call-logs", disabled=True)

    col_btn1, col_btn2 = st.columns(2)
    with col_btn1:
        if st.button("Test MongoDB Connection", type="secondary"):
            # Validate and encode
            encoded_uri, err = _encode_mongo_uri(mongo_uri_input)
            if err:
                st.error(err)
            else:
                mongo_settings = MongoSettings(uri=encoded_uri, database=mongo_db.strip())
                ok, msg = test_mongo_connection(mongo_settings)
                (st.success if ok else st.error)(msg)
    with col_btn2:
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
                    app_settings = AppSettings(backend="mongodb", mssql=None, mongodb=mongo_settings)
                    # Only save settings if this is first time setup
                    if st.session_state.active_repo is None:
                        save_settings_func(app_settings)  # stored into appConfig collection
                    save_bootstrap(app_settings)  # local bootstrap for next startup
                    set_active_repo_func("mongodb", mongo_uri=mongo_settings.uri, mongo_db=mongo_settings.database)
                    st.success("Database connected! Please login to continue.")
                    st.rerun()


def _render_email_config_section():
    """Render email configuration section."""
    st.divider()
    st.subheader("📧 Email Configuration (Optional)")
    st.info("Configure SMTP settings to enable email functionality in Reports.")
    
    repo = st.session_state.active_repo
    
    # Load existing config
    existing_config = repo.email_config_get()
    
    with st.form("email_config_form", width=1024):
        col1, col2 = st.columns(2)
        with col1:
            smtp_server = st.text_input(
                "SMTP Server", 
                value=existing_config.get("smtp_server", "smtp.gmail.com") if existing_config else "smtp.gmail.com",
                help="e.g., smtp.gmail.com, smtp.office365.com"
            )
            smtp_port = st.number_input(
                "SMTP Port", 
                value=existing_config.get("smtp_port", 587) if existing_config else 587,
                min_value=1,
                max_value=65535
            )
        with col2:
            smtp_user = st.text_input(
                "Email Address", 
                value=existing_config.get("smtp_user", "") if existing_config else "",
                help="Your email address"
            )
            smtp_password = st.text_input(
                "Email Password", 
                value="",
                type="password",
                help="For Gmail, use App Password (not your regular password)"
            )
        
        st.markdown("""
        **Note for Gmail users:**
        - Enable 2-Factor Authentication
        - Generate an App Password: [Google Account → Security → App passwords](https://myaccount.google.com/apppasswords)
        - Use the App Password here, not your regular password
        """)
        
        col_btn1, col_btn2, col_btn3 = st.columns([1, 1, 1])
        
        with col_btn1:
            test_btn = st.form_submit_button("🧪 Test Email", type="secondary")
        with col_btn2:
            save_btn = st.form_submit_button("💾 Save Config", type="primary")
        with col_btn3:
            delete_btn = st.form_submit_button("🗑️ Delete Config", type="secondary")
        
        if test_btn:
            if not smtp_server or not smtp_user or not smtp_password:
                st.error("All fields are required for testing!")
            else:
                # Test email connection
                try:
                    import smtplib
                    with smtplib.SMTP(smtp_server, smtp_port) as server:
                        server.starttls()
                        server.login(smtp_user, smtp_password)
                    st.success("✅ Email configuration is valid!")
                except Exception as e:
                    st.error(f"❌ Email test failed: {str(e)}")
        
        if save_btn:
            if not smtp_server or not smtp_user:
                st.error("SMTP Server and Email Address are required!")
            else:
                try:
                    config = {
                        "smtp_server": smtp_server,
                        "smtp_port": int(smtp_port),
                        "smtp_user": smtp_user,
                        "smtp_password": smtp_password if smtp_password else (existing_config.get("smtp_password", "") if existing_config else ""),
                    }
                    repo.email_config_save(config)
                    st.success("✅ Email configuration saved successfully!")
                    st.rerun()
                except Exception as e:
                    st.error(f"❌ Error saving config: {str(e)}")
        
        if delete_btn:
            try:
                repo.email_config_delete()
                st.success("✅ Email configuration deleted!")
                st.rerun()
            except Exception as e:
                st.error(f"❌ Error deleting config: {str(e)}")

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

def _render_logout_section():
    """Render logout section."""
    st.divider()
    st.subheader("Logout")
    st.markdown(
        """
        This will **log you out of the current session** and show a logout screen.
        
        Note: Streamlit runs as a server process, so "closing the application" means **closing the browser tab**.
        Your saved configuration remains, so the app can still auto-connect next time.
        """
    )

    if st.button("Logout", type="secondary", use_container_width=True):
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
        # Clear UI widget values so they don't reappear after logout/refresh
        for k in [
            "login_username", "login_password",
            "reg_username", "reg_password", "reg_password_confirm",
            "reset_username", "reset_new_password", "reset_confirm_password",
        ]:
            if k in st.session_state:
                del st.session_state[k]

        st.rerun()
