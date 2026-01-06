import sqlite3
import os

DB_NAME = "portfolio.db"

def init_db():
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS holdings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                symbol TEXT NOT NULL,
                quantity REAL NOT NULL,
                avg_cost REAL NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.commit()

def add_holding(symbol, quantity, avg_cost):
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO holdings (symbol, quantity, avg_cost) VALUES (?, ?, ?)",
            (symbol, float(quantity), float(avg_cost))
        )
        conn.commit()

def delete_holding(holding_id):
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM holdings WHERE id = ?", (holding_id,))
        conn.commit()

def get_holdings():
    holdings = []
    try:
        with sqlite3.connect(DB_NAME) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM holdings ORDER BY created_at DESC")
            rows = cursor.fetchall()
            for row in rows:
                holdings.append({
                    "id": row["id"],
                    "symbol": row["symbol"],
                    "qty": row["quantity"],
                    "avg_cost": row["avg_cost"]
                })
    except Exception as e:
        print(f"Error fetching holdings: {e}")
        return []
        
    return holdings
