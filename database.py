import sqlite3
import os
import logging
import streamlit as st

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- Configuration ---
# To use PostgreSQL in the cloud:
# 1. Create a DB (Supabase, Neon, etc.)
# 2. Add DATABASE_URL to your Streamlit Secrets or Environment Variables
try:
    DB_URL = os.environ.get("DATABASE_URL") or st.secrets.get("DATABASE_URL")
except (FileNotFoundError, Exception):
    # Fallback if st.secrets is not initialized or file not found
    DB_URL = os.environ.get("DATABASE_URL")

# Local SQLite fallback
DB_DIR = os.path.dirname(os.path.abspath(__file__))
SQLITE_PATH = os.path.join(DB_DIR, "portfolio.db")

def get_connection():
    if DB_URL:
        import psycopg2
        return psycopg2.connect(DB_URL)
    else:
        return sqlite3.connect(SQLITE_PATH)

def init_db():
    """Initializes the database and ensures tables and columns exist."""
    is_postgres = DB_URL is not None
    param_style = "%s" if is_postgres else "?"
    
    logger.info(f"Initializing database. Mode: {'PostgreSQL' if is_postgres else 'SQLite'}")
    
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            
            # Create table
            auto_inc = "SERIAL" if is_postgres else "INTEGER PRIMARY KEY AUTOINCREMENT"
            pk_stmt = f"id {auto_inc}" if is_postgres else f"id INTEGER PRIMARY KEY AUTOINCREMENT"
            
            cursor.execute(f"""
                CREATE TABLE IF NOT EXISTS holdings (
                    id {auto_inc if is_postgres else 'INTEGER PRIMARY KEY AUTOINCREMENT'},
                    symbol TEXT NOT NULL,
                    quantity REAL NOT NULL,
                    avg_cost REAL NOT NULL,
                    purchase_date TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Migration/Column check
            if is_postgres:
                # Postgres check
                cursor.execute("SELECT column_name FROM information_schema.columns WHERE table_name='holdings'")
            else:
                # SQLite check
                cursor.execute("PRAGMA table_info(holdings)")
            
            columns = [row[0] if is_postgres else row[1] for row in cursor.fetchall()]
            
            if "purchase_date" not in columns:
                logger.info("Migrating database: adding purchase_date column")
                cursor.execute("ALTER TABLE holdings ADD COLUMN purchase_date TEXT")
                if is_postgres:
                    cursor.execute("UPDATE holdings SET purchase_date = CAST(created_at AS DATE)::text WHERE purchase_date IS NULL")
                else:
                    cursor.execute("UPDATE holdings SET purchase_date = date(created_at) WHERE purchase_date IS NULL")
            
            conn.commit()
            logger.info("Database initialized successfully.")
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        # If it's a module not found error for psycopg2, remind the user
        if "psycopg2" in str(e):
            logger.error("Make sure 'psycopg2-binary' is installed for PostgreSQL support.")
        raise

def add_holding(symbol, quantity, avg_cost, purchase_date):
    """Adds a new holding to the database."""
    is_postgres = DB_URL is not None
    placeholder = "%s" if is_postgres else "?"
    
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                f"INSERT INTO holdings (symbol, quantity, avg_cost, purchase_date) VALUES ({placeholder}, {placeholder}, {placeholder}, {placeholder})",
                (symbol, float(quantity), float(avg_cost), purchase_date)
            )
            conn.commit()
            logger.info(f"Added holding for {symbol}")
    except Exception as e:
        logger.error(f"Error adding holding: {e}")
        raise

def delete_holding(holding_id):
    """Deletes a holding from the database."""
    is_postgres = DB_URL is not None
    placeholder = "%s" if is_postgres else "?"
    
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(f"DELETE FROM holdings WHERE id = {placeholder}", (holding_id,))
            conn.commit()
            logger.info(f"Deleted holding ID: {holding_id}")
    except Exception as e:
        logger.error(f"Error deleting holding: {e}")
        raise

def get_holdings():
    """Retrieves all holdings from the database."""
    holdings = []
    is_postgres = DB_URL is not None
    
    try:
        # For SQLite, check if file exists
        if not is_postgres and not os.path.exists(SQLITE_PATH):
            return []
            
        with get_connection() as conn:
            # Postgres cursor doesn't have row_factory like sqlite3, but we can use DictCursor
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
                    "qty": row["quantity"],
                    "avg_cost": row["avg_cost"],
                    "purchase_date": row["purchase_date"]
                })
    except Exception as e:
        logger.error(f"Error fetching holdings: {e}")
        return []
        
    return holdings

# For backwards compatibility with the debug footer
DB_NAME = "PostgreSQL (Cloud)" if DB_URL else SQLITE_PATH
