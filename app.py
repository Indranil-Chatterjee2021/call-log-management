"""
Streamlit Call Log Application
"""
import streamlit as st
import pandas as pd
from datetime import datetime
import io
from dropdown_data import get_dropdown_values
from storage import DateRange, get_repository
from settings_store import (
    AppSettings,
    MongoSettings,
    MSSQLSettings,
    save_settings,
    test_mongo_connection,
    test_mssql_connection,
)
from bootstrap_config import load_bootstrap, save_bootstrap

# Page configuration
st.set_page_config(page_title="Call Log Management System", layout="wide")

# Mandatory backend selection:
# - user must pick backend and test/save before using other pages
if "active_backend" not in st.session_state:
    st.session_state.active_backend = None
if "active_repo" not in st.session_state:
    st.session_state.active_repo = None
if "bootstrap_attempted" not in st.session_state:
    st.session_state.bootstrap_attempted = False

# Initialize session state
if 'dropdowns' not in st.session_state:
    st.session_state.dropdowns = get_dropdown_values()
if 'master_data_exists' not in st.session_state:
    st.session_state.master_data_exists = False


def _ensure_repo_or_stop() -> None:
    if st.session_state.active_repo is None:
        st.warning("Please configure your database backend in **Settings** first.")
        st.stop()


def _set_active_repo(backend: str, mongo_uri: str | None = None, mongo_db: str | None = None) -> None:
    st.session_state.active_backend = backend
    if backend == "mongodb":
        st.session_state.active_repo = get_repository(
            backend_override="mongodb",
            mongo_uri_override=mongo_uri,
            mongo_db_override=mongo_db,
        )
    else:
        st.session_state.active_repo = get_repository(backend_override="mssql")

def _df_from_records(records: list[dict]) -> pd.DataFrame:
    if not records:
        return pd.DataFrame()
    df = pd.DataFrame.from_records(records)
    # Remove id column if present
    if 'id' in df.columns:
        df = df.drop(columns=['id'])
    return df

# Auto-activate previously saved config (local bootstrap file)
if st.session_state.active_repo is None and not st.session_state.bootstrap_attempted:
    st.session_state.bootstrap_attempted = True
    prev = load_bootstrap()
    if prev:
        if prev.backend == "mssql" and prev.mssql:
            ok, _ = test_mssql_connection(prev.mssql)
            if ok:
                _set_active_repo("mssql")
                st.session_state.active_backend = "mssql"
        elif prev.backend == "mongodb" and prev.mongodb:
            ok, _ = test_mongo_connection(prev.mongodb)
            if ok:
                _set_active_repo("mongodb", mongo_uri=prev.mongodb.uri, mongo_db=prev.mongodb.database)
                st.session_state.active_backend = "mongodb"

# Auto-import master data on first run (if empty)
if st.session_state.active_repo is not None:
    if "master_data_checked" not in st.session_state:
        st.session_state.master_data_checked = True
        try:
            repo = st.session_state.active_repo
            master_records = repo.master_list()
            record_count = len(master_records)
            
            if record_count == 0:
                # Import from Excel automatically
                from init_database import import_master_data
                with st.spinner("Importing master data from Excel sheet..."):
                    result = import_master_data(repo)
                
                # Show import statistics
                st.success(f"✅ Master data imported successfully! {result['imported']} records imported.")
                if result['duplicates'] > 0:
                    with st.expander(f"⚠️ {result['duplicates']} duplicate mobile numbers found and skipped"):
                        st.write("Duplicate Mobile Numbers:")
                        st.write(result['duplicate_numbers'])
                st.info("You can now manage master data through the Master Data Management page.")
                st.session_state.master_data_exists = True
            else:
                # st.info(f"ℹ️ Master data already exists ({record_count} records). Using existing data.")
                st.session_state.master_data_exists = True
        except FileNotFoundError:
            st.warning("⚠️ Excel file 'Verma R Master.xlsx' not found. Please add master data manually.")
        except Exception as e:
            st.error(f"⚠️ Error with master data: {e}")
            st.info("If you need to reimport, please clear the Master collection first from Master Data Management page.")

def local_css(file_name):
    with open(file_name) as f:
        st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)

# Call the function
local_css("style.css")

# Navigation - show Call Log Entry by default when setup is complete
page_options = ["Settings", "Master Data Management", "Call Log Entry", "Reports"]

