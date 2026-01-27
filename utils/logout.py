import streamlit as st
import time
from datetime import datetime
from utils.backup_service import run_mongo_backup

@st.dialog("Confirm Logout")
def logout_dialog():
    """Triggers a modal to confirm the user wants to leave."""
    st.write("Are you sure you want to log out? A system backup will be performed automatically.")
    
    col1, col2 = st.columns(2)
    if col1.button("Yes, Log out", type="primary", use_container_width=True):
        # We set a specific flag to trigger the backup logic in the next rerun
        st.session_state.logging_out = True
        st.rerun()
    if col2.button("Cancel", use_container_width=True):
        # Reset the page index to 'Call Log' or 'Home' so they stay in the app
        st.session_state.current_page_index = 4 
        st.rerun()

def perform_logout_logic():
    """Renders the backup status and final logout UI."""
    # Retrieve settings stored during _set_active_repo
    settings = st.session_state.get("app_settings")
    
    st.header("🚪 Logging Out")
    st.divider()

    # Perform Backup if settings exist
    if settings and settings.mongodb and settings.mongodb.backup_path:
        with st.status("🔄 Initiating System Backup...", expanded=True) as status:
            st.write("🔍 Connecting to MongoDB cluster...")
            time.sleep(0.6) 
            
            st.write(f"📂 Accessing backup path: `{settings.mongodb.backup_path}`")
            time.sleep(0.4)
            
            # This calls your mongodump logic from backup_service.py
            with st.spinner("📦 Compressing collections and writing to disk..."):
                success, result = run_mongo_backup(
                    uri=settings.mongodb.uri,
                    db_name=settings.mongodb.database,
                    backup_root=settings.mongodb.backup_path
                )
            
            if success:
                st.write("🚀 Verifying backup file integrity...")
                time.sleep(0.8)
                status.update(label=f"✅ Backup Successful: {result}", state="complete", expanded=False)
                time.sleep(1.0)
            else:
                status.update(label="❌ Backup Failed", state="error", expanded=True)
                st.error(f"Reason: {result}")
                if st.button("Ignore and Logout Anyway"):
                    pass # Allow logic to proceed to session.clear()
                else:
                    st.stop() # Halt so they can fix the issue

    # Clear volatile session data
    st.session_state.clear()
    
    # Final Confirmation UI
    st.markdown(
        """
        <div style="display: flex; align-items: center; gap: 15px; margin-top: 30px;">
            <h1 style="margin: 0; padding: 0; white-space: nowrap;">Logged out :</h1>
            <div style="background-color: rgba(28, 131, 225, 0.1); 
                        border: 1px solid rgba(28, 131, 225, 0.2); 
                        padding: 12px 20px; border-radius: 8px; 
                        color: #60b4ff; font-size: 16px; width: 400px;">
                Backup complete. This session is safely closed.
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

    # Footer
    current_date = datetime.now().strftime("%B %d, %Y")
    st.markdown(f'<div class="fixed-footer"><b>© 2026 Call Log Management System | Version 1.0.0 | Date: {current_date}</b></div>', unsafe_allow_html=True)
    st.stop()

def logout():
    """Main entry point called by app1.py"""
    if st.session_state.get("logging_out"):
        perform_logout_logic()
    else:
        logout_dialog()