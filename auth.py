import sqlite3
import hashlib

DB = "users.db"


def init_users():
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE,
            password TEXT,
            role TEXT
        )
    """)
    conn.commit()
    conn.close()


def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()


def criar_usuario(username, password, role="USER"):
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute(
        "INSERT INTO users (username, password, role) VALUES (?, ?, ?)",
        (username, hash_password(password), role)
    )
    conn.commit()
    conn.close()


def autenticar(username, password):
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute(
        "SELECT role FROM users WHERE username=? AND password=?",
        (username, hash_password(password))
    )
    user = c.fetchone()
    conn.close()
    return user[0] if user else None
