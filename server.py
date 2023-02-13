import threading
import socket
import Message
host = '127.0.0.1'
port = 59000
server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.bind((host, port))
server.listen()
clients = [] #live users [client_socket, client_socket]
aliases = [] 
clientID = {} # Now: [alias: client_socket] Future -> [userID: User(), userID: User()]

#Class User
# client
# queuedMessages [Message()]
# deque --> 

loginStatus = {} #[alias: T or F]
#[A: T, B: F, C: F, D: T]
#Send User X

queuedMessages = {} #[alias:[Message(), Message(), Message()]


def broadcast(message):
    for client in clients:
        client.send(message)

# Function to handle clients'connections
def sendToClient(alias, message):
    client = clientID[alias]
    client.send(message)


def unPackMessage(data):
    decodedM = data.decode('UTF-8').split("->")
    sender = decodedM[0]
    recipient = decodedM[1].strip()
    recipient = recipient.encode('UTF-8')
    message = (sender + " says -> " + decodedM[2]).encode('UTF-8')
    return recipient, message

def protocol(data):
    "M:SENDER:RECIPIENT:MESSAGE"
    dataSplit = data.decode('UTF-8').split(":")
    type_ = dataSplit[0]
    if type_ == "M":
        return Message.createMessageFromBuffer(dataSplit)


def handle_client(client):
    while True:
        try:
            index = clients.index(client)
            alias = aliases[index]
            data = client.recv(1024)
            obj = protocol(data)
            # UNPACK 
            # Get type
            # Check if type is message, command, etc... 
            # Return message or command or etc... obj
            # Check what type of object our unpack function returned 
            # Act on message or command or etc... () Can be under the hood

            recipient, message = unPackMessage(data)
            if recipient not in loginStatus:
                client.send(("The user you are trying to contact does not exist.").encode('UTF-8'))
            # Check if user is logged in
            elif not loginStatus[recipient]:
                notlogin = recipient.decode('UTF-8') + " is not logged in."
                notlogin = notlogin.encode('UTF-8')
                client.send(notlogin)
                if recipient not in queuedMessages.keys():
                    queuedMessages[recipient] = []
                queuedMessages[recipient].append(message)
            #If user is active
            elif (clientID[recipient] in clients):
                sendToClient(recipient, message)
            else:
                print(clientID.keys())
                print(recipient + " does not exist")
                broadcast(data)

        except:
            # Client Logs out or Crashes
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
