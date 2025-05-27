import socket
import threading
import os

clients = []


def admin_console():
    
    while True:
        cmd = input() 
        if cmd.strip().lower() == "terminate":
            print("[SERVER] Terminate command received. Shutting down.")
            os._exit(0) 

def handle_client(conn, addr):
    print(f"[NEW CONNECTION] {addr} connected.")
    while True:
        try:
            msg = conn.recv(1024)
            if not msg:
                break
            print(f"[{addr}] {msg.decode()}")
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
