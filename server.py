import socket
import threading
import os
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError
from pymongo import MongoClient, errors
from datetime import datetime
import base64

# ——— DatabaseManager —————————————————————————————
class DatabaseManager:
    def __init__(self, mongo_uri="mongodb://localhost:27017", db_name="chat_app"):

        try:
            # Short timeout so failures surface quickly
            self.client = MongoClient(mongo_uri, serverSelectionTimeoutMS=5000)
            # Force a round-trip to the server
            self.client.admin.command("ping")
            print("[DB] Connected to MongoDB!")
        except errors.ServerSelectionTimeoutError as e:
            print(f"[DB] ERROR: Could not connect to MongoDB at {mongo_uri}")
            print(f"[DB] Details: {e}")
            raise  # or sys.exit(1)

        self.db = self.client[db_name]
        self.users = self.db["users"]
        self.messages = self.db["messages"]

        self.users.create_index("username", unique=True)
        self.messages.create_index([("from", 1), ("to", 1), ("timestamp", 1)])

    def add_user(self, username, password_hash, public_key_bytes = None):
        try:
            self.users.insert_one({
                "username": username,
                "password_hash": password_hash,
                "public_key": public_key_bytes, 
                "created_at": datetime.utcnow().isoformat(),
            })
            return True
        except errors.DuplicateKeyError:
            return False

    def get_password_hash(self, username):
        user = self.users.find_one({"username": username})
        return user["password_hash"] if user else None
    
    def store_public_key(self, username: str, public_key_b64: str) -> bool:
        """
        Update the given user’s document to set their Base64 public_key.
        Returns True if update succeeded.
        """
        result = self.users.update_one(
            {"username": username},
            {"$set": {"public_key": public_key_b64}}
        )
        return result.matched_count == 1

    def get_public_key(self, username) -> bytes:
        """Fetch the user’s public key bytes (or None)."""
        doc = self.users.find_one({"username": username}, {"public_key": 1})
        if doc and "public_key" in doc:
            return base64.b64decode(doc["public_key"])
        return None
    
    def save_message(self, from_user, to_user, text):
        self.messages.insert_one({
            "from": from_user,
            "to": to_user,
            "text": text,
            "timestamp": datetime.utcnow().isoformat()
        })

    def get_messages_between(self, user1, user2, limit=50):
        query = {
            "$or": [
                {"from": user1, "to": user2},
                {"from": user2, "to": user1}
            ]
        }
        return list(
            self.messages.find(query).sort("timestamp", -1).limit(limit)
        )

# ——— AuthManager —————————————————————————————————
class AuthManager:
    def __init__(
        self,
        db_manager,
        pepper: bytes,
        time_cost: int = 2,
        memory_cost: int = 64 * 1024,
        parallelism: int = 4,
        salt_len: int = 16,
        hash_len: int = 32,
    ):
        self.db = db_manager
        self.pepper = pepper
        self.ph = PasswordHasher(
            time_cost=time_cost,
            memory_cost=memory_cost,
            parallelism=parallelism,
            salt_len=salt_len,
            hash_len=hash_len,
        )

    def hash_password(self, password: str) -> str:
        secret = self.pepper + password.encode('utf-8')
        return self.ph.hash(secret)

    def needs_rehash(self, stored_hash: str) -> bool:
        return self.ph.check_needs_rehash(stored_hash)

    def register_user(self, username: str, password: str) -> bool:
        pwd_hash = self.hash_password(password)
        return self.db.add_user(username, pwd_hash)

    def authenticate_user(self, username: str, password: str) -> bool:
        stored_hash = self.db.get_password_hash(username)
        if not stored_hash:
            return False
        secret = self.pepper + password.encode('utf-8')
        try:
            return self.ph.verify(stored_hash, secret)
        except VerifyMismatchError:
            return False

