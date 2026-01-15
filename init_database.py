"""
Initialize database and create tables
"""
import pandas as pd
import os

from dotenv import load_dotenv

from db_config import get_db_connection
from storage import get_repository

def create_tables():
    """Create Master and CallLogEntries tables"""
    load_dotenv()
    backend = (os.getenv("DB_BACKEND") or "mssql").strip().lower()
    if backend in {"mongodb", "mongo"}:
        # MongoDB is schema-less; indexes are created in repository init.
        get_repository()
        print("MongoDB backend selected: collections/indexes ready (no SQL tables to create).")
        return

    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Create Master table
        cursor.execute("""
            IF NOT EXISTS (SELECT * FROM sys.objects WHERE object_id = OBJECT_ID(N'[dbo].[Master]') AND type in (N'U'))
            CREATE TABLE [dbo].[Master] (
                [SrNo] INT IDENTITY(1,1) PRIMARY KEY,
                [MobileNo] NVARCHAR(20) NOT NULL UNIQUE,
                [Project] NVARCHAR(100),
                [TownType] NVARCHAR(50),
                [Requester] NVARCHAR(100),
                [RDCode] NVARCHAR(50),
                [RDName] NVARCHAR(200),
                [Town] NVARCHAR(100),
                [State] NVARCHAR(50),
                [Designation] NVARCHAR(100),
                [Name] NVARCHAR(200),
                [GSTNo] NVARCHAR(50),
                [EmailID] NVARCHAR(200),
                [CreatedDate] DATETIME DEFAULT GETDATE(),
                [UpdatedDate] DATETIME DEFAULT GETDATE()
            )
        """)
        
        # Create CallLogEntries table
        cursor.execute("""
            IF NOT EXISTS (SELECT * FROM sys.objects WHERE object_id = OBJECT_ID(N'[dbo].[CallLogEntries]') AND type in (N'U'))
            CREATE TABLE [dbo].[CallLogEntries] (
                [SrNo] INT IDENTITY(1,1) PRIMARY KEY,
                [Date] DATETIME DEFAULT GETDATE(),
                [MobileNo] NVARCHAR(20) NOT NULL,
                [Project] NVARCHAR(100),
                [Town] NVARCHAR(100),
                [Requester] NVARCHAR(100),
                [RDCode] NVARCHAR(50),
                [RDName] NVARCHAR(200),
                [State] NVARCHAR(50),
                [Designation] NVARCHAR(100),
                [Name] NVARCHAR(200),
                [Module] NVARCHAR(100),
                [Issue] NVARCHAR(500),
                [Solution] NVARCHAR(500),
                [SolvedOn] NVARCHAR(100),
                [CallOn] NVARCHAR(100),
                [Type] NVARCHAR(100),
                [CreatedDate] DATETIME DEFAULT GETDATE(),
                [UpdatedDate] DATETIME DEFAULT GETDATE()
            )
        """)
        
        conn.commit()
        print("Tables created successfully!")
        
    except Exception as e:
        print(f"Error creating tables: {e}")
        conn.rollback()
        raise
    finally:
        cursor.close()
        conn.close()

def import_master_data(repo=None):
    """Import data from Master sheet into database
    
    Returns:
        dict: Import statistics with keys 'imported', 'duplicates', 'duplicate_numbers'
    """
    if repo is None:
        repo = get_repository()

    try:
        # Read Master sheet (header is at row 1, so skip first row)
        df = pd.read_excel('Verma R Master.xlsx', sheet_name='Master', header=1)
        
        # Clean column names - remove 'Unnamed:' prefix and use proper names
        df.columns = ['SrNo', 'MobileNo', 'Project', 'TownType', 'Requester', 'RDCode', 
                      'RDName', 'Town', 'State', 'Designation', 'Name', 'GSTNo', 'EmailID']
        
        # Remove rows where MobileNo is NaN or header row
        df = df[df['MobileNo'].notna()]
        df = df[df['MobileNo'] != 'Mobile No']
        
        # Convert MobileNo to string
        df['MobileNo'] = df['MobileNo'].astype(str).str.strip()
        
        # Remove duplicates - keep first occurrence of each mobile number
        initial_count = len(df)
        # Find duplicate mobile numbers before removing
        duplicate_mask = df.duplicated(subset=['MobileNo'], keep='first')
        duplicate_numbers = df[duplicate_mask]['MobileNo'].tolist()
        
        df = df.drop_duplicates(subset=['MobileNo'], keep='first')
        duplicates_removed = initial_count - len(df)
        if duplicates_removed > 0:
            print(f"Removed {duplicates_removed} duplicate mobile numbers from Excel data")

        records = []
        for _, row in df.iterrows():
            records.append(
                {
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
                }
            )

        inserted = repo.master_replace_all(records)
        print(f"Imported {inserted} records into Master storage")
        
        return {
            'imported': inserted,
            'duplicates': duplicates_removed,
            'duplicate_numbers': duplicate_numbers
        }
        
    except Exception as e:
        print(f"Error importing master data: {e}")
        raise

if __name__ == '__main__':
    print("Creating tables...")
    create_tables()
    print("\nImporting master data...")
    import_master_data()
    print("\nDatabase initialization complete!")
