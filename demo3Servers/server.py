import threading
import socket
import sys

from message import Message
from command import Command
import time



# Constants
print("order")
HEADER_LENGTH = 10
HOST = '10.250.209.143'
PORT = int(sys.argv[1])

# Connect sockets to server
server1 = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server1.bind((HOST, PORT))
server1.listen()

server2 = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server2.bind((HOST, PORT-5))
server2.listen()

# Information storage structures

# Stores active socket
clients = []

# Stores active usernames
usernames = [] 


# Stores all active users {username:socket} pairs
clientID = {}

# Stores if a user is online or not all accounts {username:Boolean}
loginStatus = {}

# The server is always online so users cannot log into the server account
loginStatus['SERVER'] = True

# Stores all messages to offline users {username: Message()}
queuedMessages = {}


# Function sends encoded message to username
def sendToClient(username, message):

    # Creates Message() object
    message = Message(username, "SERVER", message)

    # Finds socket associated with user
    client = clientID[username]

    # Sends encoded message to that user
    client.send(message.encode())

# Function receives data from client
def receiveData(client):
    data = client.recv(HEADER_LENGTH).decode('utf-8')
    data_length = int(data.strip())
    data = client.recv(data_length).decode('utf-8')
    return data

# Protocol action handles all actions by the server according to our Protocol
# Input is either a Message() or Command() object
def protocol_action(obj):

    # If the object is a Message() then we try to send the message
    if isinstance(obj, Message):

        # If recipient exists -> sends error to client if they do not
        if obj.recipient not in loginStatus:
            # doesNotExist = "The user you are trying to contact does not exist."
            # doesNotExist = Message(obj.sender, "SERVER", doesNotExist)
            # sendToClient(obj.sender, doesNotExist.encode())

            sendToClient(obj.sender, "The user you are trying to contact does not exist.")

        # If recipient is logged-out -> Alerts sender and and queues the message
        elif not loginStatus[obj.recipient]:
            # notlogin = obj.recipient + " is not logged in. But your message will be delivered"
            # notlogin = Message(obj.sender, "SERVER", notlogin)
            # sendToClient(obj.sender,notlogin.encode())

            sendToClient(obj.sender, f"{obj.recipient} is not logged in. But your message will be delivered")

            if obj.recipient not in queuedMessages.keys():
                queuedMessages[obj.recipient] = []
            queuedMessages[obj.recipient].append(obj)

        # Else sends the message to recipient and delivery confirmation to sender
        elif (clientID[obj.recipient] in clients):
            # success = "Your message has successfully delivered."
            # success = Message(obj.sender, "SERVER", success)
            # sendToClient(obj.recipient, obj.encode())
            # sendToClient(obj.sender, success.encode())
            clientID[obj.recipient].send(obj.encode())
            sendToClient(obj.sender, "Your message has successfully delivered.")
    
    # If the object is a Command() then we execute the command
    if isinstance(obj, Command):

        # If Command type is DA -> Delete Account
        if obj.actionType == "DA":
                
            # User must be online execute this Command so no checks are needed

            # Send confirmation to user
            # success = "Account-Successfully-Deleted"
            # success = Message(obj.username, "SERVER", success)
            # sendToClient(obj.username, success.encode())
            sendToClient(obj.username,"Account-Successfully-Deleted")


            # Remove user from loginStatus and clientID list
            del loginStatus[obj.username]
            del clientID[obj.username]

            # Only delete from queued messages if user had queued messages. 
            if obj.username in queuedMessages.keys():
                del queuedMessages[obj.username]

        # If Command type is LA -> Lists all stored accounts with their login status
        elif obj.actionType == "LA":

            ## Generate account list
            allAccounts = 'LA|'

            # Append (active) or (inactive) to every username
            for account in obj.data:

                #  If username is active
                if obj.data[account]:
                    status = 'active'

                # If username is not active
                else:
                    status = 'inactive'
                
                # Add account status to list with "|", as a divider
                allAccounts += account + " ( " + status + " )" + "|"

            # Remove the last "|" if accounts exists 
            if len(allAccounts) > len("LA|"):
                allAccounts = allAccounts[:-1]

            # Sends list to client to display
            # allAccounts = Message(obj.username, "SERVER", allAccounts)
            # sendToClient(obj.username, allAccounts.encode())
            sendToClient(obj.username, allAccounts)


# Protocol unpack returns Message() and Command() from protocol buffers
# Takes a client socket and encoded buffer data
def protocol_unpack(client):
    # Receives bits from client and converts to buffer(encoded)
    data = receiveData(client)
   
    # Buffer data and splits on the colon 
    dataSplit = data.split(":",3)

    # Retrieves type of message/command from buffer data
    type_ = dataSplit[0]

    # If type is M -> create and return Message() object
    if type_ == "M":

        # Return Message()
        return Message.createMessageFromBuffer(data)

    # If type is LA -> create and return Command() object
    elif type_ == "LA":
        
        # Get username from buffer
        username = dataSplit[1]

        # Return Command() with server login status information
        return Command.createCommandFromBuffer(client, loginStatus ,username,type_)

    # If type is DA -> create and return Command() object
    elif type_ == "DA":

        # Get username from buffer
        username = dataSplit[1]

        # Return Command() 
        return Command.createCommandFromBuffer(client, None ,username,type_)


