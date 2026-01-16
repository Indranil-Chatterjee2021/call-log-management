"""
Master Data Management Page Module
Handles CRUD operations for master data
"""
import streamlit as st
import pandas as pd
from datetime import datetime

def render_master_data_page(repo, dropdowns):
    """
    Render the Master Data Management page.
    
    Args:
        repo: Active repository instance
        dropdowns: Dictionary of dropdown values
    """
    st.title("Master Data Management")
    st.subheader("CRUD Operations for Master Data")
    
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
        key="master_tab_selector"
    )
    
    # Update session state
    st.session_state.master_active_tab = tab_selection
    
    st.divider()
    
    # Render the selected tab
    if tab_selection == "View All":
        _render_view_all_tab(repo)
    elif tab_selection == "Add New":
        _render_add_new_tab(repo, dropdowns)
    elif tab_selection == "Update":
        _render_update_tab(repo, dropdowns)
    elif tab_selection == "Delete":
        _render_delete_tab(repo)


def _df_from_records(records: list[dict], keep_id: bool = False) -> pd.DataFrame:
    """Convert records to DataFrame and optionally remove id column."""
    if not records:
        return pd.DataFrame()
    df = pd.DataFrame.from_records(records)
    # Remove id column if present and not explicitly kept
    if not keep_id and 'id' in df.columns:
        df = df.drop(columns=['id'])
    return df


def _render_view_all_tab(repo):
    """Render view all records tab."""
    st.header("All Master Records")
    try:
        df = _df_from_records(repo.master_list())
        st.dataframe(df, use_container_width=True)
        
        # Display total records and import section
        col1, col2 = st.columns([3, 1])
        with col1:
            st.info(f"Total records: {len(df)}")
        
        # Import section - show only if no data exists
        if len(df) == 0:
            st.divider()
            st.subheader("📥 Import Master Data from Excel")
            _handle_excel_import(repo)
        else:
            with col2:
                st.button("📥 Import from Excel", disabled=True, help="Import disabled - data already exists. Delete existing data to re-import.")
                
    except Exception as e:
        st.error(f"Error loading data: {e}")