# Determine default page based on setup status
if st.session_state.active_repo is not None and st.session_state.master_data_exists:
    default_index = 2  # Call Log Entry
else:
    default_index = 0  # Settings

# Create title bar with embedded navigation using HTML
st.markdown('<div class="title-bar">📞  Implementors Call Log Management System  📞</div>', unsafe_allow_html=True)

# Navigation bar right below title
page = st.radio(
    "Navigation",
    page_options,
    index=default_index,
    horizontal=True,
    label_visibility="collapsed"
)

st.divider()

# Footer
current_date = datetime.now().strftime("%B %d, %Y")
st.markdown(f"""
    <div class="footer">
        <p style="margin: 0;">Developed by <b>Indranil Chatterjee</b> | Version 1.0.0 | Date: {current_date}</p>
    </div>
""", unsafe_allow_html=True)

# Logged out screen
if st.session_state.get("logged_out") is True:
    st.title("Logged out")
    st.info("This session is closed. You can safely close this browser tab.")
    st.stop()

# Settings Page (mandatory)
if page == "Settings":
    st.title("Settings")
    st.subheader("Choose database backend (required)")

    backend = st.radio(
        "Backend Database *",
        options=["MSSQL", "MongoDB"],
        horizontal=True,
        index=None,
        help="You must select a backend before using the application.",
    )

    st.divider()

    if backend == "MSSQL":
        st.markdown("**MSSQL Connection Details**")
        col1, col2 = st.columns(2)
        with col1:
            mssql_server = st.text_input("Server *", value="")
            mssql_db = st.text_input("Database *", value="CallLogDB")
            mssql_user = st.text_input("Username *", value="sa")
        with col2:
            mssql_password = st.text_input("Password *", value="", type="password")
            mssql_driver = st.text_input("ODBC Driver", value="{ODBC Driver 17 for SQL Server}")

        mssql_settings = MSSQLSettings(
            server=mssql_server.strip(),
            database=mssql_db.strip(),
            username=mssql_user.strip(),
            password=mssql_password,
            driver=mssql_driver.strip() or "{ODBC Driver 17 for SQL Server}",
        )

        col_btn1, col_btn2 = st.columns(2)
        with col_btn1:
            if st.button("Test MSSQL Connection", type="secondary"):
                ok, msg = test_mssql_connection(mssql_settings)
                (st.success if ok else st.error)(msg)
        with col_btn2:
            if st.button("Save & Activate MSSQL", type="primary"):
                ok, msg = test_mssql_connection(mssql_settings)
                if not ok:
                    st.error(msg)
                else:
                    app_settings = AppSettings(backend="mssql", mssql=mssql_settings, mongodb=None)
                    save_settings(app_settings)  # stored into dbo.AppConfig
                    save_bootstrap(app_settings)  # local bootstrap for next startup
                    _set_active_repo("mssql")
                    st.success("Saved. MSSQL backend is now active.")
                    st.rerun()

    elif backend == "MongoDB":
        st.markdown("**MongoDB Connection Details**")
        mongo_uri = st.text_input("Mongo URI *", value="mongodb://localhost:27017")
        mongo_db = st.text_input("Mongo Database *", value="CallLogDB")

        mongo_settings = MongoSettings(uri=mongo_uri.strip(), database=mongo_db.strip())

        col_btn1, col_btn2 = st.columns(2)
        with col_btn1:
            if st.button("Test MongoDB Connection", type="secondary"):
                ok, msg = test_mongo_connection(mongo_settings)
                (st.success if ok else st.error)(msg)
        with col_btn2:
            if st.button("Save & Activate MongoDB", type="primary"):
                ok, msg = test_mongo_connection(mongo_settings)
                if not ok:
                    st.error(msg)
                else:
                    app_settings = AppSettings(backend="mongodb", mssql=None, mongodb=mongo_settings)
                    save_settings(app_settings)  # stored into appConfig collection
                    save_bootstrap(app_settings)  # local bootstrap for next startup
                    _set_active_repo("mongodb", mongo_uri=mongo_settings.uri, mongo_db=mongo_settings.database)
                    st.success("Saved. MongoDB backend is now active.")
                    st.rerun()

    st.divider()
    
    # Show current active backend status
    st.markdown("**Currently active backend:** " + (st.session_state.active_backend or "_none_"))
    
    # Logout (does NOT clear saved config)
    st.divider()
    st.subheader("Logout")
    st.markdown(
        """
        This will **log you out of the current session** and show a logout screen.
        
        Note: Streamlit runs as a server process, so “closing the application” means **closing the browser tab**.
        Your saved configuration remains, so the app can still auto-connect next time.
        """
    )

    if st.button("Logout", type="secondary", use_container_width=True):
        # Close DB connections for this repo if supported
        repo_obj = st.session_state.active_repo
        if hasattr(repo_obj, "close") and callable(getattr(repo_obj, "close")):
            try:
                repo_obj.close()
            except Exception:
                # Best-effort; ignore errors on close
                pass
        st.session_state.active_backend = None
        st.session_state.active_repo = None
        st.session_state.bootstrap_attempted = True  # avoid immediate auto-bootstrapping in same session
        st.session_state.logged_out = True
        st.rerun()

    st.stop()

