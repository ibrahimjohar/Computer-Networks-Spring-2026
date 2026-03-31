import socket
import threading

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.bind(('localhost', 9999))
s.listen()

clients = []

def broadcast(msg, sender):
    for client in clients:
        if client != sender:
            client.send(msg)
            
def handle_client(c):
    while True:
        try:
            msg = c.recv(1024).decode()
            if not msg:
                break
            broadcast(msg.encode(), c)
        except:
            print("a client has disconnected.")
            break
    clients.remove(c)
    c.close()
    
while True:
    c, addr = s.accept()
    clients.append(c)
    print(f"new client connected from {addr}.")
    
    t = threading.Thread(target=handle_client, args=(c,))
    t.start()
    
    
