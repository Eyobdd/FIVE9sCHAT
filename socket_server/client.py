## TODO
# 1. Write unit tests and say expected outputs -- Eyob
# 2. Write setup documentation
# IMPORTANT 3. Set up port forwarding
# 4. Comment code (Eyob on socket), (Aneesh on GRPC)
# 5. Clean up code
# 6. Write decision documentation (Eyob on Socket), (Aneesh on GRPC), (Aneesh on intro and design strategy)
# 7. Add Go Back in the Create or Login window -> (Eyob on Socket), (Aneesh on GRPC)
# 8. Add Broadcast in GPRC
# 9. Create Uniform Error Code System



import threading
import socket
from message import Message
import os
import signal
import errno
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

try:
    command = input("Press C to Create an Account and L to Login")
    while command != "C" and command != "L":
        print("Please select either C or L\n")
        command = input("Press C to Create an Account and L to Login")

    while not auth:
        username = input("Please enter a username:")
        print("line 38")
        if command == "C":
            print("line 40")
            request_message = f"CA:{username}"
            request_message = encoded_message(request_message)
            client.send(request_message)

            header = client.recv(HEADER_LENGTH).decode('utf-8')
            confirmation_length = int(header.strip())
            confirmation = client.recv(confirmation_length).decode('utf-8')
            
            print("CONFIRMATION:",confirmation.split(":"))
            confirmation = confirmation.split(":")[3]
            
            if confirmation == "Successful-Account-Creation.":
                auth = True
                print(bcolors.OKGREEN + confirmation + bcolors.ENDC)
            else:
                username = ''
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
                    if data.data[0] == "<":
                        continue
                    if data.data[0:3] == "LA|":
                        allAccounts = data.data.split("|")[1:]
                        print(bcolors.OKGREEN + "The server holds the following accounts." + bcolors.ENDC)
                        for account in allAccounts:
                            print(" -- > " + account)

                    elif data.data == "Login-Successful":
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
                    elif data.data == "Account-Successfully-Deleted":
                        print("Your account has been deleted. Your client connection will end. Bye, Bye")
                        print(bcolors.BOLD + bcolors.FAIL + "EXITING CLIENT PROGRAM." + bcolors.ENDC)
                        os.kill(os.getpid(), signal.SIGINT)
                    elif data.data == "Account-Does-Not-Exist":
                        print(bcolors.FAIL + data.data + bcolors.ENDC)
                    else:
                        print(bcolors.OKCYAN + "[" + data.sender + " BROADCAST] " + bcolors.ENDC + data.data)


                # TODO Print errors in red - check if message is an error

                # TODO we should catch all server messages from above -- so we should say if data.sender is not SERVER
                if data.sender != "SERVER":
                    print(bcolors.OKCYAN + "[" + data.sender + "] " + bcolors.ENDC + data.data)
            
            except Exception as e:
                print(bcolors.WARNING +'Error! '+ str(e) + bcolors.ENDC)
                client.close()
                break
            

    def client_send():
        
        while True:
            inp = input(bcolors.BOLD +"COMMANDS" + bcolors.ENDC + ": " + bcolors.BOLD + "\n" +"LA" + bcolors.ENDC + " - List accounts. "+ bcolors.BOLD + "\n" + "USERNAME-> MESSAGE" + bcolors.ENDC+ " - Send USERNAME MESSAGE." + "\n" + bcolors.BOLD + "DA" + bcolors.ENDC + " - Delete your account."+"\n" + bcolors.BOLD + "Q" + bcolors.ENDC + " - Quit client program."+"\n")
            if inp == "":
                print(bcolors.Warning + "Empty input" + bcolors.ENDC)
            else:
                if "->" not in inp:
                    if inp == "LA":
                        # List Accounts
                        message = f"LA:{username}"
                        message = encoded_message(message)
                        client.send(message)
                        
                    elif inp == "DA":
                        # Delete Account
                        
                        # Uses the authorized username
                        message = f"DA:{username}"
                        message = encoded_message(message)
                        client.send(message)

                    elif inp == "Q":
                        # Quit
                        print(bcolors.BOLD + bcolors.FAIL + "EXITING CLIENT PROGRAM." + bcolors.ENDC)
                        os.kill(os.getpid(), signal.SIGINT)
                        break

                    else:
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

except KeyboardInterrupt:
    print(bcolors.BOLD + bcolors.FAIL + "EXITING CLIENT PROGRAM." + bcolors.ENDC)
