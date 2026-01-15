"""
MSSQL Database Initialization
Automatically creates all required tables for the Call Log Application
"""
from db_config import get_db_connection


def init_mssql_database() -> tuple[bool, str]:
    """
    Initialize MSSQL database with all required tables.
    Creates tables if they don't exist.
    Returns: (success: bool, message: str)
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # SQL scripts for table creation
        tables_sql = [
            # Master Table
            """
            IF NOT EXISTS (SELECT * FROM sys.objects WHERE object_id = OBJECT_ID(N'[dbo].[Master]') AND type in (N'U'))
            BEGIN
                CREATE TABLE [dbo].[Master] (
                    [SrNo] INT IDENTITY(1,1) PRIMARY KEY,
                    [MobileNo] NVARCHAR(20) NOT NULL UNIQUE,
                    [Project] NVARCHAR(200),
                    [TownType] NVARCHAR(100),
                    [Requester] NVARCHAR(200),
                    [RDCode] NVARCHAR(50),
                    [RDName] NVARCHAR(200),
                    [Town] NVARCHAR(200),
                    [State] NVARCHAR(100),
                    [Designation] NVARCHAR(200),
                    [Name] NVARCHAR(200),
                    [GSTNo] NVARCHAR(50),
                    [EmailID] NVARCHAR(200),
                    [CreatedDate] DATETIME2 DEFAULT GETDATE(),
                    [UpdatedDate] DATETIME2 DEFAULT GETDATE()
                )
            END
            """,
            
            # CallLogEntries Table
            """
            IF NOT EXISTS (SELECT * FROM sys.objects WHERE object_id = OBJECT_ID(N'[dbo].[CallLogEntries]') AND type in (N'U'))
            BEGIN
                CREATE TABLE [dbo].[CallLogEntries] (
                    [SrNo] INT IDENTITY(1,1) PRIMARY KEY,
                    [Date] DATETIME2 NOT NULL,
                    [MobileNo] NVARCHAR(20),
                    [Project] NVARCHAR(200),
                    [Town] NVARCHAR(200),
                    [Requester] NVARCHAR(200),
                    [RDCode] NVARCHAR(50),
                    [RDName] NVARCHAR(200),
                    [State] NVARCHAR(100),
                    [Designation] NVARCHAR(200),
                    [Name] NVARCHAR(200),
                    [Module] NVARCHAR(200),
                    [Issue] NVARCHAR(MAX),
                    [Solution] NVARCHAR(MAX),
                    [SolvedOn] NVARCHAR(200),
                    [CallOn] NVARCHAR(200),
                    [Type] NVARCHAR(100),
                    [CreatedDate] DATETIME2 DEFAULT GETDATE(),
                    [UpdatedDate] DATETIME2 DEFAULT GETDATE()
                )
            END
            """,
            
            # Users Table
            """
            IF NOT EXISTS (SELECT * FROM sys.objects WHERE object_id = OBJECT_ID(N'[dbo].[Users]') AND type in (N'U'))
            BEGIN
                CREATE TABLE [dbo].[Users] (
                    [UserId] INT IDENTITY(1,1) PRIMARY KEY,
                    [Username] NVARCHAR(100) NOT NULL UNIQUE,
                    [Password] NVARCHAR(256) NOT NULL,
                    [CreatedDate] DATETIME2 DEFAULT GETDATE(),
                    [UpdatedDate] DATETIME2 NULL
                )
            END
            """,
            
            # AppConfig Table
            """
            IF NOT EXISTS (SELECT * FROM sys.objects WHERE object_id = OBJECT_ID(N'[dbo].[AppConfig]') AND type in (N'U'))
            BEGIN
                CREATE TABLE [dbo].[AppConfig] (
                    [Id] INT IDENTITY(1,1) PRIMARY KEY,
                    [ConfigKey] NVARCHAR(100) NOT NULL UNIQUE,
                    [ConfigValue] NVARCHAR(MAX) NOT NULL,
                    [CreatedDate] DATETIME2 DEFAULT GETDATE(),
                    [UpdatedDate] DATETIME2 DEFAULT GETDATE()
                )
            END
            """,
            
            # EmailConfig Table
            """
            IF NOT EXISTS (SELECT * FROM sys.objects WHERE object_id = OBJECT_ID(N'[dbo].[EmailConfig]') AND type in (N'U'))
            BEGIN
                CREATE TABLE [dbo].[EmailConfig] (
                    [ConfigId] INT PRIMARY KEY,
                    [SmtpServer] NVARCHAR(200) NOT NULL,
                    [SmtpPort] INT NOT NULL,
                    [SmtpUser] NVARCHAR(200) NOT NULL,
                    [SmtpPassword] NVARCHAR(500) NOT NULL,
                    [CreatedDate] DATETIME2 DEFAULT GETDATE(),
                    [UpdatedDate] DATETIME2 DEFAULT GETDATE()
                )
            END
            """,
            
            # Create indexes
            """
            IF NOT EXISTS (SELECT * FROM sys.indexes WHERE name = 'IX_Master_MobileNo' AND object_id = OBJECT_ID('[dbo].[Master]'))
            BEGIN
                CREATE NONCLUSTERED INDEX [IX_Master_MobileNo] ON [dbo].[Master] ([MobileNo])
            END
            """,
            
            """
            IF NOT EXISTS (SELECT * FROM sys.indexes WHERE name = 'IX_CallLogEntries_Date' AND object_id = OBJECT_ID('[dbo].[CallLogEntries]'))
            BEGIN
                CREATE NONCLUSTERED INDEX [IX_CallLogEntries_Date] ON [dbo].[CallLogEntries] ([Date])
            END
            """,
            
            """
            IF NOT EXISTS (SELECT * FROM sys.indexes WHERE name = 'IX_Users_Username' AND object_id = OBJECT_ID('[dbo].[Users]'))
            BEGIN
                CREATE NONCLUSTERED INDEX [IX_Users_Username] ON [dbo].[Users] ([Username])
            END
            """
        ]
        
        # Execute each table creation script
        for sql in tables_sql:
            cursor.execute(sql)
        
        conn.commit()
        cursor.close()
        conn.close()
        
        return True, "✅ All database tables created successfully!"
        
    except Exception as e:
        return False, f"❌ Error creating tables: {str(e)}"
