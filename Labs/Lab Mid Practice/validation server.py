import os
import socket
import threading

HOST = "localhost"
PORT = 9999

ALLOWED_EXTENSIONS = {".txt", ".jpg", ".pdf"}
BANNED_WORDS = {"badword1", "badword2", "spam"}

clients = []
clients_lock = threading.Lock()


def recv_line(sock):
    """
    Read bytes from a socket until a newline byte is found.
    Returns the line WITHOUT the trailing newline.
    """
    data = b""
    while not data.endswith(b"\n"):
        part = sock.recv(1)
        if not part:
            return b""
        data += part
    return data[:-1]


def broadcast(payload, sender=None):
    """
    Send payload to all connected clients except sender.
    """
    with clients_lock:
        current_clients = clients[:]

    for client in current_clients:
        if client != sender:
            try:
                client.sendall(payload)
            except:
                pass


def is_allowed_file(filename):
    ext = os.path.splitext(filename)[1].lower()
    return ext in ALLOWED_EXTENSIONS


def contains_banned_word(message):
    msg = message.lower()
    return any(word in msg for word in BANNED_WORDS)


def discard_bytes(sock, n):
    """
    Read and throw away n bytes from the socket.
    Needed when a file is rejected but the client has already sent its data.
    """
    remaining = n
    while remaining > 0:
        chunk = sock.recv(min(1024, remaining))
        if not chunk:
            break
        remaining -= len(chunk)


def handle_client(c, addr):
    print(f"[CONNECTED] {addr}")

    while True:
        try:
            header = recv_line(c)
            if not header:
                break

            header = header.decode()

            if header.startswith("MSG|"):
                message = header[4:]

                if contains_banned_word(message):
                    c.sendall(b"REJECT|Message contains banned content\n")
                else:
                    broadcast(f"MSG|{message}\n".encode(), sender=c)

            elif header.startswith("FILE|"):
                # Expected format: FILE|filename|size
                _, filename, size_str = header.split("|", 2)
                size = int(size_str)

                if not is_allowed_file(filename):
                    c.sendall(b"REJECT|File type not allowed\n")
                    discard_bytes(c, size)
                else:
                    # Tell other clients a file is coming
                    broadcast(f"FILE|{filename}|{size}\n".encode(), sender=c)

                    # Forward the exact number of bytes in chunks
                    remaining = size
                    while remaining > 0:
                        chunk = c.recv(min(1024, remaining))
                        if not chunk:
                            break
                        broadcast(chunk, sender=c)
                        remaining -= len(chunk)

            else:
                c.sendall(b"REJECT|Unknown command\n")

        except:
            break

    with clients_lock:
        if c in clients:
            clients.remove(c)

    c.close()
    print(f"[DISCONNECTED] {addr}")


def main():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind((HOST, PORT))
    server.listen()

    print(f"Server listening on {HOST}:{PORT}")

    while True:
        client_socket, addr = server.accept()
        with clients_lock:
            clients.append(client_socket)

        thread = threading.Thread(
            target=handle_client,
            args=(client_socket, addr),
            daemon=True
        )
        thread.start()


if __name__ == "__main__":
    main()