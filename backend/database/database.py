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

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS conversations(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        title TEXT DEFAULT 'New chat',
        pinned INTEGER DEFAULT 0,
        created_at TEXT DEFAULT (datetime('now')),
        updated_at TEXT DEFAULT (datetime('now'))
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS messages(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        conversation_id INTEGER NOT NULL,
        sender TEXT NOT NULL,
        text TEXT NOT NULL,
        created_at TEXT DEFAULT (datetime('now')),
        FOREIGN KEY (conversation_id) REFERENCES conversations(id)
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


# ---------- conversations ----------

def create_conversation(user_id):
    conn = connect()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO conversations (user_id) VALUES (?)", (user_id,))
    conv_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return conv_id


def list_conversations(user_id):
    conn = connect()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT id, title, pinned, updated_at FROM conversations "
        "WHERE user_id IS ? OR user_id = ? ORDER BY pinned DESC, updated_at DESC LIMIT 100",
        (user_id, user_id),
    )
    rows = cursor.fetchall()
    conn.close()
    return [
        {"id": r[0], "title": r[1], "pinned": bool(r[2]), "updated_at": r[3]}
        for r in rows
    ]


def get_conversation(conv_id, user_id):
    conn = connect()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT id, user_id, title, pinned FROM conversations WHERE id = ?",
        (conv_id,),
    )
    row = cursor.fetchone()
    conn.close()
    if not row:
        return None
    # owner check: guest chats (NULL user_id) only visible to guests
    if row[1] != user_id:
        return None
    return {"id": row[0], "user_id": row[1], "title": row[2], "pinned": bool(row[3])}


def get_messages(conv_id):
    conn = connect()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT sender, text FROM messages WHERE conversation_id = ? ORDER BY id",
        (conv_id,),
    )
    rows = cursor.fetchall()
    conn.close()
    return [{"sender": "You" if r[0] == "user" else "NOVA", "text": r[1]} for r in rows]


def add_message(conv_id, sender, text):
    conn = connect()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO messages (conversation_id, sender, text) VALUES (?, ?, ?)",
        (conv_id, sender, text),
    )
    cursor.execute(
        "UPDATE conversations SET updated_at = datetime('now') WHERE id = ?",
        (conv_id,),
    )
    conn.commit()
    conn.close()


def set_conversation_title(conv_id, title):
    conn = connect()
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE conversations SET title = ? WHERE id = ? AND title = 'New chat'",
        (title, conv_id),
    )
    conn.commit()
    conn.close()


def set_conversation_pinned(conv_id, user_id, pinned):
    conn = connect()
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE conversations SET pinned = ? WHERE id = ? AND user_id IS ?",
        (1 if pinned else 0, conv_id, user_id),
    )
    conn.commit()
    conn.close()


def delete_conversation(conv_id, user_id):
    conn = connect()
    cursor = conn.cursor()
    cursor.execute(
        "DELETE FROM conversations WHERE id = ? AND user_id IS ?",
        (conv_id, user_id),
    )
    conn.commit()
    conn.close()
