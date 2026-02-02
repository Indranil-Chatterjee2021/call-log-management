import streamlit as st
import time
import os
from datetime import datetime
from utils.backup_service import run_mongo_backup

def _perform_logout_logic():
    """Renders the backup status with a Bold Yellow path and corrected slashes."""
    settings = st.session_state.get("app_settings")
    
    # Matching Nav Bar width
    _, center_col, _ = st.columns([1, 2, 1])

    with center_col:
        st.header("🚪 Logging Out")
        st.divider()

        if settings and settings.mongodb and settings.mongodb.backup_path:
            with st.status("🔄 Initiating System Backup...", expanded=True) as status:
                st.write("🔍 Connecting to MongoDB cluster...")
                time.sleep(0.4)
                
                success, result = run_mongo_backup(
                    uri=settings.mongodb.uri,
                    db_name=settings.mongodb.database,
                    backup_root=settings.mongodb.backup_path
                )
                
                if success:
                    # 1. Correct the slashes and build the path
                    # Using os.path.normpath ensures slashes are consistent for your OS
                    full_path = os.path.normpath(os.path.join(settings.mongodb.backup_path, result))
                    
                    # 2. Styling for Bold Yellow color
                    # We use inline CSS to force the yellow color in the Markdown
                    formatted_path = f'<span style="color: #FFD700; font-weight: bold;">{full_path}</span>'
                    
                    st.write("🚀 Verifying backup file integrity...")
                    time.sleep(0.6)
                    
                    # Update status label
                    status.update(label="✅ Backup Successful", state="complete", expanded=True)
                    
                    # Show the path with the yellow color styling
                    st.markdown(f"**Backup Location:** {formatted_path}", unsafe_allow_html=True)
                    st.divider()
                    
                    # 3. Integrated "Logged out" message
                    st.markdown(
                        """
                        <div style="display: flex; align-items: center; gap: 15px; padding: 10px;">
                            <h3 style="margin: 0; color: white; white-space: nowrap;">Logged out :</h3>
                            <div style="background-color: rgba(28, 131, 225, 0.1); 
                                        border: 1px solid rgba(28, 131, 225, 0.2); 
                                        padding: 8px 15px; border-radius: 5px; color: #60b4ff;">
                                Backup complete. This session is safely closed.
                            </div>
                        </div>
                        """, 
                        unsafe_allow_html=True
                    )
                else:
                    status.update(label="❌ Backup Failed", state="error", expanded=True)
                    st.error(f"Reason: {result}")
                    if not st.button("Ignore and Logout Anyway"):
                        st.stop()

        # Clear session data
        st.session_state.clear()
        
        # Footer
        current_date = datetime.now().strftime("%B %d, %Y")
        st.markdown(
            f'<div class="fixed-footer"><b>© 2026 Call Log Management System | Version 1.0.0 | Date: {current_date} | Developed By: Indranil Chatterjee</b></div>',
            unsafe_allow_html=True
        )
    st.stop()

def perform_logout():
    """Renders centered confirmation expander matching Nav Bar width."""
    if st.session_state.get("logging_out"):
        _perform_logout_logic()
        return

    # Use columns to center the Expander and match the Nav Bar length
    left_buf, center_col, right_buf = st.columns([1, 2, 1])

    with center_col:
        # Custom CSS to remove the "blank container" gap and style the expander
        st.markdown("""
            <style>
                /* Removes the extra padding often left by empty containers */
                .element-container:empty { display: none; }
                /* Optional: Ensure buttons are truly centered */
                .stButton > button { margin: 0 auto; display: block; }
            </style>
        """, unsafe_allow_html=True)

        with st.expander("🚪 Confirm Logout", expanded=True):
            st.write("Clicking **Logout** will perform a backup (if configured) and then end your session.")
            
            # Nested columns for the buttons inside the centered expander
            col_yes, col_cancel = st.columns(2)

            with col_yes:
                if st.button("Yes — Backup & Logout", key="logout_yes", use_container_width=True, type="primary"):
                    st.session_state.logging_out = True
                    st.rerun()

            with col_cancel:
                if st.button("Cancel", key="logout_cancel", use_container_width=True):
                    st.session_state.logging_out = False
                    st.session_state.current_page_index = 4
                    st.rerun()