import socket
import threading
import os
nickname = input("Choose your nickname: ")

client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client.connect(('localhost', 5555))


print("connected to validated chat server")
print("Commands:")
print("  /file <filepath>  - Send a file")
print("  /quit             - Disconnect")
print("  Just type to send a message")

def receive():
    while True:
        try:
            message = client.recv(1024).decode('utf-8')
            if message == 'NICK':
                client.send(nickname.encode('utf-8'))
            else:
                if message.startswith('[SERVER]'):
                    print(f"\n{message}")
                    print(f"{nickname}: ", end='', flush=True)
                else:
                    print(f"\n{message}")
                    print(f"{nickname}: ", end='', flush=True)
                    
        except:
            print("\n[ERROR] Connection to server lost!")
            client.close()
            break

def write():
    while True:
        try:
            message = input(f"{nickname}: ")
            if message.startswith('/file '):
                filepath = message[6:].strip()
                if not os.path.exists(filepath):
                    print("[ERROR] File not found!")
                    continue

                filename = os.path.basename(filepath)
                filesize = os.path.getsize(filepath)
                _, extension = os.path.splitext(filename)
                print(f"[UPLOADING] '{filename}' ({filesize} bytes, type: {extension})")
                
                try:
                    client.send("FILE".ljust(10).encode('utf-8'))
                    client.send(str(len(filename)).ljust(10).encode('utf-8'))
                    client.send(filename.encode('utf-8'))
                    client.send(str(filesize).ljust(20).encode('utf-8'))
                    with open(filepath, 'rb') as f:
                        sent = 0
                        while sent < filesize:
                            chunk = f.read(4096)
                            if not chunk:
                                break
                            client.send(chunk)
                            sent += len(chunk)
                    
                    print(f"[SENT] File upload complete. Waiting for server validation...")
                    
                except Exception as e:
                    print(f"[ERROR] Failed to send file: {e}")
            

            elif message.lower() == '/quit':
                client.send("DISCONNECT".ljust(10).encode('utf-8'))
                print("[DISCONNECTED] Goodbye!")
                client.close()
                break
            
            elif message.strip():
                formatted_message = f'{nickname}: {message}'
                client.send("TEXT".ljust(10).encode('utf-8'))
                client.send(formatted_message.encode('utf-8'))
                
        except KeyboardInterrupt:
            print("\n[DISCONNECTED] Goodbye!")
            client.close()
            break
        except Exception as e:
            print(f"[ERROR] {e}")
            break


receive_thread = threading.Thread(target=receive)
receive_thread.daemon = True  
receive_thread.start()
write_thread = threading.Thread(target=write)
write_thread.start()

