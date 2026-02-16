import socket
import threading

clients = []
names = {}

lock = threading.Lock()

def broadcast(message, sender=None):
    with lock:
        for c in clients:
            if c != sender:
                try:
                    c.sendall(message)
                except:
                    c.close()
                    
def handle_client(conn):
    while True:
        try:
            msg = conn.recv(1024)
            if not msg:
                break

            decoded = msg.decode()

            if decoded.lower().endswith("exit"):
                name = names.get(conn, "Unknown")

                broadcast(f"{name} has left the chat\n".encode(), conn)

                with lock:
                    clients.remove(conn)
                    del names[conn]

                conn.close()
                break

            broadcast(msg, conn)

        except:
            with lock:
                if conn in clients:
                    clients.remove(conn)
                    
            conn.close()
            break
        
s = socket.socket()
s.bind(('localhost', 9999))

s.listen(5)

print("the chat server is running now..")
print("waiting for client to connect..")

while True:
    c, addr = s.accept()
    
    name = c.recv(1024).decode()
    
    with lock:
        clients.append(c)
        names[c] = name
        
    print(f"{name} has connected")
    
    broadcast(f"{name} has joined the chat\n".encode())
    
    thread = threading.Thread(target=handle_client, args=(c,), daemon=True)
    thread.start()