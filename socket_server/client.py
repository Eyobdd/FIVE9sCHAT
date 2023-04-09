## TODO
# 1. Write unit tests and say expected outputs -- Eyob
# 2. Write setup documentation (Aneesh)
# 4. Comment code (Eyob on socket), (Aneesh on GRPC)
# 5. Clean up code
# 6. Write decision documentation (Eyob on Socket), (Aneesh on GRPC), (Aneesh on intro and design strategy)
# 9. Create Uniform Error Code System -- future
# 10. Create decode abstraction.  -- if time


# Import modules used
import threading
import socket
import os
import signal
from message import Message

# Constants used in text styling
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

# Creates an encoded bitstring from a message using our wire protocol
def encoded_message(message):
    message = message.encode('utf-8')
    header = f"{len(message) :< {HEADER_LENGTH}}".encode('utf-8')
    return header+message

# Defined header length throughout wire protocol
HEADER_LENGTH = 10
HOST = '10.250.209.143'
# Create a socket and connect to the server
client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client.connect((HOST, 12340))


# User initially starts unnamed and unauthenticated
auth = False
username = ''

try:

    ## Display all existing accounts

    # Retrieves list from server of all existing accounts
    header = client.recv(HEADER_LENGTH).decode('utf-8').strip()
    data_length = int(header)
    data = client.recv(data_length).decode('utf-8')

    # Displays all accounts with their activity status
    allAccounts = data.split("|")[1:]
    print(bcolors.OKGREEN + "The server holds the following accounts." + bcolors.ENDC)
    for account in allAccounts:
        print(" -- > " + account)
    
    
    # goBack loop lets user reselect if they want to login or create an account
    goBack = True
    while goBack:
        
        # Asks user if they would like to login or create an account
        command = input("Type " + bcolors.BOLD + "C" + bcolors.ENDC + " to create an account. Type " + bcolors.BOLD + "L" + bcolors.ENDC + " to login in." )
        
        # Reprompt if user gives invalid answer
        while command != "C" and command != "L":
            print("Please select either C or L\n")
            command = input("Type " + bcolors.BOLD + "C" + bcolors.ENDC + " to create an account. Type " + bcolors.BOLD + "L" + bcolors.ENDC + " to login in." )


        # Authentication loop only broken if user goes back or is authenticated
        while not auth:

            # Asks for username and gives option to go back 
            print("Usernames must be alphanumeric characters.\n(Type "+bcolors.BOLD+"!"+bcolors.ENDC+" to go back)")
            username = input("Please enter a username:")

            # If user wants to create an account and submits a real username
            if command == "C" and username != "!":
                
                # Sends Create account request to server
                request_message = f"CA:{username}"
                request_message = encoded_message(request_message)
                client.send(request_message)

                # Awaits and receives server confirmation
                header = client.recv(HEADER_LENGTH).decode('utf-8')
                confirmation_length = int(header.strip())
                confirmation = client.recv(confirmation_length).decode('utf-8')
                
                # Takes the confirmation message only
                confirmation = confirmation.split(":",3)[3]
                
                # Checks if request is successful
                if confirmation == "Successful-Account-Creation.":
                    
                    # User is authorized
                    auth = True
                    goBack = False
                    
                    # Print confirmation message
                    print(bcolors.OKGREEN + confirmation + bcolors.ENDC)

                else:

                    # Print confirmation message
                    print(bcolors.FAIL + confirmation + bcolors.ENDC)

            # If user submits a real username and command type is L
            elif username != "!":
                
                # Send Login request to server
                request_message = f"L:{username}"
                request_message = encoded_message(request_message)
                client.send(request_message)

                # Awaits and recieves confirmation from server
                header = client.recv(HEADER_LENGTH).decode('utf-8').strip()
                confirmation_length = int(header.strip())
                confirmation = client.recv(confirmation_length).decode('utf-8')

                # Retrieve confirmation message
                confirmation = confirmation.split(":",3)[3]

                # Checks if request is successful
                if confirmation == "Login-Successful.":
                    # User is authorized
                    auth = True
                    goBack = False
                    
                    # Print confirmation message
                    print(bcolors.OKGREEN + confirmation + bcolors.ENDC)

                else:
                    
                    # Print confirmation message
                    print(bcolors.FAIL + confirmation + bcolors.ENDC)
            
            # If username is !, break out of auth loop and reprompt commands
            else:
                break            

    # Thread that listens for communications from the server
    def client_receive():
        while True:
            try:

                # Receives data sent by server
                data_header = client.recv(HEADER_LENGTH).decode('utf-8')
                data_length = int(data_header.strip())
                data = client.recv(data_length).decode('utf-8')

                # Converts received data into a message object
                data = Message.createMessageFromBuffer(data)

                # Checks if message sender is SERVER
                if (data.sender == "SERVER"):
                    
                    # If message object doesn't encode properly
                    if data.data[0] == "<":
                        continue

                    # If SERVER is sending a list of active accounts
                    if data.data[0:3] == "LA|":

                        # Unpacks the sent list 
                        allAccounts = data.data.split("|")[1:]
                        
                        # Prints list
                        print(bcolors.OKGREEN + "The server holds the following accounts." + bcolors.ENDC)
                        for account in allAccounts:
                            print(" -- > " + account)

                    # If SERVER Confirms account is successfully deleted
                    elif data.data == "Account-Successfully-Deleted":

                        # Print message to console
                        print("Your account has been deleted. Your client connection will end. Bye, Bye")
                        print(bcolors.BOLD + bcolors.FAIL + "EXITING CLIENT PROGRAM." + bcolors.ENDC)
                        
                        # Exits terminal and closes socket
                        os.kill(os.getpid(), signal.SIGINT)
                    
                    # If SERVER cannot find and delete account 
                    elif data.data == "Account-Does-Not-Exist":
                        print(bcolors.FAIL + data.data + bcolors.ENDC)

                    # If SERVER is sending a broadcast message
                    else:
                        print(bcolors.OKCYAN + "[" + data.sender + "] " + bcolors.ENDC + data.data)


                # If the message is sent from another user
                if data.sender != "SERVER":
                    print(bcolors.OKCYAN + "[" + data.sender + "] " + bcolors.ENDC + data.data)

            # Any general errors are caught here
            except Exception as e:
                print(bcolors.WARNING +'Error! '+ str(e) + bcolors.ENDC)
                client.close()
                break       


    # Thread that sends authenticated communication to the server
    def client_send():
        
        while True:

            # Asks user for input
            inp = input(bcolors.BOLD +"COMMANDS" + bcolors.ENDC + ": " + bcolors.BOLD + "\n" +"LA" + bcolors.ENDC + " - List accounts. "+ bcolors.BOLD + "\n" + "USERNAME-> MESSAGE" + bcolors.ENDC+ " - Send USERNAME MESSAGE." + "\n" + bcolors.BOLD + "DA" + bcolors.ENDC + " - Delete your account."+"\n" + bcolors.BOLD + "Q" + bcolors.ENDC + " - Quit client program."+"\n")
            
            # If user enters nothing
            if inp == "":
                print(bcolors.WARNING + "Empty input" + bcolors.ENDC)
            
            # User enters something
            else:

                # If input is not a message
                if "->" not in inp:

                    # Check if it List Accounts request
                    if inp == "LA":

                        # Sends List Accounts request
                        message = f"LA:{username}"
                        message = encoded_message(message)
                        client.send(message)
                        
                    # Check if it is a Delete Account request
                    elif inp == "DA":
                        
                        # Sends delete account request with authorized username
                        message = f"DA:{username}"
                        message = encoded_message(message)
                        client.send(message)

                    # Check if the user is trying to quit the program
                    elif inp == "Q":
                        
                        # Prints exit message
                        print(bcolors.BOLD + bcolors.FAIL + "EXITING CLIENT PROGRAM." + bcolors.ENDC)
                        
                        # Exits terminal and closes socket
                        os.kill(os.getpid(), signal.SIGINT)
                        break

                    # User submitted invalid message syntax
                    else:
                        # Prints syntax warning message
                        print(bcolors.WARNING + "NEED TO SPECIFY USER. Correct usage: USER-> Message." + bcolors.ENDC)
                
                # User submitted valid message syntax
                else:
                    # Breaks input into recipient and message based on "->"
                    inputList = inp.split("->")
                    recipient = inputList[0]
                    message = inputList[1]

                    # Creates a message object
                    message = Message(recipient, username, message)
                    message = message.encode()

                    # Sends message to server
                    client.send(message)


            
    # USER IS NOW AUTHENTICATED
    # Open up thread to send and receive messages from server
    receive_thread = threading.Thread(target=client_receive)
    receive_thread.start()

    send_thread = threading.Thread(target=client_send)
    send_thread.start()

# If user exits with ^C it is caught here
except KeyboardInterrupt:
    print(bcolors.BOLD + bcolors.FAIL + "EXITING CLIENT PROGRAM." + bcolors.ENDC)
