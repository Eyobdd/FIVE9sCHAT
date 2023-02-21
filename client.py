import threading
import socket
from message import Message

HEADER_LENGTH = 10

client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client.connect(('127.0.0.1', 12340))
auth = False
username = ''

class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

def encoded_message(message):
    message = message.encode('utf-8')
    header = f"{len(message) :< {HEADER_LENGTH}}".encode('utf-8')
    return header+message

command = input("Press C to Create an Account and L to Login")
while command != "C" and command != "L":
    print("Please select either C or L\n")
    command = input("Press C to Create an Account and L to Login")

while not auth:
    username = input("Please enter a username:")
    while username =='':
        print("Please enter a username!")
        username = input("Please enter a username:")

    if command == "C":
        request_message = f"CA:{username}"
        request_message = encoded_message(request_message)
        client.send(request_message)

        header = client.recv(HEADER_LENGTH).decode('utf-8')
        confirmation_length = int(header.strip())
        confirmation = client.recv(confirmation_length).decode('utf-8')

        # print("CONFIRMATION:",confirmation.split(":"))
        confirmation = confirmation.split(":")[3]
        
        if confirmation == "Successful-Account-Creation.":
            auth = True
            print(bcolors.OKGREEN + confirmation + bcolors.ENDC)
        else:
            print(bcolors.FAIL + confirmation + bcolors.ENDC)

    else:
        request_message = f"L:{username}"
        request_message = encoded_message(request_message)
        client.send(request_message)

        header = client.recv(HEADER_LENGTH).decode('utf-8').strip()
        # print("HEADER:",header)
        confirmation_length = int(header.strip())
        confirmation = client.recv(confirmation_length).decode('utf-8')

        confirmation = confirmation.split(":")[3]

        if confirmation == "Login-Successful.":
            auth = True
            print(bcolors.OKGREEN + confirmation + bcolors.ENDC)
        else:
            print(bcolors.FAIL + confirmation + bcolors.ENDC)

# def authenticate():
#     print(bcolors.OKGREEN + "Would you like to CREATE an account or LOGIN to an existing user from above? " + bcolors.ENDC)
#     decision = input("Type " + bcolors.BOLD + "C" + bcolors.ENDC + " to create an account. Type " + bcolors.BOLD + "L" + bcolors.ENDC + " to login in." )
#     while (decision != "C" and decision != "L"):
#         print("please type a valid decision.")
#         decision = input("Type " + bcolors.BOLD + "C" + bcolors.ENDC + " to create an account. Type " + bcolors.BOLD + "L USERNAME" + bcolors.ENDC + " to login into USERNAME." )
#     if decision == "C":
#         while not auth:
#         # Create Account
#             if auth:
#                 break
#             usernameSubmit = input("What username would you like to create?\n")
#                 # WE DID NOT make seperate class like Message because it is trivial
#             create_account_command = f"CA:{usernameSubmit}"
#             create_account_command = encoded_message(create_account_command)
#                 # create_account_command.encode('UTF-8')
#             client.send(create_account_command)
#             username = usernameSubmit
#             # print("username outside of while loop: ", username)
#             # self.username = username
#     elif decision == "L":
#         # Attempt to Login
#         print("login")

    
def client_receive():
    while True:
        try:
            data_header = client.recv(HEADER_LENGTH).decode('utf-8')
            # print("HEADER:",data_header)
            data_length = int(data_header.strip())
            data = client.recv(data_length).decode('utf-8')
            # print("INCOMING DATA "+str(data)+ "\n")
            data = Message.createMessageFromBuffer(data)
            # Check for server messages
            if (data.sender == "SERVER"):
                if data.data == "Login-Successful":
                    auth = True
                    print(bcolors.OKGREEN + data.data + bcolors.ENDC)
                elif data.data == "Login-Failed":
                    print(bcolors.FAIL + data.data + bcolors.ENDC)
                elif data.data == "Successful-Account-Creation.":
                    auth = True
                    print("The username after authentication is", username)
                    print("Hit enter to continue.")
                    print(bcolors.OKGREEN + data.data + bcolors.ENDC)
                elif data.data == "Username-Already-Exists.":
                    print(bcolors.FAIL + data.data + bcolors.ENDC)
            # TODO Print errors in red - check if message is an error
            print(bcolors.OKCYAN + "[" + data.sender + "] " + bcolors.ENDC + data.data)
        except Exception as e:
            print(bcolors.WARNING +'Error! '+ str(e) + bcolors.ENDC)
            client.close()
            break

def client_send():
    
    print("auth in the send thread,", auth)
    print("username in the send thread is ", username)
    while True:
        inp = input("What would you like to say? To whom?\n(recipient username -> message input format)\n")
        if "->" not in inp:
            print(bcolors.WARNING + "NEED TO SPECIFY USER. Correct usage: USER-> Message." + bcolors.ENDC)
        else:
            inputList = inp.split("->")
            recipient = inputList[0]
            message = inputList[1]
            message = Message(recipient, username, message)
            message = message.encode()
            # print("MESSAGE-CS:",message)
            print("The client username: " + username + " is attempting to send this message to the server.")
            # print(message)
            #TODO Check for byte overflow 1024            
            client.send(message)

        
# USER IS NOW AUTHENTICATED

# Open up client to send and receive messages from server
receive_thread = threading.Thread(target=client_receive)
receive_thread.start()

send_thread = threading.Thread(target=client_send)
send_thread.start()