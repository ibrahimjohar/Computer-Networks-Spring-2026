import os
import socket
import threading

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.connect(('localhost', 9999))

def recv_line(sock):
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
            
            if header.startwith("MSG|"):
                print("server: ", header[:4])
            elif header.startswith("FILE|"):
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
                    
                print("server sent file: ", save_name)
        except:
            break
        

def send():
    while True:
        text = input("You: ")
        
        if text.startswith("/file "):
            path = text[6:].strip()
            filename = os.path.basename(path)
            size = os.path.getsize(path)
            
            s.sendall(f"FILE|{filename}|{size}\n".encode())
            
            with open(path, "rb") as f:
                while True:
                    chunk = f.read(1024)
                    if not chunk:
                        break
                    s.sendall(chunk)
        else:
            s.sendall(f"MSG|{text}\n".encode())
            
threading.Thread(target=receive, daemon=True).start()
send()

"""
Normal message:

client types text
client sends MSG|hello
server broadcasts it
other clients print it

File:

client types /file mypic.jpg
client sends FILE|mypic.jpg|<size>
client sends file bytes in chunks
server forwards header + bytes
other clients save it back into a file
"""
