import socket
import threading
import os
import sys

SERVER = 'localhost'
PORT = 9999
BUFFER = 4096

def recv_line(sock):
    data = bytearray()
    while True:
        chunk = sock.recv(1)
        if not chunk:
            return None
        data.extend(chunk)
        if data.endswith(b'\n'):
            return data.decode().rstrip('\n')

def recv_exact(sock, n):
    data = bytearray()
    while len(data) < n:
        chunk = sock.recv(min(BUFFER, n - len(data)))
        if not chunk:
            break
        data.extend(chunk)
    return bytes(data)

def receive_loop(sock):
    while True:
        try:
            header = recv_line(sock)
            if header is None:
                print("Connection closed by server.")
                break

            #file incoming header format: FILEFROM:Sender:filename:filesize
            if header.startswith("FILEFROM:"):
                try:
                    _, sender, filename, size_str = header.split(":", 3)
                    size = int(size_str)
                except Exception:
                    print("Malformed file header from server.")
                    continue

                print(f"Receiving file '{filename}' ({size} bytes) from {sender} ...")
                file_bytes = recv_exact(sock, size)

                #save file to current directory with prefix
                save_name = f"recv_{filename}"
                with open(save_name, "wb") as f:
                    f.write(file_bytes)
                print(f"Saved incoming file as '{save_name}'")
                continue

            #otherwise normal text line from server or other clients
            print(header)

        except Exception as e:
            print("Receive thread error:", e)
            break

def send_file(sock, filepath, name):
    if not os.path.isfile(filepath):
        print("File not found:", filepath)
        return
    filename = os.path.basename(filepath)
    filesize = os.path.getsize(filepath)
    header = f"FILE:{filename}:{filesize}\n".encode()
    try:
        sock.sendall(header)
        with open(filepath, "rb") as f:
            while True:
                chunk = f.read(BUFFER)
                if not chunk:
                    break
                sock.sendall(chunk)
    except Exception as e:
        print("Error sending file:", e)

#start client behavior immediately when file is run
client_sock = socket.socket()
try:
    client_sock.connect((SERVER, PORT))
except Exception as e:
    print("Unable to connect to server:", e)
    sys.exit(1)

print("Connected to server.")

name = input("Enter your name: ").strip()
if not name:
    print("Name required.")
    client_sock.close()
    sys.exit(0)

#send name terminated by newline
client_sock.sendall((name + "\n").encode())

#start receive thread
threading.Thread(target=receive_loop, args=(client_sock,), daemon=True).start()

print("Type messages and press Enter to send.")
print("Commands:")
print("  /sendfile <path>   -- send a file to the chat")
print("  exit               -- leave chat")

while True:
    try:
        line = input()
    except EOFError:
        break

    if not line:
        continue

    if line.lower() == "exit":
        try:
            client_sock.sendall("exit\n".encode())
            client_sock.close()
        except:
            pass
        print("Disconnected.")
        break

    #send file command
    if line.startswith("/sendfile "):
        path = line[len("/sendfile "):].strip()
        if not path:
            print("Usage: /sendfile <path>")
            continue
        send_file(client_sock, path, name)
        continue

    try:
        msg = f"{name}: {line}\n"
        client_sock.sendall(msg.encode())
    except Exception as e:
        print("Send failed:", e)
        break