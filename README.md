# Call Log Management System

A Streamlit-based web application for managing call logs with authentication and support for both MSSQL and MongoDB databases.

## Features

1. **User Authentication**: Secure login system
   - User registration (first-time setup)
   - Login with username/password
   - Password reset functionality
   - Session-based authentication

2. **Master Data Management**: CRUD operations for master data
   - View all master records
   - Add new master records
   - Update existing master records
   - Delete master records

3. **Call Log Entry**: Create new call log entries with auto-fill functionality
   - Enter mobile number to auto-fill related fields from Master table
   - Fields auto-filled: Project, Town, Requester, RD Code, RD Name, State, Designation, Name
   - Dropdown fields: Module, Issue, Solution, Solved On, Call On, Type

4. **Reports**: Export call log data to Excel
   - Filter by date range
   - Export filtered data to Excel format

5. **Settings (required)**:
   - User must choose **MSSQL** (local only) or **MongoDB** (local and cloud)
   - Test connection
   - Save & Activate (stores config inside the chosen backend)

## Deployment Options

### Option 1: Local Executable
- Create a standalone executable file
- Supports both MSSQL and MongoDB
- No installation required for end users
- See "Creating Executable" section below

### Option 2: Streamlit Cloud
- Deploy to Streamlit Cloud for worldwide access
- **MongoDB only** (MSSQL disabled on cloud)
- Free hosting with Streamlit Community Cloud
- See "Deploying to Streamlit Cloud" section below

## Prerequisites

### For Local Use:
- Python 3.8 or higher
- One of:
  - **MSSQL Server** (SQL Server or SQL Server Express) + ODBC Driver 17/18
  - **MongoDB** (local or Atlas)

### For Streamlit Cloud:
- GitHub account
- MongoDB Atlas account (free tier available)

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
DB_NAME=CALLLOG
DB_USER=your_username
DB_PASSWORD=your_password
DB_DRIVER={ODBC Driver 17 for SQL Server}

# MongoDB (used only when DB_BACKEND=mongodb)
MONGO_URI=mongodb://localhost:27017
MONGO_DB=call-logs
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

### For MSSQL (Local Use):
**Tables are automatically created!** When you click "Save & Activate MSSQL", the application will automatically create all required tables:
- Master
- CallLogEntries
- Users
- AppConfig

No manual setup required!

### For MongoDB (Local or Cloud):
Collections are automatically created when first used. No manual setup required.

### Master Data Import:
The app automatically imports master data from `Verma R Master.xlsx` on first run if the Master collection/table is empty.

## Where Settings Are Stored

- **MSSQL**: `dbo.AppConfig` table (key: `active`)
- **MongoDB**: `appConfig` collection (`_id: "active"`)

## Running the Application Locally

Start the Streamlit app:
```bash
streamlit run app.py
```

The application will open in your default web browser at `http://localhost:8501`

## Creating Executable

To create a standalone executable that can be shared with others:

1. Install PyInstaller (already in requirements.txt):
```bash
pip install pyinstaller
```

2. Build the executable:
```bash
pyinstaller app.spec
```

3. The executable will be created in the `dist` folder:
   - `dist/app` (macOS/Linux) or `dist/app.exe` (Windows)

4. Share the entire `dist` folder with users - they can run the app without installing Python!

**Note**: The executable includes support for both MSSQL and MongoDB.

## Deploying to Streamlit Cloud

### Prerequisites:
1. Create a [MongoDB Atlas](https://www.mongodb.com/cloud/atlas/register) account (free tier available)
2. Create a cluster and get your connection URI
3. Create a [GitHub](https://github.com) account
4. Create a [Streamlit Cloud](https://streamlit.io/cloud) account

### Steps:

1. **Push your code to GitHub**:
   - Create a new repository on GitHub
   - Push your project files (including `Verma R Master.xlsx`)
   - Make sure `.env` and `bootstrap.json` are in `.gitignore`

2. **Deploy on Streamlit Cloud**:
   - Go to [share.streamlit.io](https://share.streamlit.io)
   - Click "New app"
   - Connect your GitHub account
   - Select your repository and branch
   - Set Main file path: `app.py`
   - Click "Deploy!"

3. **Configure for each user**:
   - Each user opens your Streamlit Cloud URL
   - They enter their MongoDB Atlas URI in the Settings page
   - They register and login
   - The app automatically imports master data to their database

**Important Notes**:
- **MSSQL is disabled on Streamlit Cloud** - only MongoDB is available
- Each user must provide their own MongoDB connection URI
- Each user gets their own isolated database
- Users need to re-enter their MongoDB URI on each visit (for security)

## Usage

### First Time Setup:
1. Open the application
2. Go to "Settings" page
3. Choose your database (MSSQL for local, MongoDB for local or cloud)
4. Enter connection details and click "Save & Activate"
5. **Register** your first user account
6. **Login** with your credentials
7. Master data is automatically imported on first run

### Subsequent Usage:
1. Open the application
2. Enter database credentials (if needed)
3. **Login** with your username and password
4. Use the application

### Master Data Management
1. Navigate to "Master Data Management"
2. Use the tabs to View, Add, Update, or Delete master records
3. Mobile No is a required field and must be unique

### Call Log Entry
1. Navigate to "Call Log Entry"
2. Enter a mobile number and click "Fetch from Master"
3. The form will be populated with data from the Master table
4. Fill in the dropdown fields (Module, Issue, Solution, etc.)
5. Click "Add Call Log" to save

### Reports
1. Navigate to "Reports"
2. Optionally select a date range to filter records
3. View data in the table
4. Click "Download Excel File" to export

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
