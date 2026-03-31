import socket
import threading

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.connect(('localhost', 9999))

def receive():
    while True:
        try:
            msg = s.recv(1024).decode()
            print(msg)
        except:
            print("connection closed by the server.")
            break

def send():
    while True:
        msg = input()
        s.send(msg.encode())
        
t1 = threading.Thread(target=receive)
t2 = threading.Thread(target=send)

t1.start()
t2.start()