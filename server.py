import socket
import threading
import os

import sqlite3

# === Authentication ===
import bcrypt

# === User database setup ===
user_db = sqlite3.connect("chat_users.db", check_same_thread=False)
user_cur = user_db.cursor()
user_cur.execute("""
CREATE TABLE IF NOT EXISTS users (
    username TEXT PRIMARY KEY,
    password_hash BLOB NOT NULL
)
""")
user_db.commit()

def register_user(username: str, password: str) -> bool:
    """Hash password and insert new user. Return False if username exists."""
    pw_hash = bcrypt.hashpw(password.encode(), bcrypt.gensalt())
    try:
        user_cur.execute(
            "INSERT INTO users (username, password_hash) VALUES (?, ?)",
            (username, pw_hash)
        )
        user_db.commit()
        return True
    except sqlite3.IntegrityError:
        return False

def authenticate_user(username: str, password: str) -> bool:
    """Check given password against stored hash. Return True if match."""
    user_cur.execute(
        "SELECT password_hash FROM users WHERE username = ?", (username,)
    )
    row = user_cur.fetchone()
    if not row:
        return False
    stored_hash = row[0]
    return bcrypt.checkpw(password.encode(), stored_hash)


# === Database setup ===
from datetime import datetime

def log_message(username: str, text: str):
    """Insert a chat message into the SQLite history table."""
    timestamp = datetime.utcnow().isoformat()  # e.g. '2025-05-28T12:34:56.789'
    cursor.execute(
        "INSERT INTO messages (username, text, timestamp) VALUES (?, ?, ?)",
        (username, text, timestamp)
    )
    db.commit()

def get_last_messages(limit: int = 10):
    """Return the last `limit` messages as a list of (username, text, timestamp)."""
    cursor.execute(
        "SELECT username, text, timestamp "
        "FROM messages "
        "ORDER BY id DESC "
        "LIMIT ?",
        (limit,)
    )
    rows = cursor.fetchall()
    return rows[::-1]


db = sqlite3.connect("chat_history.db", check_same_thread=False)
cursor = db.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL,
    text     TEXT NOT NULL,
    timestamp TEXT NOT NULL
)
""")
db.commit()


clients = []


def admin_console():
    
    while True:
        cmd = input() 
        if cmd.strip().lower() == "terminate":
            print("[SERVER] Terminate command received. Shutting down.")
            os._exit(0) 

def handle_client(conn, addr):
    print(f"[NEW CONNECTION] {addr} connected.")

    # —– Authentication Phase —–
    conn.send(b"SYSTEM: Welcome! Use /register <user> <pass> or /login <user> <pass>\n")
    username = None
    while True:
        data = conn.recv(1024)
        if not data:
            conn.close()
            return
        parts = data.decode().strip().split()
        if len(parts) != 3 or parts[0] not in ("/register", "/login"):
            conn.send(b"SYSTEM: Invalid. Try /register or /login.\n")
            continue

        cmd, user, pwd = parts
        if cmd == "/register":
            if register_user(user, pwd):
                conn.send(f"SYSTEM: Registered {user}. Now /login.\n".encode())
            else:
                conn.send(f"SYSTEM: Username {user} taken.\n".encode())

        else:  # /login
            if authenticate_user(user, pwd):
                conn.send(f"SYSTEM: Login successful. Welcome {user}!\n".encode())
                username = user
                break
            else:
                conn.send(b"SYSTEM: Login failed.\n")

    # === Send recent history ===
    conn.send(b"SYSTEM: Last 10 messages:\n")
    for user, text, ts in get_last_messages(10):
        time_str = ts.split("T")[1][:8]
        conn.send(f"[{time_str}] {user}: {text}\n".encode())

    conn.send(b"SYSTEM: You can now chat. Type exit to quit.\n")

    while True:
        try:
            msg = conn.recv(1024)
            if not msg:
                break
            text = msg.decode().strip()
            print(f"[{addr}] {text}")

            log_message(str(addr), text)

            # Broadcast to other clients
            for client in clients:
                if client != conn:
                    client.send(msg)
        except:
            break

    print(f"[DISCONNECTED] {addr}")
    clients.remove(conn)
    conn.close()

def start_server(host='0.0.0.0', port=12345):
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind((host, port))
    server.listen()
    print(f"[LISTENING] Server running on {host}:{port}")

    # ←— Start admin console thread
    threading.Thread(target=admin_console, daemon=True).start()

    while True:
        conn, addr = server.accept()
        clients.append(conn)
        thread = threading.Thread(target=handle_client, args=(conn, addr))
        thread.start()

if __name__ == "__main__":
    start_server()
