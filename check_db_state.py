import sqlite3
import os

DB_DIR = r"c:\Users\d98691\Desktop\Zabbix\Finanzas"
DB_NAME = os.path.join(DB_DIR, "portfolio.db")

def check_db():
    if not os.path.exists(DB_NAME):
        print(f"Database {DB_NAME} does not exist.")
        return
    
    print(f"Checking database at {DB_NAME}")
    try:
        with sqlite3.connect(DB_NAME) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
            tables = cursor.fetchall()
            print(f"Tables: {[t['name'] for t in tables]}")
            
            for table in tables:
                tname = table['name']
                cursor.execute(f"SELECT COUNT(*) as count FROM {tname}")
                count = cursor.fetchone()['count']
                print(f"Table {tname} has {count} rows.")
                
                if count > 0:
                    cursor.execute(f"SELECT * FROM {tname} LIMIT 5")
                    rows = cursor.fetchall()
                    for row in rows:
                        print(dict(row))
    except Exception as e:
        print(f"Error checking DB: {e}")

if __name__ == "__main__":
    check_db()
