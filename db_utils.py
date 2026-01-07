import sqlite3
import os
import logging
import streamlit as st

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- Configuration ---
try:
    DB_URL = os.environ.get("DATABASE_URL") or st.secrets.get("DATABASE_URL")
    # Fix for psycopg2: it prefers 'postgresql://' over 'postgres://'
    if DB_URL and DB_URL.startswith("postgres://"):
        DB_URL = DB_URL.replace("postgres://", "postgresql://", 1)
except (FileNotFoundError, Exception):
    DB_URL = os.environ.get("DATABASE_URL")

# Local SQLite fallback
DB_DIR = os.path.dirname(os.path.abspath(__file__))
SQLITE_PATH = os.path.join(DB_DIR, "portfolio.db")

def get_connection():
    """Tries to connect to PostgreSQL, falls back to SQLite if it fails."""
    if DB_URL:
        try:
            import psycopg2
            # We add a connection timeout to avoid hanging
            conn = psycopg2.connect(DB_URL, connect_timeout=5)
            return conn, True
        except Exception as e:
            logger.error(f"PostgreSQL connection failed: {e}. Falling back to SQLite.")
            # We store the error in session state to show it in the UI later
            if "db_error" not in st.session_state:
                st.session_state.db_error = str(e)
            return sqlite3.connect(SQLITE_PATH), False
    else:
        return sqlite3.connect(SQLITE_PATH), False

def init_db():
    """Initializes the database and ensures tables and columns exist."""
    conn, is_postgres = get_connection()
    placeholder = "%s" if is_postgres else "?"
    
    try:
        cursor = conn.cursor()
        
        # Create table logic
        auto_inc = "SERIAL" if is_postgres else "INTEGER PRIMARY KEY AUTOINCREMENT"
        cursor.execute(f"""
            CREATE TABLE IF NOT EXISTS holdings (
                id {auto_inc},
                symbol TEXT NOT NULL,
                quantity REAL NOT NULL,
                avg_cost REAL NOT NULL,
                purchase_date TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Migration/Column check
        if is_postgres:
            cursor.execute("SELECT column_name FROM information_schema.columns WHERE table_name='holdings'")
        else:
            cursor.execute("PRAGMA table_info(holdings)")
        
        columns = [row[0] if is_postgres else row[1] for row in cursor.fetchall()]
        
        if "purchase_date" not in columns:
            cursor.execute("ALTER TABLE holdings ADD COLUMN purchase_date TEXT")
            if is_postgres:
                cursor.execute("UPDATE holdings SET purchase_date = CAST(created_at AS DATE)::text WHERE purchase_date IS NULL")
            else:
                cursor.execute("UPDATE holdings SET purchase_date = date(created_at) WHERE purchase_date IS NULL")
        
        conn.commit()
    except Exception as e:
        logger.error(f"Database init error: {e}")
    finally:
        conn.close()

def add_holding(symbol, quantity, avg_cost, purchase_date):
    conn, is_postgres = get_connection()
    placeholder = "%s" if is_postgres else "?"
    try:
        cursor = conn.cursor()
        cursor.execute(
            f"INSERT INTO holdings (symbol, quantity, avg_cost, purchase_date) VALUES ({placeholder}, {placeholder}, {placeholder}, {placeholder})",
            (symbol, float(quantity), float(avg_cost), purchase_date)
        )
        conn.commit()
    finally:
        conn.close()

def update_holding(holding_id, symbol, quantity, avg_cost, purchase_date):
    """Updates an existing holding in the database."""
    conn, is_postgres = get_connection()
    placeholder = "%s" if is_postgres else "?"
    try:
        cursor = conn.cursor()
        cursor.execute(
            f"UPDATE holdings SET symbol = {placeholder}, quantity = {placeholder}, avg_cost = {placeholder}, purchase_date = {placeholder} WHERE id = {placeholder}",
            (symbol, float(quantity), float(avg_cost), purchase_date, holding_id)
        )
        conn.commit()
    finally:
        conn.close()

def delete_holding(holding_id):
    conn, is_postgres = get_connection()
    placeholder = "%s" if is_postgres else "?"
    try:
        cursor = conn.cursor()
        cursor.execute(f"DELETE FROM holdings WHERE id = {placeholder}", (holding_id,))
        conn.commit()
    finally:
        conn.close()

def get_holdings():
    holdings = []
    conn, is_postgres = get_connection()
    try:
        if is_postgres:
            from psycopg2.extras import RealDictCursor
            cursor = conn.cursor(cursor_factory=RealDictCursor)
        else:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
        cursor.execute("SELECT * FROM holdings ORDER BY created_at DESC")
        rows = cursor.fetchall()
        
        for row in rows:
            holdings.append({
                "id": row["id"],
                "symbol": row["symbol"],
                "qty": row["quantity"] if is_postgres else row["quantity"], # names might differ slightly in dict
                "avg_cost": row["avg_cost"],
                "purchase_date": row["purchase_date"]
            })
    except Exception as e:
        logger.error(f"Error fetching: {e}")
    finally:
        conn.close()
    return holdings

DB_NAME = "PostgreSQL (Cloud)" if DB_URL else SQLITE_PATH