# Master Data Management Page
if page == "Master Data Management":
    _ensure_repo_or_stop()
    repo = st.session_state.active_repo
    st.title("Master Data Management")
    st.subheader("CRUD Operations for Master Data")
    
    # Display success message if it exists (from previous operation)
    if 'master_success_msg' in st.session_state:
        st.success(st.session_state.master_success_msg)
        del st.session_state.master_success_msg
    
    tab1, tab2, tab3, tab4 = st.tabs(["View All", "Add New", "Update", "Delete"])
    
    with tab1:
        st.header("All Master Records")
        try:
            df = _df_from_records(repo.master_list())
            st.dataframe(df, use_container_width=True)
            st.info(f"Total records: {len(df)}")
        except Exception as e:
            st.error(f"Error loading data: {e}")
    
    with tab2:
        st.header("Add New Master Record")
        with st.form("add_master_form", width=1024):
            col1, col2 = st.columns(2)
            with col1:
                mobile_no = st.text_input("Mobile No *", key="add_mobile")
                project = st.selectbox("Project", [""] + st.session_state.dropdowns['projects'], key="add_project")
                town_type = st.selectbox("Town Type", [""] + st.session_state.dropdowns['town_types'], key="add_town_type")
                requester = st.selectbox("Requester", [""] + st.session_state.dropdowns['requesters'], key="add_requester")
                rd_code = st.text_input("RD Code", key="add_rd_code")
                rd_name = st.text_input("RD Name", key="add_rd_name")
            with col2:
                town = st.text_input("Town", key="add_town")
                state = st.text_input("State", key="add_state")
                designation = st.selectbox("Designation", [""] + st.session_state.dropdowns['designations'], key="add_designation")
                name = st.text_input("Name", key="add_name")
                gst_no = st.text_input("GST No", key="add_gst")
                email_id = st.text_input("Email ID", key="add_email")
            
            submitted = st.form_submit_button("Add Record")
            if submitted:
                if not mobile_no:
                    st.error("Mobile No is required!")
                else:
                    try:
                        inserted_id = repo.master_create(
                            {
                                "MobileNo": mobile_no,
                                "Project": project,
                                "TownType": town_type,
                                "Requester": requester,
                                "RDCode": rd_code,
                                "RDName": rd_name,
                                "Town": town,
                                "State": state,
                                "Designation": designation,
                                "Name": name,
                                "GSTNo": gst_no,
                                "EmailID": email_id,
                            }
                        )
                        if inserted_id:
                            st.session_state.master_success_msg = "✅ Master record added successfully!"
                            st.rerun()
                        else:
                            st.error("Failed to create master record - no ID returned")
                    except Exception as e:
                        st.error(f"Error adding record: {e}")
    
    with tab3:
        st.header("Update Master Record")
        try:
            all_records = repo.master_list()
            df = _df_from_records(all_records)
            if len(df) > 0:
                # Normalize selection ids to string for Mongo + MSSQL
                df["id"] = df["id"].astype(str)
                selected_id = st.selectbox(
                    "Select Record to Update",
                    df["id"].tolist(),
                    format_func=lambda x: f"{df[df['id']==x]['MobileNo'].values[0]} - {df[df['id']==x]['Name'].values[0]}", width=1024
                )
                
                current = repo.master_get(selected_id)
                if current:
                    with st.form("update_master_form", width=1024):
                        col1, col2 = st.columns(2)
                        with col1:
                            mobile_no = st.text_input("Mobile No *", value=current.get("MobileNo") or "", key="upd_mobile")
                            project = st.selectbox("Project", [""] + st.session_state.dropdowns['projects'], 
                                index=st.session_state.dropdowns['projects'].index(current.get("Project")) + 1 if current.get("Project") and current.get("Project") in st.session_state.dropdowns['projects'] else 0,
                                key="upd_project")
                            town_type = st.selectbox("Town Type", [""] + st.session_state.dropdowns['town_types'],
                                index=st.session_state.dropdowns['town_types'].index(current.get("TownType")) + 1 if current.get("TownType") and current.get("TownType") in st.session_state.dropdowns['town_types'] else 0,
                                key="upd_town_type")
                            requester = st.selectbox("Requester", [""] + st.session_state.dropdowns['requesters'],
                                index=st.session_state.dropdowns['requesters'].index(current.get("Requester")) + 1 if current.get("Requester") and current.get("Requester") in st.session_state.dropdowns['requesters'] else 0,
                                key="upd_requester")
                            rd_code = st.text_input("RD Code", value=current.get("RDCode") or "", key="upd_rd_code")
                            rd_name = st.text_input("RD Name", value=current.get("RDName") or "", key="upd_rd_name")
                        with col2:
                            town = st.text_input("Town", value=current.get("Town") or "", key="upd_town")
                            state = st.text_input("State", value=current.get("State") or "", key="upd_state")
                            designation = st.selectbox("Designation", [""] + st.session_state.dropdowns['designations'],
                                index=st.session_state.dropdowns['designations'].index(current.get("Designation")) + 1 if current.get("Designation") and current.get("Designation") in st.session_state.dropdowns['designations'] else 0,
                                key="upd_designation")
                            name = st.text_input("Name", value=current.get("Name") or "", key="upd_name")
                            gst_no = st.text_input("GST No", value=current.get("GSTNo") or "", key="upd_gst")
                            email_id = st.text_input("Email ID", value=current.get("EmailID") or "", key="upd_email")
                        
                        submitted = st.form_submit_button("Update Record", type="primary")
                        if submitted:
                            if not mobile_no:
                                st.error("Mobile No is required!")
                            else:
                                try:
                                    repo.master_update(
                                        selected_id,
                                        {
                                            "MobileNo": mobile_no,
                                            "Project": project,
                                            "TownType": town_type,
                                            "Requester": requester,
                                            "RDCode": rd_code,
                                            "RDName": rd_name,
                                            "Town": town,
                                            "State": state,
                                            "Designation": designation,
                                            "Name": name,
                                            "GSTNo": gst_no,
                                            "EmailID": email_id,
                                        },
                                    )
                                    st.session_state.master_success_msg = "✅ Master record updated successfully!"
                                    st.rerun()
                                except Exception as e:
                                    st.error(f"Error updating record: {e}")
            else:
                st.info("No records found")
        except Exception as e:
            st.error(f"Error: {e}")
    
    with tab4:
        st.header("Delete Master Record")
        try:
            df = _df_from_records(repo.master_list())
            if len(df) > 0:
                df["id"] = df["id"].astype(str)
                selected_id = st.selectbox("Select Record to Delete", 
                    df['id'].tolist(), 
                    format_func=lambda x: f"{df[df['id']==x]['MobileNo'].values[0]} - {df[df['id']==x]['Name'].values[0]}",
                    key="del_select", width=900)
                
                if st.button("Delete Record", type="primary"):
                    try:
                        repo.master_delete(selected_id)
                        st.session_state.master_success_msg = "✅ Master record deleted successfully!"
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error deleting record: {e}")
            else:
                st.info("No records found")
        except Exception as e:
            st.error(f"Error: {e}")

