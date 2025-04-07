import socket
import threading

clients = {}

def handle_client(client_socket, address):
    try:
        username = client_socket.recv(1024).decode().strip()
        if not username:
            username = "Unknown"
        clients[client_socket] = username
        print(f"[CONNECTION] {username} connected from {address}")

        while True:
            msg = client_socket.recv(1024)
            if not msg:
                break
            broadcast(msg.decode(), client_socket)
    except socket.error as e:
        print(f"[ERROR] Socket error with {address}: {e}")
    finally:
        username = clients.get(client_socket, "Unknown")
        print(f"[DISCONNECTED] {username} has left the chat")
        clients.pop(client_socket, None)
        client_socket.close()

def broadcast(msg, sender_socket):
    for client in list(clients.keys()):
        if client != sender_socket:
            try:
                client.send(msg.encode())
            except (socket.error, ConnectionResetError):
                client.close()
                clients.pop(client, None)

def start_server(host = '127.0.0.1', port = 5020):
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind((host, port))  # Fix bind to use tuple (host, port)
    server.listen()
    print(f"[RUNNING] Listening on {host}:{port}")

    while True:
        client_socket, addr = server.accept()
        threading.Thread(target = handle_client, args = (client_socket, addr), daemon = True).start()

if __name__ == "__main__":
    start_server()
