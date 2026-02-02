import streamlit as st
from datetime import datetime

def render_about_page():
    st.subheader("ℹ️ About Call Log Management System")
    
    # Section 1: How it works
    with st.expander("🚀 How this Application Works", expanded=True):
        st.markdown("""
        This application is designed to streamline the call logging process by integrating master data.
        * **Step 1: Database Setup** – Configure your MongoDB backend in Settings.
        * **Step 2: Email** – Configure SMTP in Settings → Email. You can send generated reports directly from the Reports page after saving SMTP details.
        * **Step 3: Master Data** – Import or add your customer/client master records.
        * **Step 4: Types (Dropdowns)** – Use the "Types" / Dropdowns page to manage Projects, Modules, Issues, Solutions, Solved On, Call On and Type values; these drive the dropdowns throughout the app.
        * **Step 5: Auto-Fill Logging** – Use the 'Call Log Entry' page. Enter a mobile number to instantly fetch details from the Master database.
        * **Step 6: Reporting** – Filter logs by date range and export them for analysis.
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

    # Section 3: Gmail Setup Guide
    with st.expander("📧 Step-by-Step: Gmail SMTP & App Password"):
        st.markdown("### 1️⃣ Generate a Google App Password")
        st.write("Since Google no longer allows 'Less Secure Apps', you must use an App Password.")
        st.markdown("""
        1. Go to your [Google Account Security Settings](https://myaccount.google.com/security).
        2. Enable **2-Step Verification** (required for App Passwords).
        3. Search for **'App passwords'** in the top search bar.
        4. In 'App name', type **'Call Log System'** and click **Create**.
        5. **Copy the 16-character code** (the yellow box). You won't see it again!
        """)
        
        st.markdown("### 2️⃣ Fill the Configuration Page")
        st.markdown(f"""
        Navigate to **Settings → Email** and enter:
        - **SMTP Server**: `smtp.gmail.com`
        - **SMTP Port**: `587`
        - **Email Address**: Your full Gmail (e.g., `abcdefgk@gmail.com`)
        - **Email Password**: Paste the **16-character App Password** (no spaces).
        """)
        st.info("💡 Always click 'Test Connection' before saving to ensure your credentials are valid.")    

    # Section 3: Development Info
    st.divider()
    col1, col2 = st.columns([1, 1])
    with col1:
        st.markdown("### 👨‍💻 Developed By")
        st.write("**Indranil Chatterjee**")
        st.write("Email: indranil.ranaghat@gmail.com")
        st.caption("Version 1.0.0 | Release: February 2026")
    
    with col2:
        st.markdown("### 🛠️ Technology Stack")
        st.markdown("`Streamlit` `Python` `MongoDB` `Pandas`")

    # Add a small copyright footer
    current_year = datetime.now().year
    st.markdown(
        f"<div style='text-align: center; color: gray; margin-top: 50px;'>"
        f"© {current_year} Call Log Management System | All Rights Reserved.</div>", 
        unsafe_allow_html=True
    )