# ——— ChatUser —————————————————————————————————
class ChatUser:
    def __init__(self, conn, addr, clients_dict, auth_manager, db_manager):
        self.conn = conn
        self.addr = addr
        self.clients = clients_dict
        self.auth = auth_manager
        self.db = db_manager
        self.username = None
        self.alive = True

    def send(self, msg: str):
        self.conn.send(msg.encode('utf-8'))

    def recv(self) -> str:
        data = self.conn.recv(1024)
        return data.decode('utf-8').strip() if data else ''

    def log_message(self, to_user, text):
        self.db.save_message(self.username, to_user, text)

    def handle_auth(self):
        self.send("SYSTEM: Welcome! Use /register <user> <pass> or /login <user> <pass>\n")
        while self.alive and not self.username:
            line = self.recv()
            if not line:
                self.alive = False
                return

            if line.startswith("/storekey "):
                parts = line.split(" ", 2)
                if len(parts) == 3:
                    _, user, pub_b64 = parts
                    if self.db.store_public_key(user, pub_b64):
                        self.send("SYSTEM: Public key stored.\n")
                    else:
                        self.send("SYSTEM: Failed to store public key.\n")
                else:
                    self.send("SYSTEM: Usage: /storekey <user> <pubkey>\n")
                continue

            parts = line.split()
            if len(parts) != 3 or parts[0] not in ("/register", "/login"):
                self.send("SYSTEM: Invalid. Try /register or /login.\n")
                continue

            cmd, user, pwd = parts
            if cmd == "/register":
                success = self.auth.register_user(user, pwd)
                if success:
                    self.send(f"SYSTEM: Registered {user}. Now /login.\n")
                else:
                    self.send(f"SYSTEM: Username {user} already taken.\n")
            else:  # login
                success = self.auth.authenticate_user(user, pwd)
                if success:
                    self.username = user
                    self.clients[self.conn] = user
                    self.send(f"SYSTEM: Login successful. Welcome {user}!\n")
                else:
                    self.send("SYSTEM: Login failed.\n")

    def handle_chat(self):
        self.send("SYSTEM: You can now chat. Type /exit to quit.\n")
        while self.alive:
            msg = self.recv()
            if not msg or msg.lower() == "/exit":
                break
            
            if msg == "/who":
                online = ", ".join(self.clients.values())
                self.send(f"SYSTEM: Online: {online}\n")
                continue

            if msg.startswith("@"):
                try:
                    target, private = msg[1:].split(" ", 1)
                except ValueError:
                    self.send("SYSTEM: Usage: @username message\n")
                    self.send(f"Debug: {msg}")
                    continue

                target_conn = next((c for c, u in self.clients.items() if u == target), None)
                if target_conn:
                    target_conn.send(f"[PM from {self.username}] {private}\n".encode())
                    self.log_message(target, private)

                else:
                    self.send(f"SYSTEM: {target} not online.\n")
                continue

            # Future: broadcast to all
            self.send(f"[You] {msg}\n")

    def cleanup(self):
        if self.conn in self.clients:
            del self.clients[self.conn]
        self.conn.close()
        self.alive = False
        print(f"[DISCONNECTED] {self.addr}")

    def run(self):
        print(f"[NEW CONNECTION] {self.addr}")
        try:
            self.handle_auth()
            if self.username:
                self.handle_chat()
        except Exception as e:
            print(f"[ERROR] {self.addr} → {e}")
        finally:
            self.cleanup()


# ——— Admin console —————————————————————————————
def admin_console(clients_dict, db_manager):
    while True:
        cmd = input().strip()
        if cmd == "/terminate":
            print("[SERVER] Shutting down.")
            os._exit(0)
        elif cmd == "/getClient":
            for conn, user in clients_dict.items():
                print(f"{user} @ {conn.getpeername()}")
        elif cmd == "/clear":
            db_manager.users.delete_many({})
            db_manager.messages.delete_many({})
            print("[DB] Cleared all users and messages.")


# ——— Server bootstrap —————————————————————————————
def start_server(host='0.0.0.0', port=12345):
    dbm = DatabaseManager()
    pepper = os.environ.get("APP_PEPPER", "changeme").encode('utf-8')
    auth = AuthManager(dbm, pepper)

    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind((host, port))
    server.listen()
    print(f"[LISTENING] {host}:{port}")

    clients = {}
    threading.Thread(target=admin_console, args=(clients,dbm), daemon=True).start()

    while True:
        conn, addr = server.accept()
        session = ChatUser(conn, addr, clients, auth, dbm)
        threading.Thread(target=session.run, daemon=True).start()

if __name__ == "__main__":
    start_server()
