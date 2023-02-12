import socket
import select
# Used to match specific error codes
import errno
import sys

HEADER_LENGTH = 10
IP = "127.0.0.1"
PORT = 1234

# Basic user input for username
my_username = input("Username: ")

# Create the socket
client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

# Connect client socket to server IP and Port
client_socket.connect((IP, PORT))

# Prevents recieve functionality from blocking
client_socket.setblocking(False)

# Create client username and header
username = my_username.encode('utf-8')
username_header = f"{len(username):<{HEADER_LENGTH}}".encode('utf-8')

# Send client username to the server
client_socket.send(username_header + username)

# TODO Current implementation does not allow for users to change usernames

while True:
    message = input(f"{my_username} > ")

    # Checks if a user actually inputed anything
    if message:

        # Encodes message and creates a header that indicates the length of that message
        message = message.encode('utf-8')
        message_header = f"{len(message) :< {HEADER_LENGTH}}".encode('utf-8')
        
        # Sends message to server
        client_socket.send(message_header+message)
    
    # Checks if there are any incoming messages
    try:
        while True:
            
            username_header = client_socket.recv(HEADER_LENGTH)
            
            # If there is no header recieved user has been disconnected by the server
            if not len(username_header):
                print("Connection closed by the server")
                sys.exit()

            # Decodes incoming username
            username_length = int(username_header.decode('utf-8').strip())
            username = client_socket.recv(username_length).decode('utf-8')

            # Gets message header
            message_header = client_socket.recv(HEADER_LENGTH)
            
            # Decodes incoming message
            message_length = int(message_header.decode('utf-8').strip())
            message = client_socket.recv(message_length).decode('utf-8')

            print(f"{username} > {message}")

    except IOError as e:

        # If error isn't an error indicating no new messages in the stream exit.
        if e.errno != errno.EAGAIN and e.errno != errno.EWOULDBLOCK :
            print("Reading error", str(e))
            sys.exit()

        # If error indicates no new messages continue to next loop cycle
        continue

    except Exception as e:
        print ("General error", str(e))
        pass