"""
Metadata Configuration Page Module
Handles management of dropdown values used throughout the application
"""
import streamlit as st
import pandas as pd


def get_cell_info(df: pd.DataFrame, cell):
    """
    Normalize Streamlit dataframe cell selection.
    Returns: (row_idx, col_name, cell_value) or (None, None, None)
    """
    if isinstance(cell, dict):
        row_idx = cell.get("row")
        col = cell.get("column")
    elif isinstance(cell, (list, tuple)) and len(cell) == 2:
        row_idx, col = cell
    else:
        return None, None, None

    if row_idx is None or col is None:
        return None, None, None

    try:
        # Resolve column name and value safely
        if isinstance(col, int):
            col_name = df.columns[col]
            value = df.iloc[row_idx, col]
        else:
            col_name = col
            value = df.loc[row_idx, col_name]
        return row_idx, col_name, value
    except (IndexError, KeyError):
        return None, None, None
    

def render_metadata_page(repo, dropdowns):
    # Access the username from the stored dictionary
    user_info = st.session_state.get('current_user', {})
    username = user_info.get('username', 'System')
    # Initialize a version counter to force-refresh the table when needed
    if 'table_version' not in st.session_state:
        st.session_state.table_version = 0

    # Create a dynamic key using that version
    dynamic_table_key = f"global_misc_table_{st.session_state.table_version}"

    # 1. SUCCESS MESSAGE HANDLING
    if 'misc_success_msg' in st.session_state:
        st.success(st.session_state.misc_success_msg)
        del st.session_state.misc_success_msg

    # 2. DATA INITIALIZATION & DYNAMIC KEYS
    # Fetch fresh data from DB to ensure we have all current categories
    misc_doc = repo.metadata_get() or {}
    
    # Identify fields that are arrays (the categories)
    dynamic_keys = [k for k, v in misc_doc.items() if isinstance(v, list)]
    dynamic_keys.sort()
    
    # Map for UI display: "Town Types" -> "town_types"
    display_options = {k.replace('_', ' ').title(): k for k in dynamic_keys}

    # 3. ADD NEW VALUE SECTION
    with st.form("add_value_form"):
        st.subheader("➕ Add New Value")
        col_a, col_b = st.columns(2)
        
        selected_display = col_a.selectbox("Target Category", options=list(display_options.keys()))
        new_val = col_b.text_input("New Value Name").strip()
        
        if st.form_submit_button("Add to Database", type="primary"):
            if new_val:
                db_key = display_options[selected_display]
                current_arr = misc_doc.get(db_key, [])
                
                # Case-insensitive duplicate check
                if any(val.lower() == new_val.lower() for val in current_arr):
                    st.error(f"⚠️ '{new_val}' already exists in {selected_display}!")
                else:
                    # Update local list and send to DB
                    updated_arr = sorted(current_arr + [new_val])
                    repo.metadata_update(db_key, updated_arr, username)
                    
                    # Sync global state
                    st.session_state.dropdowns[db_key] = updated_arr
                    st.session_state.misc_success_msg = f"✅ Added '{new_val}' to {selected_display}"
                    st.rerun()
            else:
                st.warning("Please enter a value.")

    st.divider()

    # 4. VIEW & MANAGE SECTION (THE GRID)
    with st.expander("📋 View & Manage All Configuration Types", expanded=True):
      if dynamic_keys:
          # 1. Prepare side-by-side table data
          max_len = max(len(misc_doc.get(k, [])) for k in dynamic_keys)
          table_data = {}
          
          for k in sorted(dynamic_keys):
              d_name = k.replace('_', ' ').title()
              vals = misc_doc.get(k, [])
              # Pad with empty strings to maintain equal column lengths
              table_data[d_name] = vals + [""] * (max_len - len(vals))
              
          df_all = pd.DataFrame(table_data)

          st.info("💡 Click cells to select them for deletion. You can select items from different columns.")

          # 2. Dataframe with multi-cell selection enabled
          selection_event = st.dataframe(
              df_all,
              use_container_width=True,
              hide_index=True,
              selection_mode="multi-cell",
              on_select="rerun",
              key=dynamic_table_key
          )

          # 3. Selection Buffer Logic (Persistence)
          if 'cells_to_delete' not in st.session_state:
              st.session_state.cells_to_delete = {}
          if 'last_seen_selection' not in st.session_state:
              st.session_state.last_seen_selection = []

          # 1. Identify what is currently selected in the UI
          current_selection = selection_event.selection.get("cells", [])
          
          # 2. Find the cell that was JUST clicked (the difference)
          # We look for the cell that is in current_selection but NOT in last_seen_selection
          newly_clicked = [c for c in current_selection if c not in st.session_state.last_seen_selection]

          # 3. If a new cell was clicked, toggle it in our permanent memory
          for cell in newly_clicked:
              row_idx, col_name, val = get_cell_info(df_all, cell)
              
              if col_name and val and str(val).strip() != "":
                  db_key = display_options.get(col_name)
                  if db_key:
                      if db_key not in st.session_state.cells_to_delete:
                          st.session_state.cells_to_delete[db_key] = set()

                      # TOGGLE: If already in our "Delete Bucket", remove it. Otherwise, add it.
                      if val in st.session_state.cells_to_delete[db_key]:
                          st.session_state.cells_to_delete[db_key].remove(val)
                      else:
                          st.session_state.cells_to_delete[db_key].add(val)   
          # 4. Update "last_seen" so we don't process the same click twice
          st.session_state.last_seen_selection = current_selection

          # 4. Delete Action UI (Horizontal Grid Layout)
          if st.session_state.cells_to_delete:
              # Filter out empty categories to get an accurate count
              active_categories = {k: v for k, v in st.session_state.cells_to_delete.items() if v}
              total_to_del = sum(len(items) for items in active_categories.values())

              if total_to_del > 0:
                  st.divider()
                  st.markdown(f"#### 🚩 Items Marked for Deletion ({total_to_del})")
                  
                  # Create a grid: 3 columns wide
                  cols = st.columns(3)
                  
                  # Enumerate through active categories to distribute them across columns
                  for idx, (db_key, items) in enumerate(active_categories.items()):
                      col_index = idx % 3  # This wraps the containers into rows of 3
                      with cols[col_index]:
                          with st.container(border=True):
                              cat_label = db_key.replace('_', ' ').title()
                              st.markdown(f"**{cat_label}**")
                              # Display items as pills
                              item_tags = " ".join([f"`{item}`" for item in items])
                              st.markdown(item_tags)

                  st.write("") # Padding
                  # Create 4 columns to push the Cancel button to the far right
                  # [Fixed width for Delete, Flexible wide spacer, Fixed width for Cancel]
                  c_del, c_spacer, c_cancel = st.columns([1.5, 5, 1.5]) 
                  
                  with c_del:
                      btn_label = f"🗑️ Confirm: Delete {total_to_del} Items"
                      if st.button(btn_label, type="primary", help="Permanently delete all selected metadata values", use_container_width=True):
                          try:
                              fresh_doc = repo.metadata_get() or {}
                              for db_key, to_remove in active_categories.items():
                                  current_list = fresh_doc.get(db_key, [])
                                  updated_list = [v for v in current_list if v not in to_remove]
                                  repo.metadata_update(db_key, sorted(updated_list), username)
                                  st.session_state.dropdowns[db_key] = sorted(updated_list)
                              
                              # Reset states and increment version
                              st.session_state.cells_to_delete = {}
                              st.session_state.last_seen_selection = []
                              st.session_state.table_version += 1
                              st.session_state.misc_success_msg = f"✅ Successfully removed {total_to_del} items."
                              st.rerun()
                          except Exception as e:
                              st.error(f"Error: {e}")

                  with c_cancel:
                      # This button is now pushed to the far right by the '5' ratio spacer
                      if st.button("Cancel / Clear", use_container_width=True):
                          st.session_state.cells_to_delete = {}
                          st.session_state.last_seen_selection = []
                          st.session_state.table_version += 1 
                          st.rerun()           
      else:
          st.info("No configuration categories found in the database.")
