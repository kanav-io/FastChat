import socket
import threading

def receive_messages(sock):
    while True:
        try:
            msg = sock.recv(1024).decode()
            if msg:
                print(f"\n{msg}")
        except:
            break

def start_client(server_ip='127.0.0.1', server_port=12345):
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client.connect((server_ip, server_port))

    print(f"Connected to chat server at {server_ip}:{server_port}")
    name = input("Enter your name: ")

    threading.Thread(target=receive_messages, args=(client,), daemon=True).start()

    while True:
        msg = input()
        if msg[0] == "$"
            if msg.lower() == "$exit":
                break
            else:
                client.send(f"{msg}".encode())

        else:
            client.send(f"{name}: {msg}".encode())

    client.close()

if __name__ == "__main__":
    start_client()

