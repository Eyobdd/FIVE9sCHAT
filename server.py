import threading
import socket
import random
from message import Message
HEADER_LENGTH = 10


host = '127.0.0.1'
port = 12340
server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.bind((host, port))
server.listen()
clientDict = {} # [username: Account(), username: Account()]
clients = [] #live users [client_socket, client_socket]
usernames = [] 
clientID = {} # Now: [username: client_socket] Future -> [userID: User(), userID: User()]


#Class User
# client
# queuedMessages [Message()]
# deque --> 

loginStatus = {} #[username: T or F]
#[A: T, B: F, C: F, D: T]
#Send User X

queuedMessages = {} #[username:[Message(), Message(), Message()]

def encoded_message(message):
    message = message.encode('utf-8')
    header = f"{len(message) :< {HEADER_LENGTH}}".encode('utf-8')
    return header+message

# TODO Login and Register will need to be in another earlier function
def protocol_action(obj):
    print("our object is of instance ")
    print(obj)
    print(type(obj))
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

    # else:
    #     # must be an account
    # match type_ :

    #     # Message type -> call send message on object
    #     case "M":
    #         recipient = data[1]

    #         # Does recipient exist?
    #         if recipient in clientDict:

    #             recipient_account = clientDict[recipient]
    #             recipient_online = recipient_account.online
                
    #             # if recipient online -> send message
    #             if recipient_online: 
    #                 obj.send()
    #             # if recipient offline -> queue messsage
    #             else:
    #                 recipient_account.queueMessage(obj)
    #         else:
    #             # TODO Send Error to sender!
    #             sender = data[2]
    #             sender_account = clientDict[sender]
    #             sender_account.sendConfirmation(sender_account.socket,"User does not exist!")


    #     # Login type -> call login method on object // TODO IDK if this is true but its late I will fix tmr need to do more logic on this side
    #     case "L":
    #         if obj.exists:
    #             # find the account via username and login
    #             obj.account_obj.login(obj.exists,client)
    #         else:
    #             # sends login error
    #             account.Account.login(obj.exists,client)

    #     # Delete type -> call delete method on object
    #     case "D":
    #         username = data[1]
    #         if obj.exists:
    #             # deletes object from account dictionary
    #             del clientDict[username]
    #             # send confirmation and closes client socket
    #             obj.delete(obj.exists)
    #         else:
    #             # Sends error message
    #             account.Account.delete(obj.exists)

    #     case "R":
    #         username = data[1]

    #         if obj.is_taken:
    #             message = f"M:{username}:SERVER:Username is unavailible".encode('utf-8')
    #             header = f"{len(message) :< {HEADER_LENGTH}}".encode('utf-8')
    #             client.send(header+message)
    #         else:
    #             clientDict[username] = obj.account_obj
        

def protocol_unpack(data):
    data = data.decode('UTF-8')
    type_ = data[0]
    print("UNPACK-TYPE:",type_)
    match type_:

        case "M":
            return Message.createMessageFromBuffer(data)
        
        #  # Register type -> call register method
        # case "R":
        #     username = data[1]
        #     is_taken = username in clientDict
        #     #obj = account.Account.registerAccount(client,is_taken,username)

        #     #return {"is_taken": is_taken,"account_obj": obj}
        
        # case "L":
        #     username = data[1]
        #     if username in clientDict:
        #         return {"exists": True, "account_obj": clientDict[username]}
        #     return {"exists": False} 

        # case "D":
        #     username = data[1]
        #     if username in clientDict:
        #         return {"exists": True, "account_obj": clientDict[username]}
        #     return {"exists": False} 

def broadcast(message):
    for client in clients:
        index = clients.index(client)
        username = usernames[index]
        message = f"M:{username}:SERVER:{message}"
        message = encoded_message(message)
        client.send(message)

# Function to handle clients'connections
def sendToClient(username, message):
    # print("username is " + username)
    # print("These are the clientID Dictionary ")
    # print(clientID)

    client = clientID[username]
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

            header = client.recv(HEADER_LENGTH).decode("utf-8").strip()
            data_length = int(header)
            data = client.recv(data_length)
            # print("HANDLE CLIENT DATA:",data)
            obj = protocol_unpack(data)
            protocol_action(obj)

        except:
            # Client Logs out or Crashes
            index = clients.index(client)
            clients.remove(client)
            client.close()
            username = usernames[index]
            # print("USERNAME:",username)
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
        
        data = client.recv(HEADER_LENGTH).decode('utf-8')
        # print("DATA 1:", data)
        data_length = int(data.strip())
        # print("DATA Length is ", data_length)
        data = client.recv(data_length).decode('utf-8')
        print("data is ", data)
        
        data = data.split(":")
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

       
        thread = threading.Thread(target=handle_client, args=(client,))
        thread.start()

def onConnection(username):
    # print(f'The username of this client is {username}')
    message = encoded_message(f'{username} has connected to the chat room')
    #broadcast(message)
    if username in queuedMessages.keys():
        for message in queuedMessages[username][:]:
            sendToClient(username, message.encode())
            queuedMessages[username].remove(message)

if __name__ == "__main__":
    receive()
