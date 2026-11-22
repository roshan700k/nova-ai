import sqlite3

DATABASE = "astra.db"


def connect():
    return sqlite3.connect(DATABASE)


def create_table():

    conn = connect()

    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS memory(
        key TEXT PRIMARY KEY,
        value TEXT
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        email TEXT UNIQUE,
        name TEXT,
        provider TEXT,
        created_at TEXT DEFAULT (datetime('now'))
    )
    """)

    conn.commit()
    conn.close()


def upsert_user(email: str, name: str, provider: str):
    conn = connect()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO users (email, name, provider) VALUES (?, ?, ?) "
        "ON CONFLICT(email) DO UPDATE SET name=excluded.name",
        (email, name, provider),
    )
    conn.commit()
    cursor.execute("SELECT id, email, name, provider FROM users WHERE email = ?", (email,))
    row = cursor.fetchone()
    conn.close()
    if row:
        return {"id": row[0], "email": row[1], "name": row[2], "provider": row[3]}
    return None


def get_user_by_id(user_id: int):
    conn = connect()
    cursor = conn.cursor()
    cursor.execute("SELECT id, email, name, provider FROM users WHERE id = ?", (user_id,))
    row = cursor.fetchone()
    conn.close()
    if row:
        return {"id": row[0], "email": row[1], "name": row[2], "provider": row[3]}
    return None
