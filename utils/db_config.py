import os
from dotenv import load_dotenv

load_dotenv()

def get_db_connection():
    """
    MSSQL support has been removed from this project. If your code
    still calls this helper, switch to the MongoDB repository APIs.
    """
    raise RuntimeError(
        "MSSQL support removed. Use MongoDB repository (set DB_BACKEND=mongodb)."
    )
