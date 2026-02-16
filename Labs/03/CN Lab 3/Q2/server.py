# ipynb files weren't supporting an interactive chat server like this for me so i had to program it in a .py file
# to check the code, open the terminal and run 'python server.py' to start the server, 
# then open another terminal and run 'python client.py' to connect as a client. 
# You can run multiple clients in separate terminals to test the chat functionality.

import socket
import threading 
clients = []
nicknames = []
server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.bind(('localhost', 5555))
server.listen()

print("Server is running and waiting for connections...")
def broadcast(message):
    for client in clients:
        try:
            client.send(message)
        except:
            pass
        
def handle_client(client):
    while True:
        try:
            message = client.recv(1024)
            broadcast(message)
            
        except:
            index = clients.index(client)
            clients.remove(client)
            client.close()
            
            nickname = nicknames[index]

            broadcast(f'{nickname} left the chat!'.encode('utf-8'))

            nicknames.remove(nickname)
            break


def receive():
    while True:
        client, addr = server.accept()
        print(f"Connected with {addr}")
        
        client.send('NICK'.encode('utf-8'))
        

        nickname = client.recv(1024).decode('utf-8')
        

        nicknames.append(nickname)
        clients.append(client)

        print(f"Nickname of the client is {nickname}")
        broadcast(f'{nickname} joined the chat!'.encode('utf-8'))
        client.send('Connected to the server!'.encode('utf-8'))
        thread = threading.Thread(target=handle_client, args=(client,))
        thread.start()
        
        
print("Server is listening for clients...")
receive()