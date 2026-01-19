"""
Call Log Entry Page Module
Handles creation of new call log entries with auto-fill from master data
"""
import streamlit as st
from datetime import datetime


def render_call_log_page(repo, dropdowns):
    """
    Render the Call Log Entry page.
    
    Args:
        repo: Active repository instance
        dropdowns: Dictionary of dropdown values
    """
    st.subheader("📝 Enter New Call Log Entry")
    
    # Initialize session state for form values
    if 'call_form_values' not in st.session_state:
        st.session_state.call_form_values = {}
    
    mobile_no_input = st.text_input(
        "Enter Mobile No:", 
        key="mobile_input",
        width=1024,
        value=st.session_state.call_form_values.get('mobile_no', '')
    )
    
    auto_fill_clicked = st.button("Fetch from Master", key="auto_fill_btn", type="primary")
        
    if auto_fill_clicked:
        if mobile_no_input:
            master_data = repo.master_get_by_mobile(mobile_no_input.strip())
            if master_data:
                # Update both call_form_values dict AND individual form field keys
                st.session_state.call_form_values = {
                    'mobile_no': mobile_no_input.strip(),
                    'project': master_data.get('Project', '') or '',
                    'town': master_data.get('Town', '') or '',
                    'requester': master_data.get('Requester', '') or '',
                    'rd_code': master_data.get('RDCode', '') or '',
                    'rd_name': master_data.get('RDName', '') or '',
                    'state': master_data.get('State', '') or '',
                    'designation': master_data.get('Designation', '') or '',
                    'name': master_data.get('Name', '') or ''
                }
                # Also update the form field keys directly so Streamlit uses them
                st.session_state.call_mobile = mobile_no_input.strip()
                st.session_state.call_project = master_data.get('Project', '') or ''
                st.session_state.call_town = master_data.get('Town', '') or ''
                st.session_state.call_requester = master_data.get('Requester', '') or ''
                st.session_state.call_rd_code = master_data.get('RDCode', '') or ''
                st.session_state.call_rd_name = master_data.get('RDName', '') or ''
                st.session_state.call_state = master_data.get('State', '') or ''
                st.session_state.call_designation = master_data.get('Designation', '') or ''
                st.session_state.call_name = master_data.get('Name', '') or ''
                st.success("✅ Data auto-filled from Master!")
                st.rerun()
            else:
                st.warning("⚠️ No matching record found in Master table")
        else:
            st.warning("⚠️ Please enter Mobile No first")
    
    st.divider()
    
    # Display success message if it exists (from previous submission)
    if 'call_log_success_msg' in st.session_state:
        st.success(st.session_state.call_log_success_msg)
        del st.session_state.call_log_success_msg
    
    # Initialize form field keys if they don't exist (avoids widget conflict warning)
    form_fields = {
        'call_mobile': 'mobile_no',
        'call_project': 'project',
        'call_town': 'town',
        'call_requester': 'requester',
        'call_rd_code': 'rd_code',
        'call_rd_name': 'rd_name',
        'call_state': 'state',
        'call_designation': 'designation',
        'call_name': 'name'
    }
    
    for key, value_key in form_fields.items():
        if key not in st.session_state:
            st.session_state[key] = st.session_state.call_form_values.get(value_key, '')
    
    with st.form("call_log_form", width=1028):
        col1, col2 = st.columns(2)
        
        with col1:
            date = st.date_input("Date", value=datetime.now().date(), key="call_date")
            mobile_no = st.text_input("Mobile No *", key="call_mobile")
            project = st.text_input("Project", key="call_project")
            town = st.text_input("Town", key="call_town")
            requester = st.text_input("Requester", key="call_requester")
            rd_code = st.text_input("RD Code", key="call_rd_code")
            rd_name = st.text_input("RD Name", key="call_rd_name")
            state = st.text_input("State", key="call_state")
        
        with col2:
            designation = st.text_input("Designation", key="call_designation")
            name = st.text_input("Name", key="call_name")
            module = st.selectbox("Module", [""] + dropdowns['modules'], key="call_module")
            issue = st.selectbox("Issue", [""] + dropdowns['issues'], key="call_issue")
            solution = st.selectbox("Solution", [""] + dropdowns['solutions'], key="call_solution")
            solved_on = st.selectbox("Solved On", [""] + dropdowns['solved_on'], key="call_solved_on")
            call_on = st.selectbox("Call On", [""] + dropdowns['call_on'], key="call_call_on")
            call_type = st.selectbox("Type", [""] + dropdowns['types'], key="call_type")
        
        submitted = st.form_submit_button("Add Call Log", type="primary")
        if submitted:
            if not mobile_no:
                st.error("Mobile No is required!")
            else:
                try:
                    inserted_id = repo.calllog_create(
                        {
                            "Date": datetime.combine(date, datetime.min.time()),
                            "MobileNo": mobile_no,
                            "Project": project,
                            "Town": town,
                            "Requester": requester,
                            "RDCode": rd_code,
                            "RDName": rd_name,
                            "State": state,
                            "Designation": designation,
                            "Name": name,
                            "Module": module,
                            "Issue": issue,
                            "Solution": solution,
                            "SolvedOn": solved_on,
                            "CallOn": call_on,
                            "Type": call_type,
                        }
                    )
                    # Only show success message if record was actually created
                    if inserted_id:
                        st.session_state.call_log_success_msg = "✅ Call log entry added successfully!"
                        # Clear form values from both locations
                        st.session_state.call_form_values = {}
                        # Clear all form field keys including text inputs, dropdowns, and mobile input
                        for key in ['mobile_input', 'call_mobile', 'call_project', 'call_town', 'call_requester', 
                                    'call_rd_code', 'call_rd_name', 'call_state', 'call_designation', 'call_name',
                                    'call_module', 'call_issue', 'call_solution', 'call_solved_on', 
                                    'call_call_on', 'call_type']:
                            if key in st.session_state:
                                del st.session_state[key]
                        st.rerun()
                    else:
                        st.error("Failed to create call log entry - no ID returned")
                except Exception as e:
                    st.error(f"Error adding call log entry: {e}")
