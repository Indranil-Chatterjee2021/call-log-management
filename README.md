# Call Log Management System

A comprehensive Streamlit-based web application for managing call logs with user authentication, master data management, and MongoDB as the supported database backend.

## Overview

This application provides a complete solution for tracking and managing customer call logs with auto-fill capabilities from master data. It supports local deployment and cloud deployment (MongoDB) on Streamlit Cloud.

## Features

### 1. **User Authentication**
   - User registration (first-time setup)
   - Secure login with username/password
   - Password reset functionality
   - Session-based authentication with automatic logout

### 2. **Master Data Management**
   - **Manual Excel Import**: Import master data from Excel file (one-time process)
   - **CRUD Operations**: View, Add, Update, and Delete master records
   - **Unique Mobile Numbers**: Enforces unique mobile number constraint
   - **Duplicate Detection**: Automatically detects and reports duplicates during import
   - **Import Disabled**: Import button is disabled once data exists to prevent accidental overwrites

### 3. **Dropdown Configuration** (New!)
   - **Centralized Management**: Manage all dropdown values used throughout the application
   - **Database Storage**: All dropdown values stored in database (no Excel dependency after setup)
   - **Easy Addition**: Add new values to any dropdown field via UI
   - **Bulk Import**: One-time import from Excel to extract dropdown values
   - **Fields Managed**: Projects, Town Types, Requesters, Designations, Modules, Issues, Solutions, Solved On, Call On, Types

### 4. **Call Log Entry**
   - **Auto-Fill Functionality**: Enter mobile number and fetch related data from Master table
   - **Auto-filled Fields**: Project, Town, Requester, RD Code, RD Name, State, Designation, Name
   - **Dropdown Fields**: Module, Issue, Solution, Solved On, Call On, Type
   - **Date Selection**: Record call date and time

### 5. **Reports & Export**
   - **Date Range Filtering**: Filter call logs by date range
   - **Excel Export**: Download filtered data as Excel file
   - **Email Reports**: Send reports via email (requires email configuration)
   - **Data Preview**: View filtered data before export

### 6. **Settings**
   - **Database Backend Selection**: MongoDB (local/cloud)
   - **Connection Testing**: Test database connection before activation
   - **Auto-Bootstrap**: Automatically reconnect on app restart
   - **Email Configuration**: Configure SMTP settings for email reports

## Deployment Options

### Option 1: Local Deployment
- Create a standalone executable file
- Uses **MongoDB**
- No installation required for end users
- See "Creating Executable" section below

### Option 2: Cloud Deployment (Streamlit Cloud)
- Deploy to Streamlit Cloud for worldwide access
- **MongoDB only**
- Free hosting with Streamlit Community Cloud
- See "Deploying to Streamlit Cloud" section below

## Prerequisites

### For Local Use:
- **Python 3.8 or higher**
- **MongoDB** (local installation or MongoDB Atlas)

### For Streamlit Cloud:
- GitHub account
- MongoDB Atlas account (free tier available)

## Installation

### 1. Clone or Download Repository
```bash
git clone <repository-url>
cd callLogApp
```

### 2. Create Virtual Environment (Recommended)
```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Configure Environment Variables (Optional)
Create a `.env` file in the project root for default connection settings:

```env
DB_BACKEND=mongodb

# MongoDB Settings
MONGO_URI=mongodb://localhost:27017
MONGO_DB=call-logs
```

**Note**: Environment variables are optional. You can configure everything through the Settings page in the UI.

## First Run (Mandatory Settings Step)

### 1. Start the Application
```bash
streamlit run app.py
```
The application will open at `http://localhost:8501`

### 2. Configure Database Backend
1. Navigate to **Settings** page
2. Select the MongoDB backend and enter connection details
3. Click **Test Connection** to verify
4. Click **Save & Activate** to initialize the database

### 3. Initialize Database
- **MongoDB**: Collections and indexes are created automatically when first used

### 4. Register First User
1. After database activation, the app will show the **Register** tab
2. Create your first user account with username and password
3. Subsequent users can only be added by administrators

### 5. Login
1. Enter your credentials on the **Login** tab
2. Access all application features after successful authentication

## Excel File Format Requirements

The application's database structure and dropdown values are designed based on Excel file format. If you plan to import data from Excel, ensure your Excel file follows this structure:

