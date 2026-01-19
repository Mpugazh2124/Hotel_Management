import mysql.connector
import os
from dotenv import load_dotenv

load_dotenv()
password = os.getenv("DB_PASSWORD")
def get_db_connection():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password= password
        database="hotel_management"
    )

