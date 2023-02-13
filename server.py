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
loginStatus = {}
queuedMessages = {}


def broadcast(message):
    for client in clients:
        client.send(message)

# Function to handle clients'connections

def sendToClient(alias, message):
    client = clientID[alias]
    client.send(message)


def unPackMessage(client, data):

    decodedM = data.decode('UTF-8').split("->")
    sender = decodedM[0]
    deliver = decodedM[1].strip()
    deliver = deliver.encode('UTF-8')
    message = (sender + " says -> " + decodedM[2]).encode('UTF-8')
    return deliver, message


def handle_client(client):
    while True:
        try:
            index = clients.index(client)
            alias = aliases[index]
            data = client.recv(1024)
            deliver,message = unPackMessage(client, data)
            if deliver not in loginStatus:
                client.send(("The user you are trying to contact does not exist.").encode('UTF-8'))
            elif not loginStatus[deliver]:
                notlogin = deliver.decode('UTF-8') + " is not logged in."
                notlogin = notlogin.encode('UTF-8')
                client.send(notlogin)
                if deliver not in queuedMessages.keys():
                    queuedMessages[deliver] = []
                queuedMessages[deliver].append(message)
            elif (deliver in clientID) and (clientID[deliver] in clients):
                sendToClient(deliver, message)
            else:
                print(clientID.keys())
                print(deliver + " does not exist")
                broadcast(data)

        except:
            index = clients.index(client)
            clients.remove(client)
            client.close()
            alias = aliases[index]
            loginStatus[alias] = False
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
        loginStatus[alias] = True
        print(f'The alias of this client is {alias}'.encode('utf-8'))
        broadcast(f'{alias} has connected to the chat room'.encode('utf-8'))
        client.send('you are now connected! \n'.encode('utf-8'))
        if alias in queuedMessages.keys():
            for message in queuedMessages[alias][:]:
                client.send(message)
                queuedMessages[alias].remove(message)
        thread = threading.Thread(target=handle_client, args=(client,))
        thread.start()


if __name__ == "__main__":
    receive()
