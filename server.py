import socket
import threading

clients = {}  # {client_socket: username}

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
            decoded_msg = msg.decode().strip()
            if decoded_msg.startswith("DM:"):
                # Handle direct message
                try:
                    _, recipient, sender, content = decoded_msg.split(":", 3)
                    send_direct_message(sender, recipient, content, client_socket)
                except ValueError:
                    client_socket.send("System: Invalid DM format".encode())
            else:
                # Broadcast regular message
                broadcast(decoded_msg, client_socket)
    except socket.error as e:
        print(f"[ERROR] Socket error with {address}: {e}")
    finally:
        username = clients.get(client_socket, "Unknown")
        print(f"[DISCONNECTED] {username} has left the chat")
        clients.pop(client_socket, None)
        client_socket.close()

def send_direct_message(sender, recipient, content, sender_socket):
    """Send a direct message to the recipient only."""
    recipient_socket = None
    for sock, name in clients.items():
        if name == recipient:
            recipient_socket = sock
            break

    if recipient_socket:
        dm_msg = f"DM:{sender}:{content}"  # Use the DM: format for consistency
        try:
            recipient_socket.send(dm_msg.encode())
            # Do NOT echo back to the sender; the client already displays it locally
        except (socket.error, ConnectionResetError):
            recipient_socket.close()
            clients.pop(recipient_socket, None)
    else:
        sender_socket.send(f"System: User {recipient} not found".encode())

def broadcast(msg, sender_socket):
    """Broadcast message to all clients except the sender."""
    for client in list(clients.keys()):
        if client != sender_socket:
            try:
                client.send(msg.encode())
            except (socket.error, ConnectionResetError):
                client.close()
                clients.pop(client, None)

def start_server(host='127.0.0.1', port=5020):
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind((host, port))
    server.listen()
    print(f"[RUNNING] Listening on {host}:{port}")

    while True:
        client_socket, addr = server.accept()
        threading.Thread(target=handle_client, args=(client_socket, addr), daemon=True).start()

if __name__ == "__main__":
    start_server()