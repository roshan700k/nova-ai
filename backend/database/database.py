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

    conn.commit()
    conn.close()