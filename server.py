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

HEADER_LENGTH = 10

def protocol_CLIENT_RECIEVE(client_socket):
    
    first_header = client_socket.recv(HEADER_LENGTH)
    second_header_length = int(first_header.decode('utf-8').strip())

    second_header = client_socket.recv(second_header_length).decode('utf-8').split(":")
    type_ = second_header[0]

    match type_:
        # Message from Server to Client Protocol (MtC:Sender Username: Message)
        case "MtC":
            
            sender = second_header[1]
            message = second_header[2]

            return f"{sender}->{message}"


def protocol_CLIENT_SEND(type_, data, client_socket) -> (Success: bool, message: str):
    
    match type_:
        
        # Send Message to Server Protocol
        # (MtS:Recipient Username:Sender Username: Message)
        case "MtS":

            # Extracts parsed message data
            recipient, sender, message = data

            # Creates message request
            send_msg_request = f"MtS:{recipient}:{sender}:{message}".encode('utf-8')
            send_msg_request_header = f"{len(send_msg_request) :< {HEADER_LENGTH}}".encode('utf-8')

            # Sends message request to server
            client_socket.send(send_msg_request_header+send_msg_request)

            # Waits for server return call
            verification_length = int(client_socket.recv(HEADER_LENGTH).decode('utf-8').strip())
            verification = client_socket.recv(verification_length).decode('utf-8').split(":")

            # Shape of return should be (MV:Validation:Validation Message)
            success = verification[1] == 1
            message = verification[2]
            
            return (success, message)

        # Send Login Protocol (L:Username)
        case "L":

            # Creates a Login Request
            login_request = f"L:{data}".encode('utf-8')
            login_request_header = f"{len(login_request) :< {HEADER_LENGTH}}".encode('utf-8')
            
            # Send login request to server
            client_socket.send(login_request_header+login_request)

            # Waits for server return call
            verification_length = int(client_socket.recv(HEADER_LENGTH).decode('utf-8').strip())
            verification = client_socket.recv(verification_length).decode('utf-8').split(":")

            # Shape of return should be (L:Validation:Validation Message)
            success = verification[1] == 1
            message = verification[2]
            
            return (success, message)
            


        # Send Register Account Protocol (RA:Username)
        case "RA":

            # Creates a Register Account Request
            register_request = f"RA:{data}".encode('utf-8')
            register_request_header = f"{len(register_request) :< {HEADER_LENGTH}}".encode('utf-8')

            # Send register request to server
            client_socket.send(register_request_header+register_request)

            # Waits for server return call
            verification_length = int(client_socket.recv(HEADER_LENGTH).decode('utf-8').strip())
            verification = client_socket.recv(verification_length).decode('utf-8').split(":")

            # Shape of return should be (RA:Validation:Validation Message)
            success = verification[1] == 1
            message = verification[2]
            
            return (success, message)

        case "DA":

            # Creates a Delete Account Request
            delete_request = f"RA:{data}".encode('utf-8')
            delete_request_header = f"{len(delete_request) :< {HEADER_LENGTH}}".encode('utf-8')

            # Send delete request to server
            client_socket.send(delete_request_header+delete_request)

            # Waits for server return call
            verification_length = int(client_socket.recv(HEADER_LENGTH).decode('utf-8').strip())
            verification = client_socket.recv(verification_length).decode('utf-8').split(":")

            # Shape of return should be (DA:Validation:Validation Message)
            success = verification[1] == 1
            message = verification[2]
            
            return (success, message)            


def protocol_SERVER(client_socket): 

    first_header = client_socket.recv(HEADER_LENGTH)
    second_header_length = int(first_header.decode('utf-8').strip())

    second_header = client_socket.recv(second_header_length).decode('utf-8').split(":")
    type_ = second_header[0]

    match type_:

        # Message to Server Protocol
        # (MtS:Recipient Username:Sender Username:Message)
        #   -> (MtS:Recipient Username:Sender Username:Message)
        #   -> (MtC:Sender Username: Messsage)
        case "MtS":

            # Gets recipient socket from header
            recipient = second_header[1]
            recipient_socket = clientID[recipient]

            # Gets sender information
            sender = second_header[2]
            
            # Retrieves the message to be sent in byte form
            message = second_header[3]

            # TODO Check to see if recipient is online. If no send message delay message or username doesn't exist error
            if recipient not in aliases:
                # return error to client
                pass
            
            if  recipient not in clients:
                # queue message for recipient
                # notifiy sender the recipient is offline
                pass
            


            # Creates the New Header for the message to the recipient
            message_header = f"MtC:{sender}:{message}".encode('utf-8')
            first_header = f"{len(message_header) :< {HEADER_LENGTH}}".encode('utf-8')
            
            
            # Sends message to recipient 
            return recipient_socket.send(first_header+message_header)
        
        # Login Protocol (Decodes header of L:Username) -> (L:Validation:Validation Message)
        case "L":

            username = second_header[1]

            # Well treat 0 as False and 1 as True
            if username not in aliases:
                verification_header = f"L:0:User is not registered.".encode('utf-8')
            else:
                clients.add(client_socket)
                verification_header = f"L:1:User successfully Logged-In.".encode('utf-8')

            first_header = f"{len(verification_header) :< {HEADER_LENGTH}}".encode('utf-8')
            
            # Sends respose to client
            return client_socket.send(first_header+verification_header)

        # Register Account Protocol (RA:Username) -> (RA:Validation:Validation Message)
        case "RA":

            username = second_header[1]
            
            if username not in aliases:

                # Connect user and add them to server info
                # TODO Should the user be logged in automatically on successful register?
                # clients.add(username)
                aliases.add(username)
                clientID[username] = client_socket

                verification_header = f"RA:1:User successfully registered as {username}".encode('utf-8')
            else:
                # Rejects request
                verification_header = f"RA:0:The username {username} is taken.".encode('utf-8')

            first_header = f"{len(verification_header) :< {HEADER_LENGTH}}".encode('utf-8')
            
            # Sends response to client
            return client_socket.send(first_header+verification_header)
            
        # Delete Account Protocol (DA:Username) -> (DA:Validation:Validation Message)
        case "DA":
            
            username = second_header[1]
            
            if username not in aliases:
                verification_header = f"DA:0:The account {username} does not exist.".encode('utf-8')
            else:
                try:
                    clientID.del(username)
                    aliases.remove(username)
                    clients.remove(username)
                    verification_header = f"DA:1:The account {username} successfully deleted.".encode('utf-8')
                except Exception as e:
                    verification_header = f"DA:0:ServerError -- Unable to delete the account {username}.".encode('utf-8')
                    print(f"ServerError -- The account {username} unable to be deleted:", str(e))
                    continue

            first_header = f"{len(verification_header) :< {HEADER_LENGTH}}".encode('utf-8')
            client_socket.send(first_header+verification_header)


            return client_socket.close()


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
