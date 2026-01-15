# Call Log Management System

A Streamlit-based web application for managing call logs with MSSQL database integration.

## Features

1. **Master Data Management**: CRUD operations for master data
   - View all master records
   - Add new master records
   - Update existing master records
   - Delete master records

2. **Call Log Entry**: Create new call log entries with auto-fill functionality
   - Enter mobile number to auto-fill related fields from Master table
   - Fields auto-filled: Project, Town, Requester, RD Code, RD Name, State, Designation, Name
   - Dropdown fields: Module, Issue, Solution, Solved On, Call On, Type

3. **Reports**: Export call log data to Excel
   - Filter by date range
   - Export filtered data to Excel format
4. **Settings (required)**:
   - User must choose **MSSQL** or **MongoDB**
   - Test connection
   - Save & Activate (stores config inside the chosen backend)

## Prerequisites

- Python 3.8 or higher
- One of:
  - MSSQL Server (SQL Server or SQL Server Express) + ODBC Driver 17/18
  - MongoDB (local or Atlas)

## Installation

1. Clone or download this repository

2. Create a virtual environment (recommended):
```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Configure database connection:
   - Create a `.env` file in the project root
   - Add the following variables:
```
DB_BACKEND=mssql   # or: mongodb

DB_SERVER=your_server_name
DB_NAME=CallLogDB
DB_USER=your_username
DB_PASSWORD=your_password
DB_DRIVER={ODBC Driver 17 for SQL Server}

# MongoDB (used only when DB_BACKEND=mongodb)
MONGO_URI=mongodb://localhost:27017
MONGO_DB=CallLogDB
```

## First Run (Mandatory Settings Step)

1. Start the app:
```bash
streamlit run app.py
```

2. Go to **Settings**
   - Select backend (**MSSQL** or **MongoDB**)
   - Enter connection details
   - Click **Test Connection**
   - Click **Save & Activate**

After this, the other pages (Master / Call Log / Reports) will be enabled.

## Auto-load on Startup (Recommended)

After you click **Save & Activate** in Settings, the app writes a local file:
- `.calllogapp_bootstrap.json`

On the next startup, the app will automatically try to connect using this file and activate the backend.

**Security note**: this file can contain credentials (MSSQL password / Mongo URI). It is added to `.gitignore` and should be kept private.

## Database Setup

Run the initialization script to create/import master data:
```bash
python init_database.py
```

This will:
- **MSSQL**: create `Master` + `CallLogEntries` tables, then import `Master` sheet
- **MongoDB**: ensure collections/indexes exist, then import `Master` sheet

## Where Settings Are Stored

- **MSSQL**: `dbo.AppConfig` table (key: `active`)
- **MongoDB**: `appConfig` collection (`_id: "active"`)

## Running the Application

Start the Streamlit app:
```bash
streamlit run app.py
```

The application will open in your default web browser at `http://localhost:8501`

## Usage

### Master Data Management
1. Navigate to "Master Data Management" from the sidebar
2. Use the tabs to View, Add, Update, or Delete master records
3. Mobile No is a required field and must be unique

### Call Log Entry
1. Navigate to "Call Log Entry" from the sidebar
2. Enter a mobile number in the auto-fill section and click "Auto-fill from Master"
3. The form will be populated with data from the Master table
4. Fill in the dropdown fields (Module, Issue, Solution, etc.)
5. Click "Submit Call Log Entry" to save

### Reports
1. Navigate to "Reports" from the sidebar
2. Optionally select a date range to filter records
3. Click "Download Excel File" to export the data

## Database Schema

### Master Table
- SrNo (Primary Key, Auto-increment)
- MobileNo (Unique, Required)
- Project
- TownType
- Requester
- RDCode
- RDName
- Town
- State
- Designation
- Name
- GSTNo
- EmailID
- CreatedDate
- UpdatedDate

### CallLogEntries Table
- SrNo (Primary Key, Auto-increment)
- Date
- MobileNo (Required)
- Project
- Town
- Requester
- RDCode
- RDName
- State
- Designation
- Name
- Module
- Issue
- Solution
- SolvedOn
- CallOn
- Type
- CreatedDate
- UpdatedDate

## Notes

- The Excel file `Verma R Master.xlsx` must be in the project root directory
- Dropdown values are extracted from the "Sheet1" sheet in the Excel file
- Master data is imported from the "Master" sheet

## Troubleshooting

### Database Connection Issues
- **MSSQL**:
  - Verify MSSQL Server is running
  - Check ODBC driver is installed
  - Verify connection credentials in `.env` file
  - Ensure database exists and user has proper permissions
- **MongoDB**:
  - Verify MongoDB is running / reachable
  - Verify `MONGO_URI` and `MONGO_DB` in `.env`

### Import Issues
- Ensure `Verma R Master.xlsx` is in the project root
- Check that sheet names match: "Master", "Database", "Sheet1"
- Verify Excel file is not open in another application

## License

This project is provided as-is for internal use.
