import threading
import socket

from message import Message
from command import Command

HEADER_LENGTH = 10
HOST = '10.250.92.212'
PORT = 12340


server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.bind((HOST, PORT))
server.listen()


clients = []
usernames = [] 
clientID = {}

loginStatus = {}
loginStatus['SERVER'] = True

queuedMessages = {} #[username:[Message(), Message(), Message()]


# TODO Login and Register will need to be in another earlier function
def protocol_action(obj):

    if isinstance(obj, Message):

        # we now know we are working with a message
        if obj.recipient not in loginStatus:
            doesNotExist = "The user you are trying to contact does not exist."
            doesNotExist = Message(obj.sender, "SERVER", doesNotExist)
            sendToClient(obj.sender, doesNotExist.encode())

        # Check if user is logged in
        elif not loginStatus[obj.recipient]:
            notlogin = obj.recipient + " is not logged in. But your message will be delivered"
            notlogin = Message(obj.sender, "SERVER", notlogin)
            sendToClient(obj.sender,notlogin.encode())
            if obj.recipient not in queuedMessages.keys():
                queuedMessages[obj.recipient] = []
            queuedMessages[obj.recipient].append(obj)

        #If user is active
        elif (clientID[obj.recipient] in clients):
            success = "Your message has successfully delivered."
            success = Message(obj.sender, "SERVER", success)
            sendToClient(obj.recipient, obj.encode())
            sendToClient(obj.sender, success.encode())
    
    if isinstance(obj, Command):

        if obj.actionType == "DA":
            
            # user doesn't exist? THIS MAY BE REDUNDANT CAUSE USER MUST EXIST TO MAKE CALL
            if obj.username not in clientID:
                failure = "Account-Does-Not-Exist"
                failure = Message(obj.username,"SERVER",failure)
                sendToClient(obj.username,failure.encode())
                
            # user exists
            else:
                
                # Send confirmation to user
                success = "Account-Successfully-Deleted"
                success = Message(obj.username, "SERVER", success)
                sendToClient(obj.username, success.encode())

                # Close socket - note disconnection of socket will automatically remove user from clients and usernames

                # remove user from lists
                del loginStatus[obj.username]
                del clientID[obj.username]

                # only delete from queued messages if user had queued messages. 
                if obj.username in queuedMessages.keys():
                    del queuedMessages[obj.username]

                
        elif obj.actionType == "LA":
            ## Generate account list

            # obj.data {username: loginstatus}
            allAccounts = 'LA|'
            for account in obj.data:
                #  username is active
                if obj.data[account]:
                    status = 'active'
                # username is not active
                else:
                    status = 'inactive'
                allAccounts += account + " ( " + status + " )" + "|"
            if len(allAccounts) > len("LA|"):
                allAccounts = allAccounts[:-1]
            allAccounts = Message(obj.username, "SERVER", allAccounts)
            sendToClient(obj.username, allAccounts.encode())


def protocol_unpack(data,client):
    data = data.decode('UTF-8')
    dataSplit = data.split(":",3)
    type_ = dataSplit[0]
    print("UNPACK-TYPE:",type_)
    match type_:

        case "M":
            return Message.createMessageFromBuffer(data)
        
        case "LA":
            username = dataSplit[1]

            #TODO Implement createCommandFromBuffer
            # usage -> Command.createCommandFromBuffer(client, external_data, data)
            return Command(client, loginStatus, username, type_)

        case "DA":

            #TODO Implement createCommandFromBuffer
            username = dataSplit[1]
            return Command(client, None ,username,type_)
                
def broadcast(message):
    for client in clients:
        index = clients.index(client)
        username = usernames[index]

        message = Message(username, "SERVER", message)
        
        client.send(message.encode())

# Function to handle clients'connections
def sendToClient(username, message):

    client = clientID[username]
    client.send(message)



