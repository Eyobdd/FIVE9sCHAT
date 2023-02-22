import threading
from tkinter import *
from tkinter import simpledialog
import os
import signal
import grpc

import chat_pb2 as chat
import chat_pb2_grpc as rpc

#  Host and Port of our server to connect to 
address = '10.250.52.110'
port = 12341

# Colors to print on the terminal
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

class Client:

    def __init__(self):

        # Init an temporary account to authorize 
        self.account = chat.Account()
        self.account.loggedIn = False
        self.account.created = True
       
        # connect to the gRPC channel
        channel = grpc.insecure_channel(address + ':' + str(port))
        self.conn = rpc.ChatServerStub(channel)

        # List all accounts so that user can see what accounts they can log into
        self.listAccounts()
        
        # Let user create an account or login
        self.authenticate()
       
        # deliver any queued messages to user
        self.dequeue()

        # Once the user is authenticated, we can open up the listening and send thread.
        recieve_thread = threading.Thread(target=self.client_recieve)
        send_thread =  threading.Thread(target=self.client_send)

        recieve_thread.start()
        send_thread.start()

    # Allows user to create or log into an account
    def authenticate(self):
        goBack = True
        while goBack:
            print(bcolors.OKGREEN + "Would you like to CREATE an account or LOGIN to an existing user from above? " + bcolors.ENDC)
            command = input("Type " + bcolors.BOLD + "C" + bcolors.ENDC + " to create an account. Type " + bcolors.BOLD + "L" + bcolors.ENDC + " to login in." )
            while (command != "C" and command != "L"):
                print("please type a valid command.")
                command = input("Type " + bcolors.BOLD + "C" + bcolors.ENDC + " to create an account. Type " + bcolors.BOLD + "L" + bcolors.ENDC + " to login into username." )
            if command == "C":
                # Create Account
                # Attempt to create an account until our user account is logged in
                while not self.account.loggedIn:
                    print("Username must be alphanumeric characters.\n(Type "+bcolors.BOLD+"!"+bcolors.ENDC+" to go back)")
                    username = input("Please enter a username:")
                    if username == "!":
                        break
                    acc = chat.Account()
                    acc.username = username
                    acc.created = False
                    acc.loggedIn = False

                    # Submit account to server for creation -- server will return accVerification 
                    accVerification = self.conn.createAccount(acc)

                    # Server will return accVerification.created = True if it was succesfully created.
                    if accVerification.created:
                        self.account = accVerification
                        goBack = False
                        print(bcolors.OKGREEN + "Successful-Account-Creation." + bcolors.ENDC)
                    else:
                        print(bcolors.FAIL + "Account creation failed. Make sure it's a user that doesn't already exist." + bcolors.ENDC)
            elif command == "L":
                # Attempt to Login
                # Attempt to create an account until our user account is logged in

                    while not self.account.loggedIn:
                        print("username must be alphanumeric characters.\n(Type "+bcolors.BOLD+"!"+bcolors.ENDC+" to go back)")
                        username = input("What username would you like to Log into?\n")
                        if username == "!":
                            break

                        acc = chat.Account()
                        acc.username = username
                        acc.created = False
                        acc.loggedIn = False

                        # Submit account to server to log in -- server will return accVerification
                        accVerification = self.conn.login(acc)

                        # Server will set accVerification.loggedIn = True if it is logged in
                        if accVerification.loggedIn:
                            self.account = accVerification
                            print(bcolors.OKGREEN + "Login-Successful." + bcolors.ENDC)
                            goBack = False
                        else:
                            print(bcolors.FAIL + "Login failed. Make sure user exists and/or that user isn't already logged in (active)" + bcolors.ENDC)

    # Thread to receive messages from Server
    def client_recieve(self):
        
        # We wait for messages in the ChatStream (Server)
        for message in self.conn.ChatStream(self.account):

            # Only accept messages that are meant for the client (Broadcast filtering) 
            # or messages that are meant to be read by all users
            if (message.recipient == self.account.username) or (message.recipient == "all"):
                print(bcolors.OKCYAN + "[" + message.sender + "] " + bcolors.ENDC + message.message)

    # List Accounts that exist on Server (actice and inactive)
    def listAccounts(self):

        allAccounts = self.conn.listAccounts(chat.Empty())

        if allAccounts.message == '':
            print("The server has no accounts.")
        else:
            
            # allAccounts returned from the server will have all the accounts merged as a string
            # so we need to split them off of "|" which is how we constructed them in the server
            allAccounts = allAccounts.message.split("|")
            print(bcolors.OKGREEN + "The server holds the following accounts." + bcolors.ENDC)
            for account in allAccounts:
                print(" -- > " + account)

    # Get recipient from user input
    def unpackRecipient(self, message):
        recipient = message.split("->")
        recipient = recipient[0]
        return recipient

    # Get message from user input
    def unpackMessage(self, message):
        message = message.split("->")
        message = message[1]
        return message

    def deleteAccount(self):
        # self.conn.deleteAccount(self.account) will return a chat.Str proto message, and
        # our sucessful verification code is DELETED.
        if self.conn.deleteAccount(self.account).message == "DELETED.":
            print("Your account has been deleted. Your client connection will end. Bye, Bye")
            print(bcolors.BOLD + bcolors.FAIL + "EXITING CLIENT PROGRAM." + bcolors.ENDC)
            os.kill(os.getpid(), signal.SIGINT)
        else:
            print(bcolors.FAIL + "Your account was not able to be deleted." + bcolors.ENDC)
    
    # Thread that takes care of client input (to send to Server)
    def client_send(self):
        while True:
            inp = input(bcolors.BOLD +"COMMANDS" + bcolors.ENDC + ": " + bcolors.BOLD + "\n" +"LA" + bcolors.ENDC + " - List accounts. "+ bcolors.BOLD + "\n" + "USERNAME-> MESSAGE" + bcolors.ENDC+ " - Send USERNAME MESSAGE." + "\n" + bcolors.BOLD + "DA" + bcolors.ENDC + " - Delete your account."+"\n" + bcolors.BOLD + "Q" + bcolors.ENDC + " - Quit client program."+"\n")

            # Command to list accounts
            if inp == "LA":
                self.listAccounts()
            # Command to delete accounts
            elif inp == "DA":
                self.deleteAccount() 
            # Command to quit client program   
            elif inp == "Q":
                os.kill(os.getpid(), signal.SIGINT)  
            
            # Illegal (message) command(s)  
            elif "->" not in inp:
                print(bcolors.WARNING + "NEED TO SPECIFY USER. Correct usage: USER-> message." + bcolors.ENDC)
            elif "|" in inp:
                print(bcolors.WARNING + "Unfortunately, we do not support | as a character in our chat." + bcolors.ENDC)
            else:
                # Get who the message should be sent to and the contents of the message      
                recipient = self.unpackRecipient(inp)
                message = self.unpackMessage(inp)

                # From the recipient and message contents, construct a proto message
                n = chat.Str()
                n.sender = self.account.username  
                n.message = message
                n.recipient = recipient

                # Send the message to the server and recieve a verification message
                messageVerification = self.conn.sendStr(n)
                if messageVerification.message == "USER-DOES-NOT-EXIST.":
                    print(bcolors.OKCYAN + "[SERVER] " + bcolors.ENDC + "The user you are trying to contact does not exist.")
                elif messageVerification.message == "QUEUED-MESSAGE-SENT.":
                    print(bcolors.OKCYAN + "[SERVER] " + bcolors.ENDC + n.recipient +" is not logged in. But your message will be delivered")
                elif messageVerification.message == "MESSAGE-SENT.":
                    print(bcolors.OKCYAN + "[SERVER] " + bcolors.ENDC + "Your message has successfully delivered.")

    # Called when user is first logged in -- goal is to retrieve queued messages from server
    def dequeue(self):
        allmessages = self.conn.dequeue(self.account)
        if allmessages.message == '':
            return
        else:
            print("Messages you haven't seen yet: ")
            # Like listAccounts, messages are merged -- we need to split on "|"
            allmessages = allmessages.message.split("|")
            for message in allmessages:
                print(bcolors.OKCYAN + message + bcolors.ENDC)

if __name__ == '__main__':
    c = Client()  # this starts a client and thus a thread which keeps connection to server open