### Excel File: `Verma R Master.xlsx` (or any name)

#### **Sheet 1: "Master"** (for Master Data Import)
This sheet contains customer/contact master data. Header row should be at **Row 2** (Row 1 can be title).

**Required Columns (in order):**
| Column | Field Name | Data Type | Required | Description |
|--------|------------|-----------|----------|-------------|
| A | SrNo | Number | No | Serial Number (auto-generated in DB) |
| B | MobileNo | Text/Number | **Yes** | Unique mobile number (Primary Key) |
| C | Project | Text | No | Project name |
| D | TownType | Text | No | Type of town |
| E | Requester | Text | No | Person requesting |
| F | RDCode | Text | No | RD code |
| G | RDName | Text | No | RD name |
| H | Town | Text | No | Town/City name |
| I | State | Text | No | State name |
| J | Designation | Text | No | Contact's designation |
| K | Name | Text | No | Contact's name |
| L | GSTNo | Text | No | GST number |
| M | EmailID | Text | No | Email address |

**Example:**
```
Row 1: [Title - optional]
Row 2: SrNo | Mobile No | Project | Town Type | Requester | RD Code | RD Name | Town | State | Designation | Name | GST No | Email ID
Row 3: 1 | 9876543210 | Project A | Urban | John Doe | RD001 | Region 1 | Mumbai | Maharashtra | Manager | Jane Smith | 27XXXXX | jane@example.com
Row 4: 2 | 9876543211 | Project B | Rural | Alice Brown | RD002 | Region 2 | Pune | Maharashtra | Director | Bob Wilson | 27YYYYY | bob@example.com
...
```

#### **Sheet 2: "Sheet1"** (for Dropdown Values Import)
This sheet contains all dropdown values used throughout the application. Header row should be at **Row 3** (Rows 1-2 can be titles).

**Required Columns (in order):**
| Column | Field Name | Description | Used In |
|--------|------------|-------------|---------|
| A (Unnamed: 0) | PROJECT | List of all projects | Master Data, Call Log |
| B (Unnamed: 1) | TOWN TYPE | List of town types | Master Data |
| C (Unnamed: 2) | REQUSETER | List of requesters | Master Data, Call Log |
| H (Unnamed: 7) | DESIGNATION | List of designations | Master Data, Call Log |
| J (Unnamed: 9) | MODULE | List of modules | Call Log |
| K (Unnamed: 10) | ISSUE | List of issue types | Call Log |
| L (Unnamed: 11) | SOLUTION | List of solution types | Call Log |
| M (Unnamed: 12) | SOLVED ON | List of solved on values | Call Log |
| N (Unnamed: 13) | CALL ON | List of call on values | Call Log |
| O (Unnamed: 14) | TYPE | List of call types | Call Log |

**Example:**
```
Row 1-2: [Titles - optional]
Row 3: PROJECT | TOWN TYPE | REQUSETER | ... | DESIGNATION | ... | MODULE | ISSUE | SOLUTION | SOLVED ON | CALL ON | TYPE
Row 4: Project A | Urban | John Doe | ... | Manager | ... | Accounts | Login Issue | Reset Password | Phone | Mobile | Support
Row 5: Project B | Rural | Alice | ... | Director | ... | Reports | Data Error | Fixed Query | Email | Email | Query
Row 6: Project C | Semi-Urban | Bob | ... | Executive | ... | Dashboard | Display | Updated UI | WhatsApp | SMS | Feedback
...
```

**Important Notes:**
- The Excel file is **only used for initial import**
- After import, all data is managed through the application UI
- Dropdown values are extracted from unique values in each column
- Header text (like "PROJECT", "TOWN TYPE") is automatically excluded
- Empty cells and duplicate values are automatically handled
- Once data is imported, you can manage everything through the **Dropdown Config** page

## Auto-Bootstrap on Startup

After clicking **Save & Activate** in Settings, the app creates:
- `.calllogapp_bootstrap.json` (local file)

On subsequent startups, the app automatically:
- Reads this file
- Tests the database connection
- Activates the backend if connection is successful

**Security Note**: This file may contain credentials (MongoDB URI). It is included in `.gitignore` and should be kept private.

## Database Schema

### Database Tables/Collections

