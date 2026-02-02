"""
Master Data Management Page Module
Handles CRUD operations for master data
"""
import streamlit as st
import pandas as pd
from datetime import datetime
from dataclasses import asdict
from utils import get_logged_in_user, df_from_records, get_now
from utils.data_models import MasterRecord, MetadataConfig

INDIAN_STATES = [
    "ANDHRA PRADESH", "ARUNACHAL PRADESH", "ASSAM", "BIHAR", "CHHATTISGARH", 
    "GOA", "GUJARAT", "HARYANA", "HIMACHAL PRADESH", "JHARKHAND", "KARNATAKA", 
    "KERALA", "MADHYA PRADESH", "MAHARASHTRA", "MANIPUR", "MEGHALAYA", "MIZORAM", 
    "NAGALAND", "ODISHA", "PUNJAB", "RAJASTHAN", "SIKKIM", "TAMIL NADU", 
    "TELANGANA", "TRIPURA", "UTTAR PRADESH", "UTTARAKHAND", "WEST BENGAL", 
    "ANDAMAN AND NICOBAR ISLANDS", "CHANDIGARH", "DADRA AND NAGAR HAVELI AND DAMAN AND DIU", 
    "DELHI", "JAMMU AND KASHMIR", "LADAKH", "LAKSHADWEEP", "PUDUCHERRY"
]

def render_master_data_page(repo, dropdowns):
    """
    Render the Master Data Management page.
    
    Args:
        repo: Active repository instance
        dropdowns: Dictionary of dropdown values
    """
    st.subheader("📂 Masters Management")
    # Access the username from the stored dictionar
    username = get_logged_in_user()
    
    # Display success message if it exists (from previous operation)
    if 'master_success_msg' in st.session_state:
        st.success(st.session_state.master_success_msg)
        del st.session_state.master_success_msg
    
    # Display duplicate info if it exists
    if 'duplicate_info' in st.session_state:
        dup_info = st.session_state.duplicate_info
        with st.expander(f"⚠️ {dup_info['count']} duplicate mobile numbers found and skipped"):
            st.write("Duplicate Mobile Numbers:")
            st.write(dup_info['numbers'])
        del st.session_state.duplicate_info
    
    # Initialize active tab in session state if not present
    if 'master_active_tab' not in st.session_state:
        st.session_state.master_active_tab = "View All"
    
    # Tab selection using radio buttons (persists across reruns)
    tab_selection = st.radio(
        "Select Operation",
        ["View All", "Add New", "Update", "Delete"],
        index=["View All", "Add New", "Update", "Delete"].index(st.session_state.master_active_tab),
        horizontal=True,
        label_visibility="hidden",
        key="master_tab_selector"
    )
    
    # Update session state
    st.session_state.master_active_tab = tab_selection
    st.markdown("<hr style='margin: 5px 0px; opacity: 0.5;'>", unsafe_allow_html=True)
    
    # Render the selected tab
    if tab_selection == "View All":
        _render_view_all_tab(repo, username)
    elif tab_selection == "Add New":
        _render_add_new_tab(repo, dropdowns, username)
    elif tab_selection == "Update":
        _render_update_tab(repo, dropdowns, username)
    elif tab_selection == "Delete":
        _render_delete_tab(repo, username)


