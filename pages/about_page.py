import streamlit as st
from datetime import datetime

def render_about_page():
    st.subheader("ℹ️ About Call Log Management System")
    
    # Section 1: How it works
    with st.expander("🚀 How this Application Works", expanded=True):
        st.markdown("""
        This application is designed to streamline the call logging process by integrating master data.
        * **Step 1: Database Setup** – Configure your MongoDB or MSSQL backend in Settings.
        * **Step 2: Master Data** – Import or add your customer/client master records.
        * **Step 3: Auto-Fill Logging** – Use the 'Call Log Entry' page. Enter a mobile number to instantly fetch details from the Master database.
        * **Step 4: Reporting** – Filter logs by date range and export them for analysis.
        """)

    # Section 2: Excel Export Info
    with st.expander("📊 Excel Export & Field Information"):
        st.info("💡 Tip: Use the 'Reports' page to generate custom Excel files.")
        st.markdown("""
        ### Exported Fields
        The exported Excel file includes the following data points:
        - **Identification**: Date, Mobile No, Name, and Designation.
        - **Location Details**: Project, Town, RD Code, RD Name, and State.
        - **Log Details**: Module, Issue, Solution, and Call Type.
        - **Resolution**: Status of the issue and the channel used (Call/Email/WhatsApp).
        
        *All exports are compatible with Microsoft Excel (.xlsx) and include automatic timestamps in the filename.*
        """)

    # Section 3: Development Info
    st.divider()
    col1, col2 = st.columns([1, 1])
    with col1:
        st.markdown("### 👨‍💻 Developed By")
        st.write("**Indranil Chatterjee**")
        st.caption("Version 1.0.0 | Release: January 2026")
    
    with col2:
        st.markdown("### 🛠️ Technology Stack")
        st.markdown("`Streamlit` `Python` `MongoDB` `MSSQL` `Pandas`")

    # Add a small copyright footer
    current_year = datetime.now().year
    st.markdown(
        f"<div style='text-align: center; color: gray; margin-top: 50px;'>"
        f"© {current_year} Call Log Management System | All Rights Reserved.</div>", 
        unsafe_allow_html=True
    )