#### 1. **Master** (Customer/Contact Master Data)
| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| SrNo / _id | INT / ObjectId | Primary Key, Auto-increment | Unique identifier |
| MobileNo | NVARCHAR(20) / String | UNIQUE, REQUIRED | Mobile number (unique) |
| Project | NVARCHAR(200) / String | Optional | Project name |
| TownType | NVARCHAR(100) / String | Optional | Type of town |
| Requester | NVARCHAR(200) / String | Optional | Person requesting |
| RDCode | NVARCHAR(50) / String | Optional | RD code |
| RDName | NVARCHAR(200) / String | Optional | RD name |
| Town | NVARCHAR(200) / String | Optional | Town/City |
| State | NVARCHAR(100) / String | Optional | State |
| Designation | NVARCHAR(200) / String | Optional | Designation |
| Name | NVARCHAR(200) / String | Optional | Contact name |
| GSTNo | NVARCHAR(50) / String | Optional | GST number |
| EmailID | NVARCHAR(200) / String | Optional | Email address |
| CreatedDate | DATETIME2 / Date | Auto | Creation timestamp |
| UpdatedDate | DATETIME2 / Date | Auto | Last update timestamp |

**Indexes**: MobileNo (unique index)

#### 2. **CallLogEntries** (Call Log Records)
| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| SrNo / _id | INT / ObjectId | Primary Key, Auto-increment | Unique identifier |
| Date | DATETIME2 / Date | REQUIRED | Call date and time |
| MobileNo | NVARCHAR(20) / String | Optional | Mobile number |
| Project | NVARCHAR(200) / String | Optional | Project name |
| Town | NVARCHAR(200) / String | Optional | Town/City |
| Requester | NVARCHAR(200) / String | Optional | Person requesting |
| RDCode | NVARCHAR(50) / String | Optional | RD code |
| RDName | NVARCHAR(200) / String | Optional | RD name |
| State | NVARCHAR(100) / String | Optional | State |
| Designation | NVARCHAR(200) / String | Optional | Designation |
| Name | NVARCHAR(200) / String | Optional | Contact name |
| Module | NVARCHAR(200) / String | Optional | Module/Feature |
| Issue | NVARCHAR(MAX) / String | Optional | Issue description |
| Solution | NVARCHAR(MAX) / String | Optional | Solution provided |
| SolvedOn | NVARCHAR(200) / String | Optional | Resolution channel |
| CallOn | NVARCHAR(200) / String | Optional | Call channel |
| Type | NVARCHAR(100) / String | Optional | Call type |
| CreatedDate | DATETIME2 / Date | Auto | Creation timestamp |
| UpdatedDate | DATETIME2 / Date | Auto | Last update timestamp |

**Indexes**: Date (for efficient date range queries)

#### 3. **Users** (User Authentication)
| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| UserId / _id | INT / ObjectId | Primary Key, Auto-increment | Unique identifier |
| Username | NVARCHAR(100) / String | UNIQUE, REQUIRED | Login username |
| Password | NVARCHAR(256) / String | REQUIRED | Hashed password |
| CreatedDate | DATETIME2 / Date | Auto | Creation timestamp |
| UpdatedDate | DATETIME2 / Date | Optional | Last update timestamp |

**Indexes**: Username (unique index)

#### 4. **MiscData** (Dropdown Configuration)
This document stores dropdown configuration values used throughout the application.

| Field | Type | Description |
|-------|------|-------------|
| _id | String | Document id (e.g. "dropdown_values") |
| projects | Array[String] | List of projects |
| town_types | Array[String] | List of town types |
| requesters | Array[String] | List of requesters |
| designations | Array[String] | List of designations |
| modules | Array[String] | List of modules |
| issues | Array[String] | List of issues |
| solutions | Array[String] | List of solutions |
| solved_on | Array[String] | List of solved on values |
| call_on | Array[String] | List of call on values |
| types | Array[String] | List of call types |

#### 5. **EmailConfig** (Email Settings)
| Field | Type | Description |
|-------|------|-------------|
| ConfigId / _id | INT / String | Primary Key |
| SmtpServer | NVARCHAR(200) / String | SMTP server address |
| SmtpPort | INT / Number | SMTP port |
| SmtpUser | NVARCHAR(200) / String | SMTP username |
| SmtpPassword | NVARCHAR(500) / String | SMTP password |
| CreatedDate | DATETIME2 / Date | Creation timestamp |
| UpdatedDate | DATETIME2 / Date | Last update timestamp |

