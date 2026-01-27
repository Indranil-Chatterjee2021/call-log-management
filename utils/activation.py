import streamlit as st
import hashlib
import time
import subprocess
import os
from datetime import datetime

def get_hardware_id():
    """Generates a unique 16-char Hardware ID based on machine UUID."""
    try:
        if os.name == 'nt': # Windows
            cmd = "wmic csproduct get uuid"
        else: # Mac
            cmd = "ioreg -rd1 -c IOPlatformExpertDevice | grep -E '(UUID)'"
        
        uuid_str = subprocess.check_output(cmd, shell=True).decode().strip()
        # Hash the raw hardware string to a clean 16-char ID
        h = hashlib.sha256(uuid_str.encode()).hexdigest().upper()
        return f"{h[:4]}-{h[4:8]}-{h[8:12]}-{h[12:16]}"
    except:
        # Fallback for Streamlit Cloud (where hardware access is restricted)
        return "CLOUD-ENV-INSTANCE"

def verify_key(email, mobile, hwid, provided_key):
    """Verifies key against Email + Mobile + Hardware ID using Environment Secrets."""
    
    secret = st.secrets.get("ACTIVATION_SECRET") or os.getenv("ACTIVATION_SECRET")
    
    if not secret:
        print("Error: ACTIVATION_SECRET not configured.")
        return False

    if not all([email, mobile, hwid, provided_key]):
        return False

    clean_email = str(email).strip().lower()
    clean_mobile = str(mobile).strip()
    clean_hwid = str(hwid).strip().upper()
    
    # Generate the hash
    raw_str = f"{clean_email}{clean_mobile}{clean_hwid}{secret}"
    h = hashlib.sha256(raw_str.encode()).hexdigest().upper()
    
    expected_key = f"{h[:4]}-{h[4:8]}-{h[8:12]}-{h[12:16]}"
    return provided_key.strip().upper() == expected_key

def render_activation_ui(repo=None):
    hwid = get_hardware_id()
    
    st.markdown("""
        <style>
            .stAppDeployButton { display: none !important; }
            #MainMenu { visibility: hidden; }
            header { visibility: hidden; }
            .centered-header { text-align: center; padding: 10px; font-size: 2rem; font-weight: bold; }
            .centered-info { text-align: center; color: #555; margin-bottom: 20px; }
        </style>
        <div class="centered-header">🛡️ Application Activation</div>
    """, unsafe_allow_html=True)

    _, center_col, _ = st.columns([1, 2, 1])
    current_date = datetime.now().strftime("%B %d, %Y")
    st.markdown(f'<div class="fixed-footer"><b>© 2026 Call Log Management System | Version 1.0.0 | Date: {current_date}</b></div>', unsafe_allow_html=True)
    
    with center_col:
        with st.form("activation_form"):
            name = st.text_input("Full Name")
            email = st.text_input("Email Address")
            mobile = st.text_input("Mobile Number")
            serial_no = st.text_input("Serial No", value=hwid, disabled=True)
            st.caption(
                '<span style="color: #FF4B4B !important; font-weight: bold;">'
                'Contact Admin with your Serial No to get activation key.'
                '</span>', 
                unsafe_allow_html=True,
                text_alignment="center"
            )
            key = st.text_input("Activation Key", placeholder="XXXX-XXXX-XXXX-XXXX")
            st.caption(
                '<span style="color: #FF4B4B !important; font-weight: bold;">'
                'Please enter your 16-character key to connect this instance.'
                '</span>', 
                unsafe_allow_html=True,
                text_alignment="center"
            )
            
            # Create three columns; the middle one will contain the centered button
            col1, col2, col3 = st.columns([1, 2.4, 1])

            with col2:
                submit = st.form_submit_button("Activate Application", use_container_width=True)

            if submit:
                if verify_key(email, mobile, hwid, key):
                    if repo:
                        # Store HWID in DB so this DB record is locked to this machine
                        repo.save_activation(
                            name=name.strip(), 
                            email=email.strip(), 
                            mobile=mobile.strip(), 
                            key=key.strip().upper(),
                            hwid=hwid
                        )
                    st.session_state.app_activated = True
                    st.success("✅ Application Activated and Machine Locked!")
                    time.sleep(1)
                    st.rerun()
                else:
                    st.error("❌ Invalid Key for this specific Hardware ID.")