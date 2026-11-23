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

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS user_settings(
        user_id INTEGER NOT NULL,
        key TEXT NOT NULL,
        value TEXT,
        PRIMARY KEY (user_id, key)
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS tasks(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        title TEXT NOT NULL,
        notes TEXT DEFAULT '',
        due TEXT DEFAULT '',
        done INTEGER DEFAULT 0,
        created_at TEXT DEFAULT (datetime('now'))
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS agent_devices(
        user_id INTEGER PRIMARY KEY,
        token TEXT NOT NULL,
        name TEXT DEFAULT 'My PC',
        last_seen TEXT,
        created_at TEXT DEFAULT (datetime('now'))
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS agent_commands(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        action TEXT NOT NULL,
        args TEXT DEFAULT '{}',
        status TEXT DEFAULT 'pending',
        result TEXT DEFAULT '',
        notified INTEGER DEFAULT 0,
        created_at TEXT DEFAULT (datetime('now')),
        finished_at TEXT
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


def delete_all_conversations(user_id):
    conn = connect()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM conversations WHERE user_id IS ?", (user_id,))
    conn.commit()
    conn.close()


# ---------- user settings ----------

def get_user_settings(user_id):
    conn = connect()
    cursor = conn.cursor()
    cursor.execute("SELECT key, value FROM user_settings WHERE user_id = ?", (user_id,))
    rows = cursor.fetchall()
    conn.close()
    return {r[0]: r[1] for r in rows}


def set_user_settings(user_id, settings: dict):
    conn = connect()
    cursor = conn.cursor()
    for key, value in settings.items():
        cursor.execute(
            "INSERT INTO user_settings (user_id, key, value) VALUES (?, ?, ?) "
            "ON CONFLICT(user_id, key) DO UPDATE SET value = excluded.value",
            (user_id, str(key)[:50], str(value)[:2000]),
        )
    conn.commit()
    conn.close()


# ---------- tasks ----------

def _task_row(r):
    return {"id": r[0], "title": r[1], "notes": r[2], "due": r[3], "done": bool(r[4]), "created_at": r[5]}


def list_tasks(user_id):
    conn = connect()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT id, title, notes, due, done, created_at FROM tasks "
        "WHERE user_id IS ? ORDER BY done ASC, created_at DESC LIMIT 200",
        (user_id,),
    )
    rows = cursor.fetchall()
    conn.close()
    return [_task_row(r) for r in rows]


def create_task(user_id, title, notes="", due=""):
    conn = connect()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO tasks (user_id, title, notes, due) VALUES (?, ?, ?, ?)",
        (user_id, title[:300], notes[:2000], due[:100]),
    )
    task_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return task_id


def update_task(task_id, user_id, fields: dict):
    allowed = {"title": 300, "notes": 2000, "due": 100}
    conn = connect()
    cursor = conn.cursor()
    for key, maxlen in allowed.items():
        if key in fields:
            cursor.execute(
                f"UPDATE tasks SET {key} = ? WHERE id = ? AND user_id IS ?",
                (str(fields[key])[:maxlen], task_id, user_id),
            )
    if "done" in fields:
        cursor.execute(
            "UPDATE tasks SET done = ? WHERE id = ? AND user_id IS ?",
            (1 if fields["done"] else 0, task_id, user_id),
        )
    conn.commit()
    conn.close()


def delete_task(task_id, user_id):
    conn = connect()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM tasks WHERE id = ? AND user_id IS ?", (task_id, user_id))
    conn.commit()
    conn.close()


# ---------- local agent (PC control) ----------

def get_device(user_id):
    conn = connect()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT user_id, token, name, last_seen FROM agent_devices WHERE user_id = ?",
        (user_id,),
    )
    r = cursor.fetchone()
    conn.close()
    if not r:
        return None
    return {"user_id": r[0], "token": r[1], "name": r[2], "last_seen": r[3]}


def register_device(user_id, name="My PC"):
    import secrets
    token = secrets.token_hex(24)
    conn = connect()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO agent_devices (user_id, token, name) VALUES (?, ?, ?) "
        "ON CONFLICT(user_id) DO UPDATE SET token = excluded.token, name = excluded.name",
        (user_id, token, name[:60]),
    )
    conn.commit()
    conn.close()
    return token


def device_by_token(token):
    conn = connect()
    cursor = conn.cursor()
    cursor.execute("SELECT user_id FROM agent_devices WHERE token = ?", (token,))
    r = cursor.fetchone()
    conn.close()
    return r[0] if r else None


def touch_device(user_id):
    conn = connect()
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE agent_devices SET last_seen = datetime('now') WHERE user_id = ?",
        (user_id,),
    )
    conn.commit()
    conn.close()


def enqueue_command(user_id, action, args=None):
    import json as _json
    conn = connect()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO agent_commands (user_id, action, args) VALUES (?, ?, ?)",
        (user_id, action[:40], _json.dumps(args or {})[:2000]),
    )
    cid = cursor.lastrowid
    conn.commit()
    conn.close()
    return cid


def pending_commands(user_id):
    """Return pending commands and mark them 'sent' so they aren't repeated."""
    import json as _json
    conn = connect()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT id, action, args FROM agent_commands "
        "WHERE user_id = ? AND status = 'pending' ORDER BY id LIMIT 10",
        (user_id,),
    )
    rows = cursor.fetchall()
    if rows:
        ids = [r[0] for r in rows]
        cursor.execute(
            f"UPDATE agent_commands SET status = 'sent' WHERE id IN ({','.join('?' * len(ids))})",
            ids,
        )
        conn.commit()
    conn.close()
    out = []
    for r in rows:
        try:
            args = _json.loads(r[2] or "{}")
        except Exception:
            args = {}
        out.append({"id": r[0], "action": r[1], "args": args})
    return out


def command_result(user_id, command_id, ok, output):
    conn = connect()
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE agent_commands SET status = ?, result = ?, finished_at = datetime('now') "
        "WHERE id = ? AND user_id = ?",
        ("done" if ok else "failed", str(output)[:4000], command_id, user_id),
    )
    conn.commit()
    conn.close()


def get_command(command_id, user_id):
    conn = connect()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT id, action, args, status, result, created_at FROM agent_commands "
        "WHERE id = ? AND user_id = ?",
        (command_id, user_id),
    )
    r = cursor.fetchone()
    conn.close()
    if not r:
        return None
    return {"id": r[0], "action": r[1], "args": r[2], "status": r[3],
            "result": r[4], "created_at": r[5]}


def unnotified_results(user_id):
    """Finished commands not yet surfaced to the user via notifications."""
    conn = connect()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT id, action, status, result FROM agent_commands "
        "WHERE user_id = ? AND status IN ('done','failed') AND notified = 0 "
        "ORDER BY id LIMIT 10",
        (user_id,),
    )
    rows = cursor.fetchall()
    if rows:
        ids = [r[0] for r in rows]
        cursor.execute(
            f"UPDATE agent_commands SET notified = 1 WHERE id IN ({','.join('?' * len(ids))})",
            ids,
        )
        conn.commit()
    conn.close()
    return [{"id": r[0], "action": r[1], "status": r[2], "result": r[3]} for r in rows]