def _handle_excel_import(repo):
    """Handle Excel file import with file uploader."""
    uploaded_file = st.file_uploader(
        "Select Excel file to import", 
        type=['xlsx', 'xls'],
        key="master_import_file",
        help="Upload an Excel file with 'Master' sheet for master data and 'Sheet1' for dropdown values"
    )
    
    if uploaded_file is not None:
        if st.button("Start Import", type="primary"):
            try:
                import pandas as pd
                from datetime import datetime
                
                with st.status("Importing data from Excel file...", expanded=True) as status:
                    st.write("📖 Reading Master sheet...")
                    # ===== Import Master Data =====
                    df = pd.read_excel(uploaded_file, sheet_name='Master', header=1)
                    
                    # Clean column names
                    df.columns = ['SrNo', 'MobileNo', 'Project', 'TownType', 'Requester', 'RDCode', 
                                  'RDName', 'Town', 'State', 'Designation', 'Name', 'GSTNo', 'EmailID']
                    
                    # Remove rows where MobileNo is NaN or header row
                    df = df[df['MobileNo'].notna()]
                    df = df[df['MobileNo'] != 'Mobile No']
                    
                    # Convert MobileNo to string
                    df['MobileNo'] = df['MobileNo'].astype(str).str.strip()
                    
                    # Remove duplicates - keep first occurrence of each mobile number
                    initial_count = len(df)
                    duplicate_mask = df.duplicated(subset=['MobileNo'], keep='first')
                    duplicate_numbers = df[duplicate_mask]['MobileNo'].tolist()
                    
                    df = df.drop_duplicates(subset=['MobileNo'], keep='first')
                    duplicates_removed = initial_count - len(df)

                    st.write(f"💾 Preparing {len(df)} records for import...")
                    records = []
                    for _, row in df.iterrows():
                        records.append({
                            "MobileNo": str(row["MobileNo"]),
                            "Project": str(row["Project"]) if pd.notna(row["Project"]) else None,
                            "TownType": str(row["TownType"]) if pd.notna(row["TownType"]) else None,
                            "Requester": str(row["Requester"]) if pd.notna(row["Requester"]) else None,
                            "RDCode": str(row["RDCode"]) if pd.notna(row["RDCode"]) else None,
                            "RDName": str(row["RDName"]) if pd.notna(row["RDName"]) else None,
                            "Town": str(row["Town"]) if pd.notna(row["Town"]) else None,
                            "State": str(row["State"]) if pd.notna(row["State"]) else None,
                            "Designation": str(row["Designation"]) if pd.notna(row["Designation"]) else None,
                            "Name": str(row["Name"]) if pd.notna(row["Name"]) else None,
                            "GSTNo": str(row["GSTNo"]) if pd.notna(row["GSTNo"]) else None,
                            "EmailID": str(row["EmailID"]) if pd.notna(row["EmailID"]) else None,
                        })

                    st.write("✍️ Writing records to database...")
                    inserted = repo.master_replace_all(records)
                    
                    # ===== Import Dropdown Values automatically =====
                    st.write("📋 Importing dropdown values from Sheet1...")
                    dropdown_imported = False
                    try:
                        df_dropdown = pd.read_excel(uploaded_file, sheet_name='Sheet1', header=2)
                        
                        # Extract unique values for each dropdown column
                        extracted_data = {
                            'projects': _extract_column_values(df_dropdown, 'Unnamed: 0', 'PROJECT'),
                            'town_types': _extract_column_values(df_dropdown, 'Unnamed: 1', 'TOWN TYPE'),
                            'requesters': _extract_column_values(df_dropdown, 'Unnamed: 2', 'REQUSETER'),
                            'designations': _extract_column_values(df_dropdown, 'Unnamed: 7', 'DESIGNATION'),
                            'modules': _extract_column_values(df_dropdown, 'Unnamed: 9', 'MODULE'),
                            'issues': _extract_column_values(df_dropdown, 'Unnamed: 10', 'ISSUE'),
                            'solutions': _extract_column_values(df_dropdown, 'Unnamed: 11', 'SOLUTION'),
                            'solved_on': _extract_column_values(df_dropdown, 'Unnamed: 12', 'SOLVED ON'),
                            'call_on': _extract_column_values(df_dropdown, 'Unnamed: 13', 'CALL ON'),
                            'types': _extract_column_values(df_dropdown, 'Unnamed: 14', 'TYPE')
                        }
                        
                        # Get existing data and merge
                        current_data = repo.misc_data_get()
                        if current_data:
                            # Merge with existing data
                            for key in extracted_data:
                                existing_values = current_data.get(key, [])
                                new_values = extracted_data[key]
                                merged = sorted(list(set(existing_values + new_values)))
                                extracted_data[key] = merged
                        
                        # Save to database
                        repo.misc_data_save(extracted_data)
                        
                        # Update session state
                        st.session_state.dropdowns = extracted_data
                        dropdown_imported = True
                    except Exception as e:
                        st.warning(f"⚠️ Could not import dropdown values from Sheet1: {e}")
                    
                    # Prepare success message before completing status
                    success_msg = f"✅ Master data imported successfully! {inserted} records imported."
                    if dropdown_imported:
                        success_msg += " Dropdown values also imported!"
                    
                    # Mark as complete
                    status.update(label="Import completed!", state="complete", expanded=False)
                
                # Store message and rerun immediately (show message on next render)
                st.session_state.master_success_msg = success_msg
                st.session_state.master_data_exists = True
                if duplicates_removed > 0:
                    st.session_state.duplicate_info = {
                        'count': duplicates_removed,
                        'numbers': duplicate_numbers
                    }
                st.rerun()
                    
            except Exception as e:
                st.error(f"Error importing data: {e}")
                st.info("Make sure your Excel file has a 'Master' sheet with the correct format.")


