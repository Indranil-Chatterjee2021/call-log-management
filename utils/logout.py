import streamlit as st
from datetime import datetime

def logout():
  """
  Handle user logout by updating session state.
  """
  st.divider()
    
  # Custom HTML for a perfect single-line alignment
  st.markdown(
        """
        <div style="display: flex; align-items: center; gap: 15px; margin-bottom: 20px;">
            <h1 style="margin: 0; padding: 0; white-space: nowrap; line-height: 1;">Logged out :</h1>
            <div style="background-color: rgba(28, 131, 225, 0.1); 
                        border: 1px solid rgba(28, 131, 225, 0.2); 
                        padding: 12px 20px; 
                        border-radius: 8px; 
                        color: #60b4ff; 
                        font-size: 16px;
                        width: 30%;
                        display: flex;
                        align-items: center;">
                This session is closed. You can safely close this browser tab.
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )
  
  # Footer Section
  current_date = datetime.now().strftime("%B %d, %Y")
  st.markdown(f'<div class="fixed-footer"><b>© 2026 Call Log Management System | Version 1.0.0 | Date: {current_date}</b></div>', unsafe_allow_html=True)
  st.stop()