def handle_client(client):
    # First message will be list accounts
    data = client.recv(HEADER_LENGTH).decode('utf-8')
    data_length = int(data.strip())
    data = client.recv(data_length)

    ## Generate account list

    # obj.data {username: loginstatus}
    allAccounts = 'LA|'
    for account in loginStatus:
        #  username is active
        if loginStatus[account]:
            status = 'active'
        # username is not active
        else:
            status = 'inactive'
        allAccounts += account + " ( " + status + " )" + "|"
    if len(allAccounts) > len("LA|"):
        allAccounts = allAccounts[:-1]
    
    message = f"M:_:SERVER:{allAccounts}".encode('utf-8')
    header = f"{len(message) :< {HEADER_LENGTH}}".encode('utf-8')
    client.send(header+message)


    client_auth = False
    # Validation - conditions -> while not auth
    while not client_auth:
         
        data = client.recv(HEADER_LENGTH).decode('utf-8')
        # print("DATA 1:", data)
        data_length = int(data.strip())
        # print("DATA Length is ", data_length)
        data = client.recv(data_length).decode('utf-8')
        print("data is ", data)
        
        data = data.split(":",3)
        type_ = data[0]
        username = data[1]
        
        if type_ == "CA":
            # Attempting to create account
            
            # print("We are trying to create an account for " + username)
            # print("DATALIST:",data)

            # User already exists
            if username in loginStatus:
                success = "Username-Already-Exists."
                success = Message(username, "SERVER", success)
                client.send(success.encode())
            else:
                # Account is succesffuly created and logged in 
                usernames.append(username)
                clients.append(client)
                clientID[username] = client
                loginStatus[username] = True
                success = "Successful-Account-Creation."
                success = Message(username, "SERVER", success)
                client.send(success.encode())
                onConnection(username)
                client_auth = True
        elif type_ == "L":
            # Attempting to login

            # User does not exist.
            if username not in loginStatus:
                failed = "Login-Failed"
                failed = Message(username,"SERVER", failed)
                client.send(failed.encode())
            # User is already active.
            elif loginStatus[username]:
                # error message that user is already logged in another machine
                active = "Account-Already-Active"
                active = Message(username, "SERVER", active)
                client.send(active.encode())
            else:
                clients.append(client)
                usernames.append(username)
                clientID[username] = client
                loginStatus[username] = True
                success = "Login-Successful."
                success = Message(username, "SERVER", success)
                client.send(success.encode())
                onConnection(username)
                client_auth = True
    # Normal
    while True:
        try:
            header = client.recv(HEADER_LENGTH).decode("utf-8").strip()
            data_length = int(header)
            data = client.recv(data_length)
            # print("HANDLE CLIENT DATA:",data)
            obj = protocol_unpack(data,client)
            protocol_action(obj)

        except:
            # Client Logs out or Crashes
            index = clients.index(client)
            clients.remove(client)
            client.close()
            username = usernames[index]
            # print("USERNAME:",username)
            
            # Check this problem on GRPC 
            if username in loginStatus:
                loginStatus[username] = False
            # print("LOGINSTATUSLIST:",loginStatus)
            # print("USER LOGINSTATUS:", loginStatus[username])
            broadcast(f'{username} has left the chat room!')
            usernames.remove(username)
            break
# Main function to receive the clients connection

def receive():
    while True:
        print('Server is running and listening ...')
        client, address = server.accept()
        print(f'connection is established with {str(address)}')
        print((f'connection is established with CLIENT'))
        print(client)
        # message = f'M:new_user:SERVER:username?'.encode('utf-8')
        # header = f"{len(message) :< {HEADER_LENGTH}}".encode('utf-8')
        # client.send(header+message)
       
        thread = threading.Thread(target=handle_client, args=(client,))
        thread.start()

def onConnection(username):
    # print(f'The username of this client is {username}')
    message = f'{username} has connected to the chat room'
    broadcast(message)
    #broadcast(message)
    if username in queuedMessages.keys():
        for message in queuedMessages[username][:]:
            sendToClient(username, message.encode())
            queuedMessages[username].remove(message)

if __name__ == "__main__":
    receive()
