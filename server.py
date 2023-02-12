'Chat Room Connection - Client-To-Client'

import threading
import socket
host = '127.0.0.1'
port = 59000
server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.bind((host, port))
server.listen()
clients = []
aliases = []
clientID = {}

def broadcast(message):
    for client in clients:
        client.send(message)

# Function to handle clients'connections

def sendToClient(alias, message):
    client = clientID[alias]
    client.send(message)

def handle_client(client):
    while True:
        try:
            message = client.recv(1024)
            decodedM = message.decode('UTF-8').split("->")
            sender = decodedM[0]
            deliver = decodedM[1].strip()
            deliver = deliver.encode('UTF-8')
            #deliver = b'Reza'
            if deliver in clientID:
                sendToClient(deliver, (sender + " says -> " + decodedM[2]).encode('UTF-8'))
            else:
                print(clientID.keys())
                print(deliver + " does not exist")
                broadcast(message)

        except:
            index = clients.index(client)
            clients.remove(client)
            client.close()
            alias = aliases[index]
            broadcast(f'{alias} has left the chat room!'.encode('utf-8'))
            aliases.remove(alias)
            break
# Main function to receive the clients connection


def receive():
    while True:
        print('Server is running and listening ...')
        client, address = server.accept()
        print(f'connection is established with {str(address)}')
        print((f'connection is established with CLIENT'))
        print(client)
        client.send('alias?'.encode('utf-8'))
        alias = client.recv(1024)
        aliases.append(alias)
        clients.append(client)
        clientID[alias] = client
        print(f'The alias of this client is {alias}'.encode('utf-8'))
        broadcast(f'{alias} has connected to the chat room'.encode('utf-8'))
        client.send('you are now connected!'.encode('utf-8'))
        thread = threading.Thread(target=handle_client, args=(client,))
        thread.start()


if __name__ == "__main__":
    receive()