def _render_add_new_tab(repo, dropdowns):
    """Render add new record tab."""
    st.header("Add New Master Record")
    with st.form("add_master_form", width=1024):
        col1, col2 = st.columns(2)
        with col1:
            mobile_no = st.text_input("Mobile No *", key="add_mobile")
            project = st.selectbox("Project", [""] + dropdowns['projects'], key="add_project")
            town_type = st.selectbox("Town Type", [""] + dropdowns['town_types'], key="add_town_type")
            requester = st.selectbox("Requester", [""] + dropdowns['requesters'], key="add_requester")
            rd_code = st.text_input("RD Code", key="add_rd_code")
            rd_name = st.text_input("RD Name", key="add_rd_name")
        with col2:
            town = st.text_input("Town", key="add_town")
            state = st.text_input("State", key="add_state")
            designation = st.selectbox("Designation", [""] + dropdowns['designations'], key="add_designation")
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


def _render_update_tab(repo, dropdowns):
    """Render update record tab."""
    st.header("Update Master Record")
    try:
        all_records = repo.master_list()
        df = _df_from_records(all_records, keep_id=True)
        if len(df) > 0:
            # Normalize selection ids to string for Mongo + MSSQL
            df["id"] = df["id"].astype(str)
            selected_id = st.selectbox(
                "Select Record to Update",
                df["id"].tolist(),
                format_func=lambda x: f"{df[df['id']==x]['MobileNo'].values[0]} - {df[df['id']==x]['Name'].values[0]}", 
                index=None,
                placeholder="Choose a record...",
                width=1024
            )
            
            if selected_id:
                current = repo.master_get(selected_id)
                with st.form("update_master_form", width=1024):
                    col1, col2 = st.columns(2)
                    with col1:
                        mobile_no = st.text_input("Mobile No *", value=current.get("MobileNo") or "", key="upd_mobile")
                        project = st.selectbox("Project", [""] + dropdowns['projects'], 
                            index=dropdowns['projects'].index(current.get("Project")) + 1 if current.get("Project") and current.get("Project") in dropdowns['projects'] else 0,
                            key="upd_project")
                        town_type = st.selectbox("Town Type", [""] + dropdowns['town_types'],
                            index=dropdowns['town_types'].index(current.get("TownType")) + 1 if current.get("TownType") and current.get("TownType") in dropdowns['town_types'] else 0,
                            key="upd_town_type")
                        requester = st.selectbox("Requester", [""] + dropdowns['requesters'],
                            index=dropdowns['requesters'].index(current.get("Requester")) + 1 if current.get("Requester") and current.get("Requester") in dropdowns['requesters'] else 0,
                            key="upd_requester")
                        rd_code = st.text_input("RD Code", value=current.get("RDCode") or "", key="upd_rd_code")
                        rd_name = st.text_input("RD Name", value=current.get("RDName") or "", key="upd_rd_name")
                    with col2:
                        town = st.text_input("Town", value=current.get("Town") or "", key="upd_town")
                        state = st.text_input("State", value=current.get("State") or "", key="upd_state")
                        designation = st.selectbox("Designation", [""] + dropdowns['designations'],
                            index=dropdowns['designations'].index(current.get("Designation")) + 1 if current.get("Designation") and current.get("Designation") in dropdowns['designations'] else 0,
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
                st.info("Please select a record to update")
        else:
            st.info("No records found")
    except Exception as e:
        st.error(f"Error: {e}")


def _render_delete_tab(repo):
    """Render delete record tab."""
    st.header("Delete Master Record")
    try:
        df = _df_from_records(repo.master_list(), keep_id=True)
        if len(df) > 0:
            df["id"] = df["id"].astype(str)
            selected_id = st.selectbox("Select Record to Delete", 
                df['id'].tolist(), 
                format_func=lambda x: f"{df[df['id']==x]['MobileNo'].values[0]} - {df[df['id']==x]['Name'].values[0]}",
                index=None,
                placeholder="Choose a record...",
                key="del_select", width=900)
            
            if selected_id and st.button("Delete Record", type="primary"):
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


def _extract_column_values(df, column_name, header_text):
    """Extract unique values from a column, excluding header text."""
    try:
        values = df[column_name].dropna().unique().tolist()
        values = [str(v).strip() for v in values if str(v).strip() and str(v).strip() != header_text]
        return sorted([v for v in values if v])
    except:
        return []
