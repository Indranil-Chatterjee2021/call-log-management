"""
Reports Page Module
Handles export of call log data to Excel with optional email functionality
"""
import streamlit as st
import pandas as pd
from datetime import datetime
import io
from storage import DateRange


def render_reports_page(repo):
    """
    Render the Reports page with data export functionality.
    """
    st.subheader("📊 Export & Analytical Reports")
    try:
        # 1. Check if any data exists at all
        all_records = repo.calllog_list()
        
        if not all_records:
            st.warning("No data found in the database to export.")
            return

        # 2. Date range filter and Clear Button
        col1, col2, col3 = st.columns([1.5, 1.5, 7])
        with col1:
            start_date = st.date_input("Start Date", value=None, key="start_date")
        with col2:
            end_date = st.date_input("End Date", value=None, key="end_date")
        
        # 3. Apply the filter (None values result in all data being fetched)
        dr = DateRange(
            start=datetime.combine(start_date, datetime.min.time()) if start_date else None,
            end=datetime.combine(end_date, datetime.max.time()) if end_date else None,
        )
        
        # 4. Get the DataFrame
        df = _df_from_records(repo.calllog_list(dr))
        
        # 5. Display table and export options if data is present
        if not df.empty:
            st.dataframe(df, use_container_width=True)
            st.info(f"Total records: {len(df)}")
            
            # Prepare Excel Buffer
            buffer = io.BytesIO()
            with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
                df.to_excel(writer, index=False, sheet_name='CallLogEntries')
            buffer.seek(0)
            
            exp_col1, exp_col2 = st.columns([1.5, 8.5])
            with exp_col1:
                st.download_button(
                    label="📥 Download Excel",
                    data=buffer,
                    file_name=f"CallLog_Export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )
            with exp_col2:
                _render_email_section(buffer)
        else:
            st.warning("No records found for the selected criteria.")
            
    except Exception as e:
        st.error(f"Error loading reports: {e}")
        

def _df_from_records(records: list[dict]) -> pd.DataFrame:
    """Convert records to DataFrame and remove id column."""
    if not records:
        return pd.DataFrame()
    df = pd.DataFrame.from_records(records)
    # Remove id column if present
    if 'id' in df.columns:
        df = df.drop(columns=['id'])
    return df


def _render_email_section(buffer):
    """Render email report functionality."""
    repo = st.session_state.active_repo
    
    # Get email config from database
    email_config = repo.email_config_get()
    
    if not email_config:
        st.warning("⚠️ Email not configured. Please configure email settings in the Email page first.")
        return
    
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
                    
                    # Use config from database
                    smtp_server = email_config.get("smtp_server")
                    smtp_port = email_config.get("smtp_port")
                    smtp_user = email_config.get("smtp_user")
                    smtp_password = email_config.get("smtp_password")
                    
                    if not smtp_user or not smtp_password:
                        st.error("⚠️ Email configuration incomplete. Please update settings.")
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
            else:
                st.warning("Please enter a recipient email address.")