def _render_view_all_tab(repo, username):
    """Render view all records tab with aligned pagination."""
    st.subheader("📋 All Master Records")
    try:
        records = repo.master_list()
        df = df_from_records(records, is_master=True)
        
        if len(df) == 0:
            st.info("Total records: 0")
            st.divider()
            _handle_excel_import(repo, username)
            return

        # Pagination Logic
        rows_per_page = 25
        total_pages = (len(df) - 1) // rows_per_page + 1
        
        if 'master_page_num' not in st.session_state:
            st.session_state.master_page_num = 1

        start_idx = (st.session_state.master_page_num - 1) * rows_per_page
        end_idx = start_idx + rows_per_page

        # 1. Display Dataframe
        st.dataframe(df.iloc[start_idx:end_idx], use_container_width=True, hide_index=True)
        
        # 2. Record Count Indicator
        st.info(f"Showing {start_idx + 1} to {min(end_idx, len(df))} of {len(df)} records")
        
        # 3. Aligned Pagination Controls
        # We use a 5-column layout to center the "Page X of Y" text perfectly
        col1, col2, col3, col4, col5 = st.columns([1.4, 1.5, 2, 1, 1.5])
        
        with col2:
            if st.button("<< Previous", use_container_width=True):
                if st.session_state.master_page_num > 1:
                    st.session_state.master_page_num -= 1
                    st.rerun()

        with col3:
            # Centering the text inside the middle column
            st.markdown(
                f"<h3 style='text-align: center; font-size: 16px; margin-top: 5px;'>"
                f"Page {st.session_state.master_page_num} of {total_pages}"
                f"</h3>", 
                unsafe_allow_html=True
            )

        with col4:
            if st.button("Next >>", use_container_width=True):
                if st.session_state.master_page_num < total_pages:
                    st.session_state.master_page_num += 1
                    st.rerun()
               
    except Exception as e:
        st.error(f"Error loading data: {e}")


