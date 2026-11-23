import os
import sqlite3

# Use env var for database path (for deployment), fallback to local
DATABASE = os.environ.get("ASTRA_DB_PATH", "astra.db")


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
        role TEXT DEFAULT 'user',
        is_active INTEGER DEFAULT 1,
        created_at TEXT DEFAULT (datetime('now'))
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS features(
        name TEXT PRIMARY KEY,
        enabled INTEGER DEFAULT 1,
        description TEXT DEFAULT ''
    )
    """)

    # Migrate existing users table if needed
    try:
        cursor.execute("ALTER TABLE users ADD COLUMN role TEXT DEFAULT 'user'")
    except:
        pass
    try:
        cursor.execute("ALTER TABLE users ADD COLUMN is_active INTEGER DEFAULT 1")
    except:
        pass

    conn.commit()
    conn.close()


def upsert_user(email: str, name: str, provider: str, role: str = "user"):
    conn = connect()
    cursor = conn.cursor()
    # Bootstrap admin: OWNER_EMAIL env wins; otherwise first user becomes admin (dev only)
    owner_email = os.environ.get("OWNER_EMAIL", "").strip().lower()
    if owner_email and email.strip().lower() == owner_email:
        role = "admin"
    elif not owner_email:
        existing_admin = cursor.execute("SELECT COUNT(*) FROM users WHERE role = 'admin'").fetchone()[0]
        if existing_admin == 0:
            role = "admin"
    cursor.execute(
        "INSERT INTO users (email, name, provider, role) VALUES (?, ?, ?, ?) "
        "ON CONFLICT(email) DO UPDATE SET name=excluded.name",
        (email, name, provider, role),
    )
    conn.commit()
    cursor.execute("SELECT id, email, name, provider, role, is_active FROM users WHERE email = ?", (email,))
    row = cursor.fetchone()
    conn.close()
    if row:
        return {"id": row[0], "email": row[1], "name": row[2], "provider": row[3], "role": row[4], "is_active": row[5]}
    return None


def get_user_by_id(user_id: int):
    conn = connect()
    cursor = conn.cursor()
    cursor.execute("SELECT id, email, name, provider, role, is_active FROM users WHERE id = ?", (user_id,))
    row = cursor.fetchone()
    conn.close()
    if row:
        return {"id": row[0], "email": row[1], "name": row[2], "provider": row[3], "role": row[4], "is_active": row[5]}
    return None