# Function sends a message to all active accounts 
def broadcast(message):
    
    # Loops through all active users
    for client in clients:

        # Finds username and creates a message object
        index = clients.index(client)
        username = usernames[index]
        
        # # Sends message to user
        sendToClient(username,message)

# Server thread to handle client <-> server communications
def handle_client(client):

    # Displays All accounts and statuses when the client connects

    ## Generate account list
    allAccounts = 'LA|'

    for account in loginStatus:

        # If username is active
        if loginStatus[account]:
            status = 'active'

        # If username is inactive
        else:
            status = 'inactive'

        # Add account status to list with "|", as a divider
        allAccounts += account + " ( " + status + " )" + "|"

    # Remove the last "|" if accounts exists 
    if len(allAccounts) > len("LA|"):
        allAccounts = allAccounts[:-1]
    
    # Sends List of all account statuses to client 
    message = f"M:_:SERVER:{allAccounts}".encode('utf-8')
    header = f"{len(message) :< {HEADER_LENGTH}}".encode('utf-8')
    client.send(header+message)


    ## Account Register/Login Loop

    # Client starts unauthorized
    client_auth = False

    # While user is not authorized attempt to authenticate
    while not client_auth:
         
        # Recieve client Command -- Either type CA (Create Account) or L(Login)
        data = receiveData(client)

        # Split buffer data and extract the username and type that were sent   
        data = data.split(":",3)
        type_ = data[0]
        username = data[1]
        

        # If type is CA -> attempt to create an account with the username
        if type_ == "CA":

            # If username already exists -> Send client error
            if username in loginStatus:
                success = "Username-Already-Exists."
                success = Message(username, "SERVER", success)
                client.send(success.encode())

            # If username doesn't exist -> Send client account creation confirmation
            else:

                # Adds user to the server and logs them in
                usernames.append(username)
                clients.append(client)
                clientID[username] = client
                loginStatus[username] = True

                sendToClient(username,"Successful-Account-Creation.")

                # Broadcasts new connection and authenticates connection
                onConnection(username)
                client_auth = True


        # If type is L -> attempt to Login in with username
        elif type_ == "L":

            # If user does not exist -> send client login failure message
            if username not in loginStatus:
                failed = "Login-Failed"
                failed = Message(username,"SERVER", failed)
                client.send(failed.encode())

            # If user is already active -> alert client!
            elif loginStatus[username]:
                active = "Account-Already-Active"
                active = Message(username, "SERVER", active)
                client.send(active.encode())

            # If username exists and is not active -> log user in
            else:
                # Log user in
                clients.append(client)
                usernames.append(username)
                clientID[username] = client
                loginStatus[username] = True

                # Send confirmation message
                sendToClient(username,"Login-Successful.")

                # Broadcast connection and deliver messages and authenticate client
                onConnection(username)
                client_auth = True

    # Receives buffers from client and applies wire protocol
    while True:
        try:
            

            # Applies wire protocol to buffer -> returns a Message() or Command() objects
            obj = protocol_unpack(client)

            # Applies an action to the object
            protocol_action(obj)


        # This exception handles client crashes and logouts
        except:

            # Removes client from active user lists
            index = clients.index(client)
            clients.remove(client)

            # Get clients username and then remove them from active user lists
            username = usernames[index]
            usernames.remove(username)

            
            # Only change loginStatus is user account isn't deleted
            if username in loginStatus:
                loginStatus[username] = False

            # Broadcast to everyone that the client disconnected
            broadcast(f'{username} has left the chat room!')
            break


# receive() listens for client connections and starts new threads when found
def receive():
    # When server starts
    print('Server 1 Open connection is running and listening ...')

    while True:

        # Accepts new client on client connection
        client, address = server1.accept()
        # Logs client connection information
        print(f'connection is established with: {str(address)}')
        connection = 'A GENERIC SERVER'
        if str(address[1]) == '12349' or str(address[1]) == '12346':
            connection = "SERVER1"
            # Open up receivng thread with Server 1

        elif str(address[1]) == '12350' or str(address[1]) == '12347':
            connection = "SERVER2"
            # Open up receiving thread with Server 2

        elif str(address[1]) == '12351' or str(address[1]) == '12348':
            connection = "SERVER3"
            # Open up receiving thread with Server 3

        else:
            # Open up a receiving thread with the client
            connection = "CLIENT"
            thread = threading.Thread(target=handle_client, args=(client,))
            thread.start()
        
        print((f'connection is established with :{connection}'))




# onConnection() broadcasts a username and dequeues their messages
def onConnection(username):

    # User connection broadcast
    message = f'{username} has connected to the chat room'
    broadcast(message)

    # Dequeing of stored user messages
    if username in queuedMessages.keys():
        for message in queuedMessages[username][:]:

            # Finds socket associated with user
            client = clientID[username]

            # Sends encoded message to that user
            client.send(message.encode())

            queuedMessages[username].remove(message)

if __name__ == "__main__":

    time.sleep(4)
    socket1 = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    socket2 = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    socket1.bind((HOST, PORT + 6))
    socket2.bind((HOST, PORT + 9))
    # attempt to connect to the three servers
    print("MY PORT IS ", PORT)
    if PORT == 12340:
        socket1.connect((HOST, 12341))
        socket2.connect((HOST, 12342))
    elif PORT == 12341:
        socket1.connect((HOST, 12340))
        socket2.connect((HOST, 12342))
    elif PORT == 12342:
        socket1.connect((HOST, 12341))
        socket2.connect((HOST, 12340))
    receive()
