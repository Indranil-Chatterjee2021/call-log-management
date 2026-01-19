"""
Email Configuration Page Module
Handles SMTP settings for report distribution.
"""
import streamlit as st
import smtplib

def render_email_config_page():
    st.subheader("📧 Email Configuration")
    st.info("Configure SMTP settings to enable email functionality in Reports.")
    
    # Safety check: Ensure database is connected first
    if st.session_state.active_repo is None:
        st.warning("⚠️ Please configure and connect your **Database Settings** before setting up Email.")
        st.stop()

    repo = st.session_state.active_repo
    
    # Load existing config from the active repository
    existing_config = repo.email_config_get()
    
    with st.form("email_config_form"):
        col1, col2 = st.columns(2)
        with col1:
            smtp_server = st.text_input(
                "SMTP Server", 
                value=existing_config.get("smtp_server", "smtp.gmail.com") if existing_config else "smtp.gmail.com"
            )
            smtp_port = st.number_input(
                "SMTP Port", 
                value=existing_config.get("smtp_port", 587) if existing_config else 587
            )
        with col2:
            smtp_user = st.text_input(
                "Email Address", 
                value=existing_config.get("smtp_user", "") if existing_config else ""
            )
            smtp_password = st.text_input(
                "Email Password (App Password)", 
                value="",
                type="password"
            )
        
        st.caption("🔒 For Gmail, use an **App Password**, not your main account password.")
        
        c1, c2, c3 = st.columns(3)
        with c1:
            test_btn = st.form_submit_button("🧪 Test Connection")
        with c2:
            save_btn = st.form_submit_button("💾 Save Settings", type="primary")
        with c3:
            delete_btn = st.form_submit_button("🗑️ Remove Config")

        if test_btn:
            try:
                with smtplib.SMTP(smtp_server, smtp_port) as server:
                    server.starttls()
                    server.login(smtp_user, smtp_password)
                st.success("✅ Connection Successful!")
            except Exception as e:
                st.error(f"❌ Failed: {str(e)}")

        if save_btn:
            config = {
                "smtp_server": smtp_server,
                "smtp_port": int(smtp_port),
                "smtp_user": smtp_user,
                "smtp_password": smtp_password if smtp_password else (existing_config.get("smtp_password", "") if existing_config else ""),
            }
            repo.email_config_save(config)
            st.success("✅ Settings Saved!")
            st.rerun()

        if delete_btn:
            repo.email_config_delete()
            st.success("🗑️ Configuration Deleted")
            st.rerun()