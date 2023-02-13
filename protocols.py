import struct

HEADER_LENGTH = 10
ENCODING = 'utf-8'

def recv_message(client_socket):
    header = socket.recv(HEADER_LENGTH)
    message_length, = struct.unpack('!I', header)

    message = socket.recv(message_length).decode(ENCODING)
    return message

def send_message(message, client_socket):
    message = message.encode(ENCODING)
    header = struct.pack('!I', len(message))
    client_socket.send(header + message)

def protocol_CLIENT_RECIEVE(client_socket):
    message = recv_message(client_socket)
    parts = message.split(":")
    type_ = parts[0]

    if type_ == "MtC":

        sender, message = parts[1], parts[2]
        
        return f"{sender}->{message}"
    
    if type_ in ("RA", "DA", "L"):

        validation, message = part[1] == 1, part[2]

        return validation, message
    
    return raise ValueError("Invalid Type Error");


def protocol_CLIENT_SEND(type_, data, client_socket):
    
    match type_:
        
        # Send Message to Server Protocol
        # (MtS:Recipient Username:Sender Username: Message)
        case "MtS":

            # Extracts parsed message data
            recipient, sender, message = data

            # Creates message request
            message = f"MtS:{recipient}:{sender}:{message}"

        # Send Login Protocol (L:Username)
        case "L":

            # Creates a Login Request
            message = f"L:{data}"
            
        # Send Register Account Protocol (RA:Username)
        case "RA":

            # Creates a Register Account Request
            message = f"RA:{data}"

        case "DA":

            # Creates a Delete Account Request
            message = f"RA:{data}"

        case:
            raise ValueError("Invalid Message Type for PCS")

        send_message(message, client_socket)



def protocol_SERVER(client_socket,clients,aliases,clientID): 

    second_header = recieve_message(client_socket).split(":")
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
            message = f"MtC:{sender}:{message}"         
            
            # Sends message to recipient 
            return send_message(message,recipient_socket)

        # Login Protocol (Decodes header of L:Username) -> (L:Validation:Validation Message)
        case "L":

            username = second_header[1]

            # Well treat 0 as False and 1 as True
            if username not in aliases:
                verification = f"L:0:User is not registered."
            else:
                clients.add(client_socket)
                verification = f"L:1:User successfully Logged-In."

            
            # Sends respose to client
            return send_message(verification,client_socket)

        # Register Account Protocol (RA:Username) -> (RA:Validation:Validation Message)
        case "RA":

            username = second_header[1]
            
            if username not in aliases:

                # Connect user and add them to server info
                # TODO Should the user be logged in automatically on successful register?
                # clients.add(username)
                aliases.add(username)
                clientID[username] = client_socket

                verification = f"RA:1:User successfully registered as {username}"
            else:
                # Rejects request
                verification = f"RA:0:The username {username} is taken."
            
            # Sends response to client
            return send_message(verification,client_socket)
            
        # Delete Account Protocol (DA:Username) -> (DA:Validation:Validation Message)
        case "DA":
            
            username = second_header[1]
            
            if username not in aliases:
                verification = f"DA:0:The account {username} does not exist."
            else:
                try:
                    clientID.del(username)
                    aliases.remove(username)
                    clients.remove(username)
                    verification = f"DA:1:The account {username} successfully deleted."
                except Exception as e:
                    verification = f"DA:0:ServerError -- Unable to delete the account {username}."
                    print(f"ServerError -- The account {username} unable to be deleted:", str(e))
                    continue

            
            send_message(verification,client_socket)

            return client_socket.close()
