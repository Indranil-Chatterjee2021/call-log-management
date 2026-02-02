"""
Call Log Entry Page Module
Handles creation of new call log entries with auto-fill from master data
"""
import streamlit as st
from datetime import datetime
from time import sleep

from utils import get_logged_in_user
from utils.data_models import CallLog, MasterRecord

def render_call_log_page(repo, dropdowns):
    st.subheader("📝 Enter New Call Log Entry")
    # Access the username from the stored dictionary
    username = get_logged_in_user()

    if st.session_state.get('reset_search_now', False):
        st.session_state["search_mobile_key"] = ""
        st.session_state['reset_search_now'] = False
    
    # 1. Initialize the storage for fetched data
    if 'fetched_data' not in st.session_state:
        st.session_state.fetched_data = None

    # 2. Search Section (Note the unique key: 'search_mobile_key')
    mobile_no_input = st.text_input(
        "Enter Mobile No:", 
        key="search_mobile_key"
    )
    
    if st.button("Fetch from Master", key="auto_fill_btn", type="primary"):
        if mobile_no_input:
            result = repo.master_get_by_mobile(mobile_no_input.strip())
            if result:
                st.session_state.fetched_data = result
                st.success("✅ Data fetched successfully!")
                st.rerun()
            else:
                st.warning("⚠️ No matching record found")
        else:
            st.warning("⚠️ Please enter Mobile No first")
    
    st.divider()

    # 3. Create a fallback to prevent 'NoneType' errors
    # If session_state.fetched_data is None, we use an empty MasterRecord
    rec = st.session_state.fetched_data or MasterRecord(
        mobile="", project="", town="", requester="", rd_code="", 
        rd_name="", state="", designation="", name=""
    )
    
    # 4. Render Form
    # IMPORTANT: We use 'value=rec.field' to populate. 
    # We use 'key=f"form_{field}"' to ensure uniqueness.
    if st.session_state.fetched_data:
        rec = st.session_state.fetched_data
        with st.form("call_log_form", clear_on_submit=True):
            col1, col2 = st.columns(2)
            
            with col1:
                date_val = st.date_input("Date", value=datetime.now().date(), format="DD/MM/YYYY", disabled=True)
                mobile = st.text_input("Mobile No *", value=rec.mobile, disabled=True)
                project = st.text_input("Project", value=rec.project, disabled=True)
                town = st.text_input("Town", value=rec.town, disabled=True)
                requester = st.text_input("Requester", value=rec.requester, disabled=True)
                rd_code = st.text_input("RD Code", value=rec.rd_code, disabled=True)
                rd_name = st.text_input("RD Name", value=rec.rd_name, disabled=True)
                state = st.text_input("State", value=rec.state, disabled=True)
            
            with col2:
                designation = st.text_input("Designation", value=rec.designation, disabled=True)
                name = st.text_input("Name", value=rec.name, disabled=True)
                # Selectboxes which need user input
                module = st.selectbox("Module", [""] + dropdowns['modules'])
                issue = st.selectbox("Issue", [""] + dropdowns['issues'])
                solution = st.selectbox("Solution", [""] + dropdowns['solutions'])
                solved_on = st.selectbox("Solved On", [""] + dropdowns['solved_on'])
                call_on = st.selectbox("Call On", [""] + dropdowns['call_on'])
                call_type = st.selectbox("Type", [""] + dropdowns['types'])
            
            if st.form_submit_button("Add Call Log", type="primary"):
                if not mobile:
                    st.error("Mobile No is required!")
                else:
                    try:
                        new_log = CallLog(
                            mobile=mobile,
                            date=datetime.combine(date_val, datetime.min.time()),
                            project=project, town=town, requester=requester,
                            rd_code=rd_code, rd_name=rd_name, state=state,
                            designation=designation, name=name, module=module,
                            issue=issue, solution=solution, solved_on=solved_on,
                            call_on=call_on, call_type=call_type, created_at=datetime.combine(date_val, datetime.min.time()),
                            created_by=username
                        )
                        
                        if repo.calllog_create(new_log):
                            # Clear the fetched data so the next form is empty
                            st.session_state.fetched_data = None
                            st.session_state.reset_search_now = True
                            st.success(f"✅ Call log added for {rd_name}!", icon='🎉')
                            sleep(2)
                            st.rerun()
                    except Exception as e:
                        st.error(f"⚠️ Error adding call log entry: {e}")
    else:
        st.info("💡 Please search for a record in Master.")                    
