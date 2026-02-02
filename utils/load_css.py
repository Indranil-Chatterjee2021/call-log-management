import sys
import os
import streamlit as st

def get_resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    if hasattr(sys, '_MEIPASS'):
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        return os.path.join(sys._MEIPASS, relative_path)
    
    # Check if we are running as a bundled EXE in --onedir mode
    exe_dir = os.path.dirname(sys.executable)
    exe_path = os.path.join(exe_dir, relative_path)
    if os.path.exists(exe_path):
        return exe_path
        
    # Fallback to current working directory (for VS Code/Development)
    return os.path.join(os.path.abspath("."), relative_path)

def load_custom_css():
    # 1. Force-hide Streamlit elements immediately
    st.markdown("""
        <style>
            [data-testid="stHeader"], .stAppDeployButton, header { display: none !important; }
            .block-container { padding-top: 0px !important; margin-top: -20px !important; }
            #MainMenu { visibility: hidden; }
            footer { visibility: hidden; }
        </style>
    """, unsafe_allow_html=True)

    # 2. Resolve the correct path for style.css
    css_path = get_resource_path("style.css")

    if os.path.exists(css_path):
        with open(css_path, "r", encoding="utf-8") as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
    else:
        # Debugging helper: will show in the console if the file is missing
        print(f"CSS Error: Could not find style.css at {css_path}")