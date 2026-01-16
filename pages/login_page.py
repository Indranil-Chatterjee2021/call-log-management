"""
Login/Authentication Page Module
Handles user registration, login, and password reset
"""
import streamlit as st
from datetime import datetime
from auth import register_user, login_user, reset_password, check_users_exist


def render_login_page(repo):
    """
    Render the authentication page with registration, login, and password reset.
    
    Args:
        repo: Active repository instance
    """
    st.markdown('<div class="title-bar">📞  Implementors Call Log Management System  📞</div>', unsafe_allow_html=True)
    st.divider()
    
    st.title("🔐 User Authentication")
    
    # Check if any users exist
    users_exist = check_users_exist(repo)
    
    # Create tabs based on whether users exist
    if users_exist:
        tab1, tab2 = st.tabs(["Login", "Reset Password"])
        show_register = False
    else:
        tab1, tab2, tab3 = st.tabs(["Register", "Login", "Reset Password"])
        show_register = True
    
    # Register Tab (only shown if no users exist)
    if show_register:
        with tab1:
            _render_register_tab(repo)
        login_tab = tab2
        reset_tab = tab3
    else:
        login_tab = tab1
        reset_tab = tab2
    
    # Login Tab
    with login_tab:
        _render_login_tab(repo)
    
    # Reset Password Tab
    with reset_tab:
        _render_reset_tab(repo)
    
    # Footer
    current_date = datetime.now().strftime("%B %d, %Y")
    st.markdown(f"""
        <div class="footer">
            <p style="margin: 0;">Developed by <b>Indranil Chatterjee</b> | Version 1.0.0 | Date: {current_date}</p>
        </div>
    """, unsafe_allow_html=True)


def _render_register_tab(repo):
    """Render registration tab."""
    st.header("Register New User")
    st.info("No users found. Please register the first user account.")
    
    with st.form("register_form", width=1024):
        reg_username = st.text_input("Username *", key="reg_username")
        reg_password = st.text_input("Password *", type="password", key="reg_password")
        reg_password_confirm = st.text_input("Confirm Password *", type="password", key="reg_password_confirm")
        
        register_btn = st.form_submit_button("Register", type="primary", use_container_width=True)
        
        if register_btn:
            if not reg_username or not reg_password:
                st.error("Username and password are required!")
            elif reg_password != reg_password_confirm:
                st.error("Passwords do not match!")
            elif len(reg_password) < 6:
                st.error("Password must be at least 6 characters long!")
            else:
                success, message = register_user(repo, reg_username, reg_password)
                if success:
                    st.success(message)
                    st.info("Please switch to the Login tab to continue.")
                    st.rerun()
                else:
                    st.error(message)


def _render_login_tab(repo):
    """Render login tab."""
    st.header("Login")
    
    with st.form("login_form", width=1024):
        login_username = st.text_input("Username *", key="login_username")
        login_password = st.text_input("Password *", type="password", key="login_password")
        
        login_btn = st.form_submit_button("Login", type="primary", use_container_width=True)
        
        if login_btn:
            if not login_username or not login_password:
                st.error("Username and password are required!")
            else:
                success, message, user_data = login_user(repo, login_username, login_password)
                if success:
                    st.session_state.authenticated = True
                    st.session_state.current_user = user_data
                    
                    # Save authentication state to bootstrap config
                    from bootstrap_config import load_bootstrap, save_bootstrap
                    bootstrap_config = load_bootstrap()
                    if bootstrap_config:
                        bootstrap_config.authenticated_user = login_username
                        save_bootstrap(bootstrap_config)
                    
                    st.success(message)
                    # After login, navigate to Master Data Management (or Call Log Entry
                    # if master data already exists). This ensures the user lands on the
                    # appropriate page instead of remaining on Settings.
                    if st.session_state.get("master_data_exists"):
                        st.session_state.current_page_index = 3  # Call Log Entry
                    else:
                        st.session_state.current_page_index = 1  # Master Data Management
                    st.rerun()
                else:
                    st.error(message)


def _render_reset_tab(repo):
    """Render password reset tab."""
    st.header("Reset Password")
    
    with st.form("reset_form", width=1024):
        reset_username = st.text_input("Username *", key="reset_username")
        reset_new_password = st.text_input("New Password *", type="password", key="reset_new_password")
        reset_confirm_password = st.text_input("Confirm New Password *", type="password", key="reset_confirm_password")
        
        reset_btn = st.form_submit_button("Reset Password", type="primary", use_container_width=True)
        
        if reset_btn:
            if not reset_username or not reset_new_password:
                st.error("Username and new password are required!")
            elif reset_new_password != reset_confirm_password:
                st.error("Passwords do not match!")
            elif len(reset_new_password) < 6:
                st.error("Password must be at least 6 characters long!")
            else:
                success, message = reset_password(repo, reset_username, reset_new_password)
                if success:
                    st.success(message)
                else:
                    st.error(message)
