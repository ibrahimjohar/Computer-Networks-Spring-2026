import socket
import threading

c = socket.socket()
c.connect(('localhost', 9999))
print("connected to server correctly.")

name = input("enter name:")
c.sendall(name.encode())

def receive():
    while True:
        try:
            msg = c.recv(1024)
            if not msg:
                break
            print(msg)
        except:
            print("connection closed down by the server.")
            break
        
threading.Thread(target=receive, daemon=True).start()

while True:
    msg = input()
    
    if msg.lower() == "exit":
        c.sendall("exit".encode())
        print("you have left the chat. disconnected.")
        c.close()
        break
    
    c.sendall(f"{name}: {msg}".encode())