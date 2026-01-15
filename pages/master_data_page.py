"""
Master Data Management Page Module
Handles CRUD operations for master data
"""
import streamlit as st
import pandas as pd


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
    
    tab1, tab2, tab3, tab4 = st.tabs(["View All", "Add New", "Update", "Delete"])
    
    with tab1:
        _render_view_all_tab(repo)
    
    with tab2:
        _render_add_new_tab(repo, dropdowns)
    
    with tab3:
        _render_update_tab(repo, dropdowns)
    
    with tab4:
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
        st.info(f"Total records: {len(df)}")
    except Exception as e:
        st.error(f"Error loading data: {e}")


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