#### 6. **AppConfig** (Application Configuration)
Stores backend configuration and settings.

**MongoDB**: Collection with document `_id: "active"`

## Usage Guide

### First Time Setup:
1. **Configure Database**: Go to Settings → Choose backend → Test & Activate
2. **Register User**: Create your first user account
3. **Import Master Data**: (Optional) Go to Master Data Management → Import from Excel
4. **Configure Dropdowns**: (Optional) Go to Dropdown Config → Import or add values manually

### Daily Operations:

#### **Master Data Management**
1. Navigate to **Master Data Management**
2. **View All**: See all master records with import button
   - **Import from Excel**: Disabled once data exists
   - Use this button for one-time import
3. **Add New**: Create new master records manually
4. **Update**: Modify existing records
5. **Delete**: Remove records

**Important**: Mobile number must be unique!

#### **Dropdown Configuration**
1. Navigate to **Dropdown Config**
2. **Add New Values**:
   - Select field type (Projects, Modules, Issues, etc.)
   - Enter new value
   - Click "Add Value"
   - Values are immediately available in dropdowns
3. **View All**: See all dropdown values for each field
4. **Bulk Import**: (One-time only) Import from Excel Sheet1

**Supported Fields:**
- Projects
- Town Types
- Requesters
- Designations
- Modules
- Issues
- Solutions
- Solved On
- Call On
- Types

#### **Call Log Entry**
1. Navigate to **Call Log Entry**
2. **Enter Mobile Number** and click "Fetch from Master"
3. Form auto-fills with data from Master table:
   - Project, Town, Requester
   - RD Code, RD Name, State
   - Designation, Name
4. **Select from Dropdowns**:
   - Module (e.g., Accounts, Reports)
   - Issue (e.g., Login Issue)
   - Solution (e.g., Reset Password)
   - Solved On (e.g., Phone, Email)
   - Call On (e.g., Mobile, WhatsApp)
   - Type (e.g., Support, Query)
5. Click **Add Call Log** to save

#### **Reports & Export**
1. Navigate to **Reports**
2. **Filter by Date**: (Optional) Select start and end dates
3. **View Data**: Preview filtered records in table
4. **Download**: Click "Download Excel File"
5. **Email** (if configured): 
   - Expand "Email Report" section
   - Enter recipient email
   - Click "Send Email"

#### **Settings**
1. **Database Configuration**: Change or test connection
2. **Email Configuration**: 
   - Enter SMTP server details
   - Test email settings
   - Save configuration

## Running the Application

### Local Development
```bash
# Activate virtual environment
source venv/bin/activate  # Windows: venv\Scripts\activate

# Run the application
streamlit run app.py
```

Access at: `http://localhost:8501`

### Production Deployment
See "Creating Executable" or "Deploying to Streamlit Cloud" sections below.

## Creating Standalone Executable

Create a distributable executable file that users can run without installing Python.

### Prerequisites
```bash
pip install pyinstaller
```

### Build Executable
```bash
pyinstaller app.spec
```

### Output
- **Location**: `dist/app/` (or `dist/app.exe` on Windows)
- **Size**: Approximately 150-200 MB (includes Python interpreter and dependencies)
- **Distribution**: Share the entire `dist/app/` folder

### Running the Executable
**Windows:**
```cmd
dist\app\app.exe
```

**macOS/Linux:**
```bash
./dist/app/app
```

The application will open in the default browser automatically.

**Note**: The executable uses MongoDB as the supported backend.

## Deploying to Streamlit Cloud

Deploy your application for worldwide access with MongoDB backend.