def _handle_excel_import(repo, username):
    """
    Handle Excel file import using MasterRecord and MetadataConfig dataclasses.
    Ensures data integrity and automatic timestamping.
    """
    uploaded_file = st.file_uploader(
        "Select Excel file to import", 
        type=['xlsx', 'xls'],
        key="master_import_file",
        help="Upload an Excel file with 'Master' sheet and 'Sheet1' for dropdown values"
    )
    
    if uploaded_file is not None:
        if st.button("Start Import", type="primary"):
            try:
                import pandas as pd
                
                with st.status("🚀 Processing Import...", expanded=True) as status:
                    # ==========================================
                    # 1. PROCESS MASTER DATA SHEET
                    # ==========================================
                    st.write("📖 Reading 'Master' sheet...")
                    df_master = pd.read_excel(uploaded_file, sheet_name='Master', header=1)
                    
                    # Align Excel columns to our logic
                    df_master.columns = [
                        'SrNo', 'MobileNo', 'Project', 'TownType', 'Requester', 'RDCode', 
                        'RDName', 'Town', 'State', 'Designation', 'Name', 'GSTNo', 'EmailID'
                    ]
                    
                    # Clean and De-duplicate
                    df_master = df_master[df_master['MobileNo'].notna()]
                    df_master = df_master[df_master['MobileNo'] != 'Mobile No']
                    df_master['MobileNo'] = df_master['MobileNo'].astype(str).str.strip()
                    
                    initial_count = len(df_master)
                    duplicate_mask = df_master.duplicated(subset=['MobileNo'], keep='first')
                    duplicate_numbers = df_master[duplicate_mask]['MobileNo'].tolist()
                    df_master = df_master.drop_duplicates(subset=['MobileNo'], keep='first')
                    
                    st.write(f"📦 Creating {len(df_master)} MasterRecord objects...")
                    master_records = []
                    for _, row in df_master.iterrows():
                        # Instantiate MasterRecord Dataclass
                        record = MasterRecord(
                            mobile=str(row["MobileNo"]),
                            project=str(row["Project"]) if pd.notna(row["Project"]) else None,
                            town_type=str(row["TownType"]) if pd.notna(row["TownType"]) else None,
                            requester=str(row["Requester"]) if pd.notna(row["Requester"]) else None,
                            rd_code=str(row["RDCode"]) if pd.notna(row["RDCode"]) else None,
                            rd_name=str(row["RDName"]) if pd.notna(row["RDName"]) else None,
                            town=str(row["Town"]) if pd.notna(row["Town"]) else None,
                            state=str(row["State"]) if pd.notna(row["State"]) else None,
                            designation=str(row["Designation"]) if pd.notna(row["Designation"]) else None,
                            name=str(row["Name"]) if pd.notna(row["Name"]) else None,
                            gst_no=str(row["GSTNo"]) if pd.notna(row["GSTNo"]) else None,
                            email_id=str(row["EmailID"]) if pd.notna(row["EmailID"]) else None,
                            created_by=username,
                            created_at=get_now()
                        )
                        master_records.append(record)

                    # Save Master Records
                    inserted_count = repo.master_replace_all(master_records)

                    # ==========================================
                    # 2. PROCESS DROPDOWN (METADATA) SHEET
                    # ==========================================
                    st.write("📋 Extracting dropdown values from 'Sheet1'...")
                    dropdown_imported = False
                    try:
                        df_drop = pd.read_excel(uploaded_file, sheet_name='Sheet1', header=2)
                        
                        # Extract unique values using helper
                        new_metadata_map = {
                            'projects': _extract_column_values(df_drop, 'Unnamed: 0', 'PROJECT'),
                            'town_types': _extract_column_values(df_drop, 'Unnamed: 1', 'TOWN TYPE'),
                            'requesters': _extract_column_values(df_drop, 'Unnamed: 2', 'REQUSETER'),
                            'designations': _extract_column_values(df_drop, 'Unnamed: 7', 'DESIGNATION'),
                            'modules': _extract_column_values(df_drop, 'Unnamed: 9', 'MODULE'),
                            'issues': _extract_column_values(df_drop, 'Unnamed: 10', 'ISSUE'),
                            'solutions': _extract_column_values(df_drop, 'Unnamed: 11', 'SOLUTION'),
                            'solved_on': _extract_column_values(df_drop, 'Unnamed: 12', 'SOLVED ON'),
                            'call_on': _extract_column_values(df_drop, 'Unnamed: 13', 'CALL ON'),
                            'types': _extract_column_values(df_drop, 'Unnamed: 14', 'TYPE')
                        }
                        
                        # Merge with existing DB data
                        current_db_data = repo.metadata_get() or {}
                        merged_data = {}
                        for key, new_vals in new_metadata_map.items():
                            existing_vals = current_db_data.get(key, [])
                            # Union of lists + Sort
                            merged_data[key] = sorted(list(set(existing_vals + new_vals)))
                        
                        # Use MetadataConfig Dataclass to structure and timestamp
                        merged_data['created_by'] = username
                        merged_data['created_at'] = get_now()
                        meta_config = MetadataConfig(**merged_data)
                        
                        # Save to Database
                        repo.metadata_save(meta_config.to_dict())
                        
                        # Update Session State so UI refreshes immediately
                        st.session_state.dropdowns = meta_config.to_dict()
                        dropdown_imported = True
                    except Exception as meta_e:
                        st.warning(f"⚠️ Metadata import skipped: {meta_e}")

                    # ==========================================
                    # 3. FINALIZATION
                    # ==========================================
                    success_msg = f"✅ Success! {inserted_count} master records imported."
                    if dropdown_imported:
                        success_msg += " Dropdown values updated."
                    
                    status.update(label="Import Complete!", state="complete", expanded=False)
                
                # Store results for the next render
                st.session_state.master_success_msg = success_msg
                if initial_count - inserted_count > 0:
                    st.session_state.duplicate_info = {
                        'count': initial_count - inserted_count,
                        'numbers': duplicate_numbers
                    }
                st.rerun()
                    
            except Exception as e:
                st.error(f"❌ Critical Error: {e}")
                st.info("Check if Excel sheet names ('Master', 'Sheet1') are correct.")


