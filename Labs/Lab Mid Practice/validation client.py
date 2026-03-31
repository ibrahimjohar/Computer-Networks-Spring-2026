import os
import socket
import threading

HOST = "localhost"
PORT = 9999

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.connect((HOST, PORT))


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


def receive():
    while True:
        try:
            header = recv_line(s)
            if not header:
                break

            header = header.decode()

            if header.startswith("MSG|"):
                print("Server:", header[4:])

            elif header.startswith("FILE|"):
                # Expected format: FILE|filename|size
                _, filename, size_str = header.split("|", 2)
                size = int(size_str)

                remaining = size
                data = b""

                while remaining > 0:
                    chunk = s.recv(min(1024, remaining))
                    if not chunk:
                        break
                    data += chunk
                    remaining -= len(chunk)

                save_name = "recv_" + os.path.basename(filename)
                with open(save_name, "wb") as f:
                    f.write(data)

                print(f"Server sent file saved as: {save_name}")

            elif header.startswith("REJECT|"):
                print("Rejected:", header[7:])

            else:
                print("Unknown:", header)

        except:
            break


def send():
    while True:
        text = input("You: ")

        if text.startswith("/file "):
            path = text[6:].strip()

            if not os.path.isfile(path):
                print("File does not exist.")
                continue

            filename = os.path.basename(path)
            size = os.path.getsize(path)

            # Send file header first
            s.sendall(f"FILE|{filename}|{size}\n".encode())

            # Send file bytes in chunks
            with open(path, "rb") as f:
                while True:
                    chunk = f.read(1024)
                    if not chunk:
                        break
                    s.sendall(chunk)

        else:
            # Send normal chat message
            s.sendall(f"MSG|{text}\n".encode())


threading.Thread(target=receive, daemon=True).start()
send()