# Call Log Entry Page
elif page == "Call Log Entry":
    _ensure_repo_or_stop()
    repo = st.session_state.active_repo
    st.title("Call Log Entry")
    st.subheader("Enter New Call Log Entry")
    
    # Initialize session state for form values
    if 'call_form_values' not in st.session_state:
        st.session_state.call_form_values = {}
    
    mobile_no_input = st.text_input(
        "Enter Mobile No:", 
        key="mobile_input",
        width=1024,
        value=st.session_state.call_form_values.get('mobile_no', '')
    )
    

    # Wrapper for the Blue button
    # st.markdown('<div class="autofill-btn">', unsafe_allow_html=True)
    auto_fill_clicked = st.button("Fetch from Master", key="auto_fill_btn", type="primary")
    # st.markdown('</div>', unsafe_allow_html=True)
        
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
            module = st.selectbox("Module", [""] + st.session_state.dropdowns['modules'], key="call_module")
            issue = st.selectbox("Issue", [""] + st.session_state.dropdowns['issues'], key="call_issue")
            solution = st.selectbox("Solution", [""] + st.session_state.dropdowns['solutions'], key="call_solution")
            solved_on = st.selectbox("Solved On", [""] + st.session_state.dropdowns['solved_on'], key="call_solved_on")
            call_on = st.selectbox("Call On", [""] + st.session_state.dropdowns['call_on'], key="call_call_on")
            call_type = st.selectbox("Type", [""] + st.session_state.dropdowns['types'], key="call_type")
        
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