def _render_add_new_tab(repo, dropdowns, username): 
    """Render add new record tab using MasterRecord dataclass."""
    st.subheader("➕ Add New Master Record")
    with st.form("add_master_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            mobile = st.text_input("Mobile No *", key="add_mobile")
            project = st.selectbox("Project", [""] + dropdowns['projects'], key="add_project")
            town_type = st.selectbox("Town Type", [""] + dropdowns['town_types'], key="add_town_type")
            requester = st.selectbox("Requester", [""] + dropdowns['requesters'], key="add_requester")
            rd_code = st.text_input("RD Code", key="add_rd_code")
            rd_name = st.text_input("RD Name", key="add_rd_name")
        with col2:
            town = st.text_input("Town", key="add_town")
            state = st.selectbox("State", [""] + INDIAN_STATES, key="add_state")
            designation = st.selectbox("Designation", [""] + dropdowns['designations'], key="add_designation")
            name = st.text_input("Name", key="add_name")
            gst_no = st.text_input("GST No", key="add_gst")
            email_id = st.text_input("Email ID", key="add_email")
        
        if st.form_submit_button("Add Record", type="primary"):
            if not mobile:
                st.error("Mobile No is required!")
            else:
                try:
                    # Initialize Dataclass (it handles created_at/updated_at automatically)
                    new_record = MasterRecord(
                        mobile=mobile, project=project, town_type=town_type,
                        requester=requester, rd_code=rd_code, rd_name=rd_name,
                        town=town, state=state, designation=designation,
                        name=name, gst_no=gst_no, email_id=email_id, created_by=username,
                        created_at=get_now()
                        
                    )
                    
                    inserted_id = repo.master_create(new_record)
                    
                    if inserted_id:
                        st.session_state.master_success_msg = "✅ Master record added successfully!"
                        st.rerun()
                except Exception as e:
                    st.error(f"Error adding record: {e}")


def _render_update_tab(repo, dropdowns, username):
    """
    Render update record tab using MasterRecord dataclass.
    Ensures data integrity by wrapping database results in objects.
    """
    st.subheader("🔄 Update Master Record")
    
    # Versioning for the selectbox to force-refresh after a successful update
    if "update_version" not in st.session_state:
        st.session_state.update_version = 0

    dynamic_key = f"update_select_{st.session_state.update_version}"
    
    try:
        # 1. Fetch records and prepare for selection
        all_records = repo.master_list()
        df = df_from_records(all_records, keep_uid=True, is_master=True)
        
        if len(df) > 0:
            df["uid"] = df["uid"].astype(str)
            
            # Use lowercase keys 'mobile' and 'name' from the MasterRecord dataclass
            selected_id = st.selectbox(
                "Select Record to Update",
                df["uid"].tolist(),
                format_func=lambda x: f"{df[df['uid']==x]['mobile'].values[0]} - {df[df['uid']==x]['name'].values[0]}", 
                index=None,
                placeholder="Choose a record...",
                key=dynamic_key,
                width=1024
            )
            
            if selected_id:
                # 2. Get current record data
                current = repo.master_get(selected_id)
                
                # Hybrid Logic for State: Handle values not in the standard INDIAN_STATES list
                current_db_state = str(current.state or "").strip()
                if current_db_state and current_db_state not in INDIAN_STATES:
                    state_options = [current_db_state] + INDIAN_STATES
                else:
                    state_options = [""] + INDIAN_STATES

                try:
                    state_index = state_options.index(current_db_state)
                except ValueError:
                    state_index = 0

                # 3. Render the Update Form
                with st.form("update_master_form", width=1024):
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        upd_mobile = st.text_input("Mobile No *", value=current.mobile or "", key="upd_mobile")
                        
                        upd_project = st.selectbox("Project", [""] + dropdowns['projects'], 
                            index=dropdowns['projects'].index(current.project) + 1 if current.project in dropdowns['projects'] else 0)
                        
                        upd_town_type = st.selectbox("Town Type", [""] + dropdowns['town_types'],
                            index=dropdowns['town_types'].index(current.town_type) + 1 if current.town_type in dropdowns['town_types'] else 0)

                        upd_requester = st.selectbox("Requester", [""] + dropdowns['requesters'],
                            index=dropdowns['requesters'].index(current.requester) + 1 if current.requester in dropdowns['requesters'] else 0)
                        
                        upd_rd_code = st.text_input("RD Code", value=current.rd_code or "")
                        upd_rd_name = st.text_input("RD Name", value=current.rd_name or "")

                    with col2:
                        upd_town = st.text_input("Town", value=current.town or "")
                        
                        upd_state = st.selectbox("State", options=state_options, index=state_index, 
                                               help="Search for a standardized state name.")
                        
                        upd_designation = st.selectbox("Designation", [""] + dropdowns['designations'],
                            index=dropdowns['designations'].index(current.designation) + 1 if current.designation in dropdowns['designations'] else 0)

                        upd_name = st.text_input("Name", value=current.name or "")
                        upd_gst = st.text_input("GST No", value=current.gst_no or "")
                        upd_email = st.text_input("Email ID", value=current.email_id or "")

                    # 4. Handle Form Submission
                    if st.form_submit_button("Update Record", type="primary"):
                        if not upd_mobile:
                            st.error("Mobile No is required!")
                        else:
                            try:
                                # Create updated MasterRecord instance
                                # We preserve the original created_at timestamp
                                updated_record = MasterRecord(
                                    mobile=upd_mobile,
                                    project=upd_project,
                                    town_type=upd_town_type,
                                    requester=upd_requester,
                                    rd_code=upd_rd_code,
                                    rd_name=upd_rd_name,
                                    town=upd_town,
                                    state=upd_state,
                                    designation=upd_designation,
                                    name=upd_name,
                                    gst_no=upd_gst,
                                    email_id=upd_email,
                                    updated_by=username,
                                    updated_at=get_now()  # Refresh the updated_at timestamp
                                )

                                # Update DB via repository
                                result = repo.master_update(selected_id, updated_record)
                                if result:
                                    st.session_state.master_success_msg = f"✅ Master record [ Rd Name: {upd_rd_name}, Mobile: {upd_mobile} ] updated successfully!"
                                    st.session_state.update_version += 1  # Forces selectbox to reset
                                    st.rerun()
                                else:
                                    st.error(f"Failed to update record for UID: {selected_id}.")
                            except Exception as e:
                                st.error(f"Error updating record: {e}")
            else:
                st.info("Please select a record from the dropdown to begin editing.")
        else:
            st.info("No master records found in the database.")
            
    except Exception as e:
        st.error(f"An unexpected error occurred: {e}")


def _render_delete_tab(repo, username):
    """
    Render delete record tab.
    Uses dataclass-aligned field names (mobile, name).
    """
    st.subheader("❌ Delete Master Record")
    
    try:
        # 1. Fetch current master list
        all_records = repo.master_list()
        df = df_from_records(all_records, keep_uid=True, is_master=True)
        
        if len(df) > 0:
            # Ensure UID is a string for consistent matching
            df["uid"] = df["uid"].astype(str)
            
            # Use lowercase keys 'mobile' and 'name' to match the MasterRecord dataclass
            selected_id = st.selectbox(
                "Select Record to Delete", 
                options=df['uid'].tolist(), 
                format_func=lambda x: f"{df[df['uid']==x]['mobile'].values[0]} - {df[df['uid']==x]['name'].values[0]}",
                index=None,
                placeholder="Choose a record to remove...",
                key="del_select", 
                help="Search by mobile number or name."
            )
            
            if selected_id:
                # Get the specific record info for the confirmation message
                record_info = df[df['uid'] == selected_id].iloc[0]
                
                st.warning(f"⚠️ Are you sure you want to delete the record for **{record_info['name']}** ({record_info['mobile']})? This action cannot be undone.")
                
                if st.button("Confirm Delete", type="primary"):
                    try:
                        # Perform deletion in DB
                        repo.master_delete(selected_id)
                        
                        # Store success message and refresh
                        st.session_state.master_success_msg = f"✅ Master record for {record_info['name']} deleted successfully!"
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error deleting record: {e}")
            else:
                st.info("Please select a record from the list to enable the delete option.")
        else:
            st.info("No master records found. The database is currently empty.")
            
    except Exception as e:
        st.error(f"Error loading records for deletion: {e}")


def _extract_column_values(df, column_name, header_text):
    """Extract unique values from a column, excluding header text."""
    try:
        values = df[column_name].dropna().unique().tolist()
        values = [str(v).strip() for v in values if str(v).strip() and str(v).strip() != header_text]
        return sorted([v for v in values if v])
    except:
        return []
