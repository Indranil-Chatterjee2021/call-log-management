"""
Streamlit Call Log Application - Main Entry Point
Clean architecture with modular page components
"""
import streamlit as st
from streamlit_option_menu import option_menu
from datetime import datetime
from utils import (
    load_custom_css, initialize_session_state, is_streamlit_cloud,
    auto_bootstrap_connection, check_master_data_exists, get_hardware_id,
    verify_key, render_activation_ui, perform_logout, save_settings, set_active_repo
)
from views import (
    render_about_page, render_settings_page, render_login_page,
    render_master_data_page, render_call_log_page, render_reports_page,
    render_metadata_page, render_email_config_page
)
# Mapping of page names to their rendering functions
pages = {
    "Login": render_login_page,
    "Dashboard": render_master_data_page,
    "Settings": render_settings_page,
    "About": render_about_page,
    "Metadata": render_metadata_page,
    "Call Log": render_call_log_page,
    "Reports": render_reports_page,
    "Email Config": render_email_config_page,
}

# Page configuration
st.set_page_config(page_title="Call Log Management System", page_icon="📞", layout="wide")

# Main application logic
def main():
    """Main application entry point."""
    load_custom_css()
    initialize_session_state()
    is_cloud = is_streamlit_cloud()
    
    # 1. Bootstrapping (Local only)
    if not is_cloud: auto_bootstrap_connection()
    
    st.markdown("<div class='sub-header-text'><span class='side-icon'>📞</span> Call Log Management System <span class='side-icon'>📞</span></div>", unsafe_allow_html=True)

    # STEP 1: FORCE SETTINGS IF NOT CONNECTED
    if st.session_state.active_repo is None:
        _, center_col, _ = st.columns([1, 6, 1])
        with center_col:
            with st.container(border=True):
                render_settings_page(is_cloud, set_active_repo_func=set_active_repo, save_settings_func=save_settings)
        return

    # STEP 2: SILENT CLOUD ACTIVATION SYNC
    if not st.session_state.app_activated:
        try:
            record = st.session_state.active_repo.get_activation_record()
            if record:
                email, mobile, key = str(record.get('email', '')), str(record.get('mobile', '')), str(record.get('key', ''))
                hwid = get_hardware_id()
                if email and mobile and hwid and key and verify_key(email, mobile, hwid, key):
                    st.session_state.app_activated = True
                    st.rerun()
        except Exception:
            pass

    # STEP 3: MANUAL ACTIVATION GATE
    if not st.session_state.app_activated:
        _, center_col, _ = st.columns([1, 2, 1])
        with center_col:
            render_activation_ui(st.session_state.active_repo)
        return

    # STEP 4: NAVIGATION & APP CONTENT
    check_master_data_exists()

    # Mapping Menu Labels to Dictionary Keys
    menu_map = {
        "Settings": "Settings",
        "Email": "Email Config",
        "Master": "Dashboard",
        "Types": "Metadata",
        "Call Log": "Call Log",
        "Reports": "Reports",
        "About": "About"
    }
    menu_options = list(menu_map.keys()) + ["Logout"]
    
    if 'current_page_index' not in st.session_state:
        st.session_state.current_page_index = 4 if st.session_state.master_data_exists else 2
            
    nav_l, nav_c, nav_r = st.columns([1, 4, 1]) 
    with nav_c:
        selection = option_menu(
            menu_title=None,
            options=menu_options,
            icons=["gear", "envelope", "database", "tags", "telephone-inbound", "graph-up", 'info-circle', "box-arrow-right"],
            default_index=st.session_state.current_page_index,
            orientation='horizontal',
            styles={"nav-link": {"font-size": "14px", "padding": "5px 15px"}, "nav-link-selected": {"background-color": "#2e7bcf"}}
        )
    st.session_state.current_page_index = menu_options.index(selection)

    # Footer
    current_date = datetime.now().strftime("%B %d, %Y")
    st.markdown(f'<div class="fixed-footer"><b>© 2026 Call Log Management System | Version 1.0.0 | Date: {current_date} | Developed By: Indranil Chatterjee</b></div>', unsafe_allow_html=True)
    
    if selection == "Logout":
        perform_logout()
        return

    _, center_col, _ = st.columns([1, 6, 1])
    with center_col:
        with st.container(border=True, height=600):
            # Auth Gate
            if not st.session_state.authenticated and selection not in ["Settings", "About"]:
                pages["Login"](st.session_state.active_repo)
            else:
                # Dynamic Routing using your 'pages' dictionary
                page_key = menu_map.get(selection)
                render_func = pages.get(page_key)

                if selection == "Settings":
                    render_func(is_cloud, set_active_repo, save_settings)
                elif selection == "About":
                    render_func()
                elif selection in ["Master", "Types", "Call Log"]:
                    render_func(st.session_state.active_repo, st.session_state.dropdowns)
                elif selection in ["Reports", "Email"]:
                    render_func(st.session_state.active_repo) if page_key != "About" else render_func()

if __name__ == "__main__":
    main()