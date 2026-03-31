import os
import socket
import threading

clients = []

def broadcast(sender, payload):
    for client in clients:
        if client != sender:
            try:
                client.sendall(payload)
            except:
                pass

def recv_line(sock):
    data = 'b'
    while not data.endswith(b"\n"):
        part = sock.recv(1)
        if not part:
            return b""
        data += part
    return data[:-1]        #remove the newline character

def handle_client(c):
    while True:
        try:
            header = recv_line(c)
            if not header:
                break
            
            header = header.decode()
            
            if header.startswith("MSG|"):
                message = header[4:]
                broadcast(c, f"MSG|{message}\n".encode())
            elif header.startswith("FILE|"):
                _, filename, size_str = header.split("|", 2)
                size = int(size_str)
                
                remaining = size
                file_bytes = b""
                
                while remaining > 0:
                    chunk = c.recv(min(1024, remaining))
                    if not chunk:
                        break
                    file_bytes += chunk
                    remaining -= len(chunk)
                    
                broadcast(c, f"FILE|{filename}|{size}\n".encode())
                broadcast(c, file_bytes)
        except:
            break
    if c in clients:
        clients.remove(c)
    c.close()
    
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.bind(('localhost', 9999))
s.listen()

while True:
    c, addr = s.accept()
    clients.append(c)
    threading.Thread(target=handle_client, args=(c,), daemon=True).start()
    


"""
ALLOWED_EXTENSIONS = {".txt", ".jpg", ".pdf"}
BANNED_WORDS = ["badword1", "badword2", "spam"]

def is_allowed_file(filename):
    ext = os.path.splitext(filename)[1].lower()
    return ext in ALLOWED_EXTENSIONS

def has_banned_word(message):
    msg = message.lower()
    return any(word in msg for word in BANNED_WORDS)

Then inside the server handler:

if header.startswith("MSG|"):
    message = header[4:]

    if has_banned_word(message):
        c.sendall(b"REJECT|Message contains banned content\n")
    else:
        broadcast(c, f"MSG|{message}\n".encode())

elif header.startswith("FILE|"):
    _, filename, size_str = header.split("|", 2)

    if not is_allowed_file(filename):
        c.sendall(b"REJECT|File type not allowed\n")
    else:
        # receive file bytes
        # then broadcast file
        pass
"""
    
                