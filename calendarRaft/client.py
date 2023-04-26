# Import modules used
import sys
import threading
import socket
import os
import signal
from message import Message
from datetime import datetime

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
HOST = '127.0.0.1'

# Create a socket and connect to the server


auth = False
username = sys.argv[1]



# Thread that listens for communications from the server
def client_receive(connection):
    global SERVERSTATE
    while True:
        try:

            # Receives data sent by server
            data_header = connection.recv(HEADER_LENGTH).decode('utf-8')
            data_length = int(data_header.strip())
            data = connection.recv(data_length).decode('utf-8')

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

                # If SERVER creates an event
                elif data.data == "Event-Created":
                    print(bcolors.OKBLUE + data.data + bcolors.ENDC)
                
                # If SERVER deletes an event
                elif data.data == "Event-Deleted":
                    print(bcolors.OKBLUE + data.data + bcolors.ENDC)

                # If SERVER is sending a broadcast message
                else:
                    print(bcolors.OKCYAN + "[" + data.sender + "] " + bcolors.ENDC + data.data)


            # If the message is sent from another user
            if data.sender != "SERVER":
                print(bcolors.OKCYAN + "[" + data.sender + "] " + bcolors.ENDC + data.data)

        # Any general errors are caught here
        except Exception as e:

            print(bcolors.WARNING +'SERVER DROPPED. RECONNECTING. PRESS ENTER. ' + bcolors.ENDC)
            connection.close()
            SERVERSTATE = 10
            sys.exit()

# Thread that sends authenticated communication to the server
def client_send(connection, state):
    while True:
        if state != SERVERSTATE:
            sys.exit()
        # Asks user for input
        inp = input(bcolors.BOLD +"COMMANDS" + bcolors.ENDC + ": " + bcolors.BOLD + "\n" +"LA" + bcolors.ENDC + " - List accounts. "+ bcolors.BOLD + "\n" + "USERNAME-> MESSAGE" + bcolors.ENDC+ " - Send USERNAME MESSAGE." + "\n" + bcolors.BOLD + "DA" + bcolors.ENDC + " - Delete your account."+"\n" + bcolors.BOLD + "Q" + bcolors.ENDC + " - Quit client program."+"\n")
        
        # If user enters nothing
        if inp == "":
            print(bcolors.WARNING + "Empty input" + bcolors.ENDC)
        
        # User enters something
        else:

            # If input is not a message
            if "->" not in inp:

                if inp == "DE":

                    title = ''
                    validNum = False
                    while title == '':
                        title = input("Event Title: ")
                        title = title.strip()
                    
                    while not validNum:
                        try:
                            day = input("Enter the event date (YYYY-MM-DD): ")
                            day = day.strip()
                            date = datetime.strptime(day, "%Y-%m-%d")
                            day = date.timetuple().tm_yday
                            validNum = True
                        except:
                            continue

                    print("Username: "+ username +" | Title: "+title+" | Day:"+ str(day))

                    message = f"DE:{username}:{title}:{day}"
                    message = encoded_message(message)
                    connection.send(message)
                        

                if inp == "CE":
                    title = ''
                    day = ''
                    validNum = False

                    while title.strip() == '':
                        title = input("Event Title: ")

                    while not validNum:
                        try:
                            day = input("Enter a date (YYYY-MM-DD): ")
                            date_str = day.strip()
                            date = datetime.strptime(date_str, "%Y-%m-%d")
                            day = date.timetuple().tm_yday

                            validNum = True
                        except Exception as error:
                            print("something went wrong...", error)
                            continue
                    
                    validNum = False

                    while not validNum:
                        try:
                            start_time = input("Enter a start time in 24H-time (HH:MM): ")
                            hours, minutes = map(int, start_time.split(':'))
                            start_time = hours * 60 + minutes
                            if start_time < 60*24:
                                validNum = True
                            else:
                                print("Enter a start time on the same day")
                        except:
                            continue
                    
                    validNum = False

                    while not validNum:
                        try:
                            end_time = input("How long is this event? (in minutes): ")
                            end_time = start_time + int(end_time.strip())
                            validNum = True
                        except:
                            continue
                        

                    message = f"CE:{username}:{title}:{day}:{start_time}:{end_time}"
                    message = encoded_message(message)
                    connection.send(message)

                # Check if it List Accounts request
                if inp == "LA":

                    # Sends List Accounts request
                    message = f"LA:{username}"
                    message = encoded_message(message)
                    connection.send(message)
                    
                # Check if it is a Delete Account request
                elif inp == "DA":
                    
                    # Sends delete account request with authorized username
                    message = f"DA:{username}"
                    message = encoded_message(message)
                    connection.send(message)

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
                connection.send(message)

while True:
    # # TRY TO CONNECT TO SERVER 1
    server1GoesThrough = True

    try:
        client1 = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client1.connect((HOST, 12340))
        request_message = f"L:{username}"
        request_message = encoded_message(request_message)
        client1.send(request_message)
        # Keep track of leader server
        SERVERSTATE = 1
        

        receive_thread1 = threading.Thread(target=client_receive, args=[client1])
        receive_thread1.start()

        send_thread1 = threading.Thread(target=client_send, args= [client1, 1])
        send_thread1.start()
    except:
        server1GoesThrough = False

    if server1GoesThrough:
        while receive_thread1.is_alive() or send_thread1.is_alive():
            x = 3

    server2GoesThrough = True

    # TRY TO CONNECT TO SERVER 2
    try:

        client2 = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client2.connect((HOST, 12341))
        request_message = f"L:{username}"
        request_message = encoded_message(request_message)
        client2.send(request_message)

        SERVERSTATE = 2
        receive_thread2 = threading.Thread(target=client_receive, args=[client2])
        receive_thread2.start()

        send_thread2 = threading.Thread(target=client_send, args= [client2, 2])
        send_thread2.start()

    except:
        server2GoesThrough = False


    if server2GoesThrough:
        while receive_thread2.is_alive() or send_thread2.is_alive():
            x = 3

    server3GoesThrough = True
    # TRY TO CONNECT TO SERVER 3
    try:
        client3 = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client3.connect((HOST, 12342))
        request_message = f"L:{username}"
        request_message = encoded_message(request_message)
        client3.send(request_message)
        SERVERSTATE = 3
        receive_thread3 = threading.Thread(target=client_receive, args=[client3])
        receive_thread3.start()

        send_thread3 = threading.Thread(target=client_send, args= [client3, 3])
        send_thread3.start()
    except:
        server3GoesThrough = False
    if server3GoesThrough:
        while receive_thread3.is_alive() or send_thread3.is_alive():
            x = 3