### Prerequisites
1. **GitHub Account**: [github.com](https://github.com)
2. **MongoDB Atlas**: [mongodb.com/cloud/atlas](https://www.mongodb.com/cloud/atlas/register)
3. **Streamlit Cloud Account**: [streamlit.io/cloud](https://streamlit.io/cloud)

### Step 1: Prepare MongoDB Atlas

1. **Create Free Cluster**:
   - Sign up for MongoDB Atlas
   - Create a free M0 cluster (512 MB storage)
   - Choose a region close to your users

2. **Configure Database Access**:
   - Go to Database Access
   - Add a database user with password
   - Note down the username and password

3. **Configure Network Access**:
   - Go to Network Access
   - Click "Add IP Address"
   - Select "Allow Access from Anywhere" (0.0.0.0/0)
   - This is required for Streamlit Cloud

4. **Get Connection String**:
   - Go to your cluster
   - Click "Connect" → "Connect your application"
   - Copy the connection URI
   - Replace `<password>` with your actual password
   - Example: `mongodb+srv://username:password@cluster0.xxxxx.mongodb.net/`

### Step 2: Push to GitHub

1. **Create Repository**:
```bash
git init
git add .
git commit -m "Initial commit"
git remote add origin https://github.com/yourusername/callLogApp.git
git push -u origin main
```

2. **Verify Files**:
   - Ensure `requirements.txt` is included
   - Ensure `.env` and `.calllogapp_bootstrap.json` are in `.gitignore`
   - Include Excel file if you want to use import feature

### Step 3: Deploy to Streamlit Cloud

1. **Access Streamlit Cloud**:
   - Go to [share.streamlit.io](https://share.streamlit.io)
   - Sign in with GitHub

2. **Create New App**:
   - Click "New app"
   - Select your repository
   - Branch: `main` (or your branch name)
   - Main file path: `app.py`

3. **Advanced Settings** (Optional):
   - Python version: 3.8+
   - No secrets needed (users enter their MongoDB URI in the app)

4. **Deploy**:
   - Click "Deploy!"
   - Wait for deployment (3-5 minutes)

### Step 4: Configure Application

**For Each User:**
1. Open the deployed Streamlit app URL
2. Go to **Settings** page
3. Select **MongoDB** backend
4. Enter their MongoDB Atlas connection URI:
   ```
   mongodb+srv://username:password@cluster0.xxxxx.mongodb.net/call-logs
   ```
5. Click **Test Connection**
6. Click **Save & Activate**
7. Register and login

### Important Notes

- MongoDB is the supported backend on Streamlit Cloud
- Each user should use their **own MongoDB Atlas cluster** for data isolation
- Free MongoDB Atlas tier (M0) is sufficient for most use cases
- Connection URI is **not persisted** between sessions (for security)
- Users need to re-enter their MongoDB URI each time they visit
- The app creates its own database and collections automatically

### Multi-Tenant Setup

**Option 1: Individual Databases (Recommended)**
- Each user creates their own MongoDB Atlas account
- Complete data isolation
- No shared infrastructure

**Option 2: Shared Cluster**
- Create one MongoDB Atlas cluster
- Share connection URI with all users
- Each user gets their own database automatically
- Set database name in connection string: `mongodb+srv://...mongodb.net/username_calllog`

### Troubleshooting Cloud Deployment

**Issue**: Connection timeout
- **Solution**: Ensure "Allow Access from Anywhere" in MongoDB Network Access

**Issue**: Authentication failed
- **Solution**: Check username and password in connection URI

**Issue**: Database not found
- **Solution**: Database is created automatically; ensure URI is correct

**Issue**: App shows "Please configure database"
- **Solution**: Go to Settings and enter MongoDB connection details

## Data Flow & Architecture

### Application Architecture
```
┌─────────────────────────────────────────────────┐
│           Streamlit Frontend (app.py)           │
├─────────────────────────────────────────────────┤
│  Pages:                                         │
│  - Login/Auth (login_page.py)                   │
│  - Settings (settings_page.py)                  │
│  - Master Data (master_data_page.py)            │
│  - Dropdown Config (misc_types_page.py)         │
│  - Call Log Entry (call_log_page.py)            │
│  - Reports (reports_page.py)                    │
├─────────────────────────────────────────────────┤
│        Repository Layer (storage/)              │
│  - Base Protocol (base.py)                      │
│  - MongoDB Repository (mongo_repo.py)           │
├─────────────────────────────────────────────────┤
│              Database Layer                     │
│  MongoDB Atlas        │                        │
│  (Local/Cloud)        │                        │
└─────────────────────────────────────────────────┘
```

### Data Flow for Call Log Entry
1. User enters mobile number
2. Click "Fetch from Master" → Query Master table
3. Auto-fill form with Master data
4. User selects dropdown values (from MiscData)
5. Click "Add Call Log" → Insert into CallLogEntries

### Data Flow for Master Data Import
1. User selects Excel file (Master sheet)
2. Click "Import from Excel"
3. Parse Excel → Extract records
4. Detect and report duplicates
5. Insert into Master table
6. Import button becomes disabled

### Data Flow for Dropdown Configuration
1. **First Time**: Bulk import from Excel Sheet1
2. **Ongoing**: Add values through UI
3. Values stored in MiscData table/collection
4. Cached in session state for performance
5. Used throughout app in dropdown fields

## Project Structure

```
callLogApp/
├── app.py                      # Main application entry point
├── requirements.txt            # Python dependencies
├── app.spec                    # PyInstaller configuration
├── .env                        # Environment variables (optional)
├── .gitignore                  # Git ignore file
├── README.md                   # This file
├── style.css                   # Custom CSS styling
│
├── pages/                      # Streamlit pages
│   ├── login_page.py          # Authentication page
│   ├── settings_page.py       # Database & email configuration
│   ├── master_data_page.py    # Master data CRUD + import
│   ├── misc_types_page.py     # Dropdown configuration (NEW)
│   ├── call_log_page.py       # Call log entry with auto-fill
│   └── reports_page.py        # Reports and export
│
├── storage/                    # Data access layer
│   ├── __init__.py            # Repository factory
│   ├── base.py                # Repository protocol (interface)
│   ├── mongo_repo.py          # MongoDB implementation
│   └── factory.py             # Repository creation logic
│
├── auth.py                     # Authentication utilities
├── init_database.py           # Database initialization
├── dropdown_data.py           # Dropdown data retrieval (DB-based)
├── settings_store.py          # Settings management
├── bootstrap_config.py        # Auto-reconnect configuration
│
└── build/                     # PyInstaller build artifacts (ignored)
```

## Key Features Explained

### 1. **Auto-Fill from Master Data**
When entering a call log, the application:
- Accepts mobile number input
- Queries the Master table for matching record
- Auto-fills 8 fields: Project, Town, Requester, RD Code, RD Name, State, Designation, Name
- Saves time and ensures data consistency

### 2. **Dropdown Management**
All dropdown values are:
- Stored in database (MiscData table/collection)
- Managed through UI (no Excel editing needed)
- Cached for performance
- Sorted alphabetically
- Deduplicated automatically

### 3. **Database Abstraction**
The repository pattern allows:
- Abstracted database access (MongoDB)
- Same codebase for data access
- Easy testing and maintenance
- Future backend additions possible

### 4. **Security**
- Passwords are hashed (bcrypt)
- Session-based authentication
- Bootstrap file excluded from version control
- MongoDB URI not persisted on cloud (security)

### 5. **Import Protection**
- Import button disabled after first import
- Prevents accidental data overwrites
- Users can still add/update records individually
- Duplicate mobile numbers detected and reported

## Advanced Configuration

### Custom Styling
Edit `style.css` to customize:
- Colors and themes
- Font sizes
- Layout spacing
- Button styles

### Email Configuration
Configure SMTP settings in Settings page:
- **SMTP Server**: e.g., `smtp.gmail.com`
- **SMTP Port**: e.g., `587` (TLS) or `465` (SSL)
- **SMTP User**: Your email address
- **SMTP Password**: App-specific password (recommended)

**Gmail Example:**
1. Enable 2-factor authentication
2. Generate app-specific password
3. Use `smtp.gmail.com:587`

### Environment Variables
Create `.env` file for default settings:
```env
# Default backend (optional)
DB_BACKEND=mongodb

# MongoDB Settings (optional)
MONGO_URI=mongodb://localhost:27017
MONGO_DB=call-logs
```

## Performance Optimization

### For Large Datasets
1. **Use Indexes**: Automatically created on MobileNo and Date fields
2. **Date Range Filtering**: Always use date filters in Reports
3. **Batch Operations**: Import large datasets using Excel import

### For Slow Connections
1. **Pagination**: Consider implementing for very large tables
2. **Connection Pooling**: MongoDB driver handles this automatically
3. **Caching**: Dropdown values cached in session state

## Backup & Restore

### MongoDB Backup
```bash
# Export database
mongodump --uri="mongodb://localhost:27017/call-logs" --out=./backup

# Import database
mongorestore --uri="mongodb://localhost:27017/call-logs" ./backup/call-logs
```

### MongoDB Atlas Backup
- Automatic continuous backups in paid tiers
- Manual export via MongoDB Compass (GUI tool)
- Use `mongodump` with connection string

## Troubleshooting

### Database Connection Issues

**MongoDB Connection Failed:**
```
✓ Check MongoDB service: mongod --version
✓ Verify connection URI format
✓ Test with MongoDB Compass
✓ Check network access (MongoDB Atlas)
✓ Verify username/password
✓ Check IP whitelist (MongoDB Atlas)
```

### Import Issues

**Excel File Not Found:**
- Ensure file is in same directory as `app.py`
- Check file name matches exactly (case-sensitive)
- File should not be open in Excel

**Import Button Not Appearing:**
- Data already exists (button is disabled)
- Delete existing data to re-enable import

**Duplicate Mobile Numbers:**
- Excel contains duplicate entries
- Check duplicate report after import
- Only first occurrence is imported

### Application Issues

**Pages Not Loading:**
- Database not configured
- Go to Settings → Test & Activate
- Check authentication (logout and login)

**Dropdowns Empty:**
- No dropdown data configured
- Go to Dropdown Config → Import from Excel
- Or add values manually

**Auto-Fill Not Working:**
- Mobile number not in Master table
- Check Master Data Management → View All
- Import or add master data first

## FAQ

**Q: Can I use this offline?**  
A: Yes! Use local MongoDB. No internet required.

**Q: How many users can access simultaneously?**  
A: Database dependent. MongoDB has no hard limit.

**Q: Can I customize dropdown values after initial setup?**  
A: Yes! Use the Dropdown Config page to add new values anytime.

**Q: Is the Excel file required after initial import?**  
A: No. After importing, all data is in the database. Excel is no longer needed.

**Q: Can I import additional master data later?**  
A: Yes, but you need to delete existing data first (import button is disabled once data exists).

**Q: How do I add more users?**  
A: Currently, register through the login page. Admin user management coming soon.

**Q: Can I backup my data?**  
A: Yes! Export reports to Excel for call logs. Use database backup tools for complete backups.

**Q: Is my data encrypted?**  
A: Passwords are hashed. For database encryption, use database-level encryption features.

## System Requirements

### Minimum Requirements
- **CPU**: Dual-core processor
- **RAM**: 4 GB
- **Storage**: 500 MB free space
- **OS**: Windows 10+, macOS 10.14+, Linux (Ubuntu 18.04+)
- **Browser**: Chrome, Firefox, Safari, Edge (latest versions)

### Recommended Requirements
- **CPU**: Quad-core processor
- **RAM**: 8 GB
- **Storage**: 2 GB free space
- **Database**: Dedicated server for MongoDB cluster

## Support & Contribution

### Getting Help
1. Check this README thoroughly
2. Review error messages carefully
3. Check database connection settings
4. Verify Excel file format

### Reporting Issues
When reporting issues, include:
- Python version: `python --version`
- Operating system
- Database type (MongoDB)
- Error message (full traceback)
- Steps to reproduce

### Future Enhancements
Potential improvements:
- [ ] Role-based access control (Admin/User)
- [ ] Advanced search and filtering
- [ ] Dashboard with analytics
- [ ] API endpoints for integration
- [ ] Mobile app companion
- [ ] Multi-language support
- [ ] Audit log tracking

## Version History

### Version 1.0.0 (Current)
- ✅ User authentication with registration and login
- ✅ Master data management (CRUD operations)
- ✅ Manual Excel import with duplicate detection
- ✅ Dropdown configuration page (database-driven)
- ✅ Call log entry with auto-fill
- ✅ Reports with date filtering
- ✅ Excel export functionality
- ✅ Email integration
- ✅ MongoDB support
- ✅ Streamlit Cloud deployment
- ✅ Standalone executable creation
- ✅ Auto-bootstrap reconnection

## Credits

**Developer**: Indranil Chatterjee  
**Version**: 1.0.0  
**Last Updated**: January 15, 2026  
**Built With**: Streamlit, Python, MongoDB

## License

This project is provided as-is for internal use.

---

**For questions or support, contact the development team.**