# Reports Page
elif page == "Reports":
    _ensure_repo_or_stop()
    repo = st.session_state.active_repo
    st.title("Reports")
    st.subheader("Export Call Log Data to Excel")
    try:
        # Date range filter
        col1, col2 = st.columns(2)
        with col1:
            start_date = st.date_input("Start Date", value=None, key="start_date")
        with col2:
            end_date = st.date_input("End Date", value=None, key="end_date")
        
        dr = DateRange(
            start=datetime.combine(start_date, datetime.min.time()) if start_date else None,
            end=datetime.combine(end_date, datetime.max.time()) if end_date else None,
        )
        df = _df_from_records(repo.calllog_list(dr))
        
        st.dataframe(df, use_container_width=True)
        st.info(f"Total records: {len(df)}")
        
        # Export to Excel
        if len(df) > 0:
            buffer = io.BytesIO()
            with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
                df.to_excel(writer, index=False, sheet_name='CallLogEntries')
            buffer.seek(0)
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.download_button(
                    label="📥 Download Excel File",
                    data=buffer,
                    file_name=f"CallLog_Export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )
            
            with col2:
                # Email functionality
                with st.expander("📧 Email Report"):
                    email_to = st.text_input("Recipient Email", placeholder="recipient@example.com")
                    email_subject = st.text_input("Subject", value=f"Call Log Report - {datetime.now().strftime('%Y-%m-%d')}")
                    email_body = st.text_area("Message", value="Please find the attached call log report.", height=100)
                    
                    if st.button("Send Email", type="primary"):
                        if email_to:
                            try:
                                import smtplib
                                from email.mime.multipart import MIMEMultipart
                                from email.mime.text import MIMEText
                                from email.mime.base import MIMEBase
                                from email import encoders
                                import os
                                
                                # Get email configuration from environment or settings
                                smtp_server = os.getenv("SMTP_SERVER", "smtp.gmail.com")
                                smtp_port = int(os.getenv("SMTP_PORT", "587"))
                                smtp_user = os.getenv("SMTP_USER", "")
                                smtp_password = os.getenv("SMTP_PASSWORD", "")
                                
                                if not smtp_user or not smtp_password:
                                    st.error("⚠️ Email configuration not set. Please configure SMTP_USER and SMTP_PASSWORD in .env file.")
                                else:
                                    # Create message
                                    msg = MIMEMultipart()
                                    msg['From'] = smtp_user
                                    msg['To'] = email_to
                                    msg['Subject'] = email_subject
                                    
                                    # Add body
                                    msg.attach(MIMEText(email_body, 'plain'))
                                    
                                    # Attach Excel file
                                    buffer.seek(0)
                                    filename = f"CallLog_Export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
                                    part = MIMEBase('application', 'vnd.openxmlformats-officedocument.spreadsheetml.sheet')
                                    part.set_payload(buffer.read())
                                    encoders.encode_base64(part)
                                    part.add_header('Content-Disposition', f'attachment; filename={filename}')
                                    msg.attach(part)
                                    
                                    # Send email
                                    with smtplib.SMTP(smtp_server, smtp_port) as server:
                                        server.starttls()
                                        server.login(smtp_user, smtp_password)
                                        server.send_message(msg)
                                    
                                    st.success(f"✅ Email sent successfully to {email_to}!")
                            except Exception as e:
                                st.error(f"❌ Error sending email: {e}")
                                st.info("Make sure SMTP settings are configured in your .env file.")
                        else:
                            st.warning("Please enter a recipient email address.")
        else:
            st.warning("No data to export")
            
    except Exception as e:
        st.error(f"Error loading reports: {e}")
