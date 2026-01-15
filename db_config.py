import os
from dotenv import load_dotenv

load_dotenv()

def get_db_connection():
    """Create and return MSSQL database connection"""
    try:
        import pyodbc  # type: ignore
    except ImportError as e:
        raise ImportError(
            "pyodbc is not available. If you want to use MSSQL on macOS, install unixODBC "
            "and an ODBC driver, e.g. `brew install unixodbc` and install Microsoft ODBC Driver. "
            "Alternatively set DB_BACKEND=mongodb to run without MSSQL."
        ) from e

    server = os.getenv('DB_SERVER', 'localhost')
    database = os.getenv('DB_NAME', 'CallLogDB')
    username = os.getenv('DB_USER', 'sa')
    password = os.getenv('DB_PASSWORD', '')
    driver = os.getenv('DB_DRIVER', '{ODBC Driver 17 for SQL Server}')
    
    connection_string = (
        f'DRIVER={driver};'
        f'SERVER={server};'
        f'DATABASE={database};'
        f'UID={username};'
        f'PWD={password};'
        'TrustServerCertificate=yes;'
    )
    
    try:
        conn = pyodbc.connect(connection_string)
        return conn
    except Exception as e:
        print(f"Error connecting to database: {e}")
        raise
