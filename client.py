import base64
import socket
import threading
from encryption import E2E
import os
from nacl.public import PrivateKey
from server import DatabaseManager

def ensure_keypair(username: str):

    base_folder = os.path.expanduser("~/.fastchat")
    user_folder = os.path.join(base_folder, username)
    os.makedirs(user_folder, exist_ok=True)

    private_path = os.path.join(user_folder, "private_key.bin")
    public_path  = os.path.join(user_folder, "public_key.b64")

    if os.path.isfile(private_path) and os.path.isfile(public_path):
        with open(private_path, "rb") as pf:
            priv_bytes = pf.read()
        with open(public_path, "r") as uf:
            pub_b64 = uf.read().strip()
        return priv_bytes, pub_b64

    keypair = PrivateKey.generate()
    priv_bytes = bytes(keypair)
    pub_b64    = base64.b64encode(bytes(keypair.public_key)).decode("ascii")

    with open(private_path, "wb") as pf:
        pf.write(priv_bytes)
    os.chmod(private_path, 0o600)
    with open(public_path, "w") as uf:
        uf.write(pub_b64)

    return priv_bytes, pub_b64

def receive_messages(sock, state, client, db):
    while True:
        try:
            msg = sock.recv(1024).decode()
            if msg:
                prefix = "[PM from "
                if msg.startswith(prefix):
                    
                    header, payload_b64 = msg.split("] ", 1)
                    header += "]"
                    sender = header[len(prefix):-1]
                    ciphertext = base64.b64decode(payload_b64)
                    plaintext_bytes = state['e2e'].decrypt(sender, ciphertext)
                    plaintext = plaintext_bytes.decode('utf-8')

                    print(f"\n{header} {plaintext}")
                    continue
                
                else:
                    print(f"\n{msg}", end="")

                if "SYSTEM: Registered" in msg and state.get('temp_user'):
                    sk_bytes, pk_b64 = ensure_keypair(state['temp_user'])
                    client.send(f"/storekey {state['temp_user']} {pk_b64}".encode())
                    ack = client.recv(1024).decode()
                    print(ack)
                
                elif msg.startswith("SYSTEM: Login successful. Welcome ") and state.get('user'):
                    sk_bytes, _ = ensure_keypair(state['user'])
                    state['e2e'] = E2E(sk_bytes, db)
                    print(f"[DEBUG] E2E initialized for {state['user']}")

        except:
            break

def start_client(server_ip='127.0.0.1', server_port=12345):
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client.connect((server_ip, server_port))

    print(f"Connected to chat server at {server_ip}:{server_port}")
    db = DatabaseManager()

    state = {
        'temp_user': None,
        'user': None,
        'e2e': None, 
    }
    threading.Thread(
        target=receive_messages,
        args=(client, state, client, db),
        daemon=True
    ).start()

    while True:
        msg = input()
        if msg and msg[0] == "/":
            if msg.lower() == "/exit":
                break
            else:
                if msg.startswith("/register"):
                    parts = msg.split()
                    if len(parts) >= 2:
                        state['temp_user'] = parts[1]
                
                elif msg.startswith("/login"):
                    parts = msg.split()
                    if len(parts) >=2:
                        state['user'] = parts[1]
                client.send(msg.encode())

        elif msg:
            if not state.get('e2e'):
                    print("⚠ Please /login first before sending encrypted messages.")
                    continue
            
            if msg[0] == "@":
                target, text = msg.split(" ", 1)
                peer = target[1:]
                try:
                    cipherText = state['e2e'].encrypt(peer, text.encode('utf-8'))
                except ValueError as e:
                    print(f"⚠ Cannot send to {peer}: {e}")
                    continue

                payload = base64.b64encode(cipherText).decode("ascii")
                message = "@" + peer + " " + payload
                client.send(f"{message}".encode())

    client.close()

if __name__ == "__main__":
     start_client()
