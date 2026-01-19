"""
Misc Types Configuration Page Module
Handles management of dropdown values used throughout the application
"""
import streamlit as st


def render_misc_types_page(repo, dropdowns):
    """
    Render the Misc Types Configuration page.
    
    Args:
        repo: Active repository instance
        dropdowns: Dictionary of current dropdown values
    """
    st.subheader("⚙️ Manage different type values used throughout the application")
    
    # Display success message if it exists
    if 'misc_success_msg' in st.session_state:
        st.success(st.session_state.misc_success_msg)
        del st.session_state.misc_success_msg
    
    st.info("Add new values to any dropdown field below. Values are stored in the database and will appear in dropdown menus throughout the app.")
    
    # Field selection outside form for real-time preview
    st.subheader("✨ Add New Type Values")
    
    # Map display names to internal keys
    field_map = {
        "Projects": "projects",
        "Town Types": "town_types",
        "Requesters": "requesters",
        "Designations": "designations",
        "Modules": "modules",
        "Issues": "issues",
        "Solutions": "solutions",
        "Solved On": "solved_on",
        "Call On": "call_on",
        "Types": "types"
    }
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**Field Selection**")
        field_type = st.selectbox(
            "Select Field",
            ["Projects", "Town Types", "Requesters", "Designations", "Modules", 
             "Issues", "Solutions", "Solved On", "Call On", "Types"],
            key="field_type_select"
        )
    
    with col2:
        st.markdown("**Current Values**")
        selected_field_key = field_map[field_type]
        # Get fresh data from session state
        fresh_dropdowns = st.session_state.get('dropdowns', dropdowns)
        current_values = fresh_dropdowns.get(selected_field_key, [])
        
        if current_values:
            # Use unique key based on field type to force refresh
            st.text_area(
                "Existing values",
                value="\n".join(current_values),
                height=150,
                disabled=True,
                key=f"current_values_display_{selected_field_key}"
            )
        else:
            st.info("No values exist for this field yet.")
    
    # Create a form for adding new values
    with st.form("add_misc_value_form", width=1024):
        st.markdown("**New Value**")
        new_value = st.text_input(
            "Enter new value",
            key="new_value",
            help="Enter a single value to add to the selected field"
        )
        
        submitted = st.form_submit_button("Add Value", type="primary")
        
        if submitted:
            if not new_value or not new_value.strip():
                st.error("Please enter a value to add.")
            else:
                new_value = new_value.strip()
                
                # Get the field type and current values from outside the form
                selected_field_key = field_map[field_type]
                fresh_dropdowns = st.session_state.get('dropdowns', dropdowns)
                current_values = fresh_dropdowns.get(selected_field_key, [])
                
                # Check if value already exists
                if new_value in current_values:
                    st.warning(f"'{new_value}' already exists in {field_type}!")
                else:
                    try:
                        # Get current data from DB
                        current_data = repo.misc_data_get()
                        if current_data is None:
                            current_data = {
                                "projects": [],
                                "town_types": [],
                                "requesters": [],
                                "designations": [],
                                "modules": [],
                                "issues": [],
                                "solutions": [],
                                "solved_on": [],
                                "call_on": [],
                                "types": []
                            }
                        
                        # Append new value to the appropriate field
                        field_values = current_data.get(selected_field_key, [])
                        field_values.append(new_value)
                        field_values = sorted(list(set(field_values)))  # Remove duplicates and sort
                        current_data[selected_field_key] = field_values
                        
                        # Save back to DB
                        repo.misc_data_save(current_data)
                        
                        # Update session state dropdowns
                        st.session_state.dropdowns = current_data
                        
                        st.session_state.misc_success_msg = f"✅ Added '{new_value}' to {field_type}!"
                        st.rerun()
                        
                    except Exception as e:
                        st.error(f"Error saving value: {e}")
    
    st.divider()
    
    # Display all current values in an expandable section
    with st.expander("📋 View All Current Type Values", expanded=False):
        cols = st.columns(2)
        
        all_fields = [
            ("Projects", "projects"),
            ("Town Types", "town_types"),
            ("Requesters", "requesters"),
            ("Designations", "designations"),
            ("Modules", "modules"),
            ("Issues", "issues"),
            ("Solutions", "solutions"),
            ("Solved On", "solved_on"),
            ("Call On", "call_on"),
            ("Types", "types")
        ]
        
        for idx, (display_name, key) in enumerate(all_fields):
            with cols[idx % 2]:
                st.markdown(f"**{display_name}** ({len(dropdowns.get(key, []))} values)")
                values = dropdowns.get(key, [])
                if values:
                    st.text_area(
                        display_name,
                        value="\n".join(values),
                        height=100,
                        disabled=True,
                        key=f"view_{key}",
                        label_visibility="collapsed"
                    )
                else:
                    st.info("No values")
    
    st.divider()
    
    # Bulk import section
    with st.expander("📤 Bulk Import from Excel (One-time)", expanded=False):
        st.warning("⚠️ This will extract dropdown values from the Excel file and store them in the database. Use this only once when setting up the system.")
        
        uploaded_file = st.file_uploader(
            "Select Excel file to extract dropdown values",
            type=['xlsx', 'xls'],
            key="misc_import_file",
            help="Upload the Excel file with Sheet1 containing dropdown values"
        )
        
        if uploaded_file is not None:
            if st.button("Extract and Import Dropdown Values", type="primary"):
                try:
                    import pandas as pd
                    
                    with st.spinner("Extracting dropdown values from Excel..."):
                        df = pd.read_excel(uploaded_file, sheet_name='Sheet1', header=2)
                        
                        # Extract unique values for each dropdown column
                        extracted_data = {}
                        
                        extracted_data['projects'] = _extract_column_values(df, 'Unnamed: 0', 'PROJECT')
                        extracted_data['town_types'] = _extract_column_values(df, 'Unnamed: 1', 'TOWN TYPE')
                        extracted_data['requesters'] = _extract_column_values(df, 'Unnamed: 2', 'REQUSETER')
                        extracted_data['designations'] = _extract_column_values(df, 'Unnamed: 7', 'DESIGNATION')
                        extracted_data['modules'] = _extract_column_values(df, 'Unnamed: 9', 'MODULE')
                        extracted_data['issues'] = _extract_column_values(df, 'Unnamed: 10', 'ISSUE')
                        extracted_data['solutions'] = _extract_column_values(df, 'Unnamed: 11', 'SOLUTION')
                        extracted_data['solved_on'] = _extract_column_values(df, 'Unnamed: 12', 'SOLVED ON')
                        extracted_data['call_on'] = _extract_column_values(df, 'Unnamed: 13', 'CALL ON')
                        extracted_data['types'] = _extract_column_values(df, 'Unnamed: 14', 'TYPE')
                        
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
                        
                        st.session_state.misc_success_msg = "✅ Dropdown values extracted and saved successfully!"
                        st.rerun()
                        
                except Exception as e:
                    st.error(f"Error extracting dropdown values: {e}")
                    st.info("Make sure your Excel file has a 'Sheet1' with the correct format.")


def _extract_column_values(df, column_name, header_text):
    """Extract unique values from a column, excluding header text."""
    try:
        values = df[column_name].dropna().unique().tolist()
        values = [str(v).strip() for v in values if str(v).strip() and str(v).strip() != header_text]
        return sorted([v for v in values if v])
    except:
        return []
