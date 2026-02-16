import socket
import threading
import os 

clients = []
nicknames = []
ALLOWED_FILE_EXTENSIONS = ['.txt', '.jpg', '.jpeg', '.png', '.pdf']
BANNED_WORDS = ['badword1', 'badword2', 'spam', 'inappropriate']
server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
server.bind(('localhost', 5555))
server.listen()


print("validated chat server")
print(f"Allowed file types: {', '.join(ALLOWED_FILE_EXTENSIONS)}")
print(f"Banned words: {len(BANNED_WORDS)} words in filter")
print("Server is running and waiting for connections...")

def is_file_allowed(filename):
    _, extension = os.path.splitext(filename)
    extension = extension.lower()
    is_allowed = extension in ALLOWED_FILE_EXTENSIONS
    return is_allowed, extension


def contains_banned_words(message):
    message_lower = message.lower()
    found_words = []
    for banned_word in BANNED_WORDS:
        if banned_word.lower() in message_lower:
            found_words.append(banned_word)
    contains_banned = len(found_words) > 0
    return contains_banned, found_words

def broadcast(message, sender_client=None):
    if isinstance(message, str):
        message = message.encode('utf-8')
    for client in clients:
        if client == sender_client:
            continue
        
        try:
            client.send(message)
        except:
            pass


def send_to_client(client, message):
    try:
        formatted_message = f"[SERVER] {message}"
        client.send(formatted_message.encode('utf-8'))
    except:
        pass

def handle_client(client):
    while True:
        try:
            msg_type = client.recv(10).decode('utf-8').strip()
            if msg_type == "TEXT":
                message = client.recv(1024).decode('utf-8')
                
                if not message:
                    break
                has_banned, found_words = contains_banned_words(message)
                
                if has_banned:
                    print(f"REJECTED: Message from {nicknames[clients.index(client)]} (banned words: {found_words})")
                    rejection_msg = f"Your message was rejected. It contains banned words: {', '.join(found_words)}"
                    send_to_client(client, rejection_msg)
                else:
                    print(f"✓ Message from {nicknames[clients.index(client)]}: {message}")
                    broadcast(message, sender_client=client)
                    
            elif msg_type == "FILE":
                filename_len = int(client.recv(10).decode('utf-8').strip())
                filename = client.recv(filename_len).decode('utf-8')
                is_allowed, extension = is_file_allowed(filename)
                
                if not is_allowed:
                    print(f"REJECTED: File '{filename}' from {nicknames[clients.index(client)]} (extension {extension} not allowed)")
                    rejection_msg = f"File '{filename}' rejected. Extension '{extension}' is not allowed. Allowed types: {', '.join(ALLOWED_FILE_EXTENSIONS)}"
                    send_to_client(client, rejection_msg)
                    filesize = int(client.recv(20).decode('utf-8').strip())
                    received = 0
                    while received < filesize:
                        chunk = client.recv(min(4096, filesize - received))
                        received += len(chunk)
                    
                else:
                    print(f" Receiving file: '{filename}' from {nicknames[clients.index(client)]}")
                    filesize = int(client.recv(20).decode('utf-8').strip())
                    os.makedirs("validated_received_files", exist_ok=True)
                    filepath = os.path.join("validated_received_files", filename)
                    with open(filepath, 'wb') as f:
                        received = 0
                        while received < filesize:
                            chunk = client.recv(min(4096, filesize - received))
                            if not chunk:
                                break
                            f.write(chunk)
                            received += len(chunk)
                    
                    print(f"✓ File saved: {filepath}")
                    send_to_client(client, f"File '{filename}' uploaded successfully!")
                    notification = f"[FILE] {nicknames[clients.index(client)]} shared '{filename}' ({filesize} bytes)"
                    broadcast(notification, sender_client=client)
            elif msg_type == "DISCONNECT":
                break
                
        except Exception as e:
            print(f"Error handling client: {e}")
            break
        
    index = clients.index(client)
    clients.remove(client)
    client.close()
    nickname = nicknames[index]
    nicknames.remove(nickname)
    broadcast(f'{nickname} left the chat!')
    print(f"- {nickname} disconnected")
    
def receive():
    while True:
        client, address = server.accept()
        print(f"\n+ New connection from {address}")
        client.send('NICK'.encode('utf-8'))
        nickname = client.recv(1024).decode('utf-8')
        nicknames.append(nickname)
        clients.append(client)
        print(f"+ Nickname: {nickname}")
        broadcast(f'{nickname} joined the chat!')
        send_to_client(client, 'Connected to validated chat server!')
        send_to_client(client, f'Allowed file types: {", ".join(ALLOWED_FILE_EXTENSIONS)}')
        thread = threading.Thread(target=handle_client, args=(client,))
        thread.start()

receive()