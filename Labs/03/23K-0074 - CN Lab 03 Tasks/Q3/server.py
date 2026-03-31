import socket
import threading
import os

HOST = '0.0.0.0'
PORT = 9999

clients = []  #list of socket objects
names = {}    #conn -> name
lock = threading.Lock()

#validation settings
ALLOWED_EXT = {'.txt', '.jpg', '.jpeg', '.pdf', '.png'}
BANNED_WORDS = {'badword', 'spamword', 'foo'}   

def recv_line(conn):
    data = bytearray()
    while True:
        chunk = conn.recv(1)
        if not chunk:
            return None
        data.extend(chunk)
        if data.endswith(b'\n'):
            return bytes(data)

def recv_exact(conn, n):
    data = bytearray()
    while len(data) < n:
        chunk = conn.recv(min(4096, n - len(data)))
        if not chunk:
            break
        data.extend(chunk)
    return bytes(data)

def broadcast(message_bytes, sender_conn=None):
    with lock:
        for c in list(clients):
            if c is sender_conn:
                continue
            try:
                c.sendall(message_bytes)
            except Exception:
                try:
                    c.close()
                except:
                    pass
                if c in clients:
                    clients.remove(c)
                if c in names:
                    del names[c]

def broadcast_file(sender_conn, filename, file_bytes, sender_name):
    header = f"FILEFROM:{sender_name}:{filename}:{len(file_bytes)}\n".encode()
    with lock:
        for c in list(clients):
            if c is sender_conn:
                continue
            try:
                c.sendall(header)
                c.sendall(file_bytes)
            except Exception:
                try:
                    c.close()
                except:
                    pass
                if c in clients:
                    clients.remove(c)
                if c in names:
                    del names[c]

def validate_message_text(text):
    low = text.lower()
    for bw in BANNED_WORDS:
        if bw in low:
            return False, f"Message contains banned word: '{bw}'"
    return True, ""

def handle_client(conn, addr):
    try:
        #read name (line terminated)
        name_line = recv_line(conn)
        if not name_line:
            conn.close()
            return
        name = name_line.decode().strip()
        with lock:
            clients.append(conn)
            names[conn] = name

        print(f"{name} connected from {addr}")
        broadcast(f"SERVER: {name} has joined the chat\n".encode(), sender_conn=None)

        while True:
            header_line = recv_line(conn)
            if header_line is None:
                break
            header = header_line.decode().rstrip('\n')

            if header.strip().lower() == "exit":
                with lock:
                    if conn in clients:
                        clients.remove(conn)
                        left_name = names.pop(conn, "Unknown")
                broadcast(f"SERVER: {left_name} has left the chat\n".encode(), sender_conn=None)
                conn.close()
                break

            #file transfer header: FILE:filename:filesize
            if header.startswith("FILE:"):
                #parse header
                try:
                    _, filename, filesize_str = header.split(":", 2)
                    filesize = int(filesize_str)
                except Exception:
                    conn.sendall(f"SERVER: Invalid file header\n".encode())
                    continue

                _, ext = os.path.splitext(filename)
                ext = ext.lower()
                sender_name = names.get(conn, "Unknown")

                if ext not in ALLOWED_EXT:
                    #reject file
                    msg = f"SERVER: File '{filename}' rejected (extension {ext} not allowed)\n"
                    conn.sendall(msg.encode())
                    print(f"Rejected file from {sender_name}: {filename} (ext {ext})")
                    #still need to read and discard the incoming bytes from sender
                    _ = recv_exact(conn, filesize)
                    continue

                #read file bytes from sender
                file_bytes = recv_exact(conn, filesize)
                if len(file_bytes) < filesize:
                    #incomplete transfer
                    conn.sendall(f"SERVER: File transfer incomplete for '{filename}'\n".encode())
                    continue

                #broadcast file to other clients
                broadcast_file(conn, filename, file_bytes, sender_name)
                conn.sendall(f"SERVER: File '{filename}' delivered to other clients\n".encode())
                print(f"Delivered file from {sender_name}: {filename} ({filesize} bytes)")
                continue

            #normal chat message
            ok, reason = validate_message_text(header)
            if not ok:
                #notify sender only
                conn.sendall(f"SERVER: Your message was rejected. Reason: {reason}\n".encode())
                print(f"Rejected message from {names.get(conn,'Unknown')}: {reason}")
                continue

            #broadcast allowed message (include newline)
            broadcast((header + "\n").encode(), sender_conn=conn)

    except Exception as e:
        print("Exception in handle_client:", e)
    finally:
        with lock:
            if conn in clients:
                clients.remove(conn)
            if conn in names:
                left_name = names.pop(conn, "Unknown")
                broadcast(f"SERVER: {left_name} has disconnected\n".encode(), sender_conn=None)
        try:
            conn.close()
        except:
            pass

#start server immediately when file is run
server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
server_socket.bind((HOST, PORT))
server_socket.listen(10)
print(f"Server listening on {HOST}:{PORT}")

try:
    while True:
        conn, addr = server_socket.accept()
        t = threading.Thread(target=handle_client, args=(conn, addr), daemon=True)
        t.start()
except KeyboardInterrupt:
    print("Server shutting down.")
finally:
    server_socket.close()