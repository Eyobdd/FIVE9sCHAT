import threading
from tkinter import *
from tkinter import simpledialog
import os
import signal
import grpc

import chat_pb2 as chat
import chat_pb2_grpc as rpc

address = 'localhost'
port = 11912

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


        self.account = chat.Account()
        self.account.loggedIn = False
        self.account.created = True
       
        # create a gRPC channel + stub

        channel = grpc.insecure_channel(address + ':' + str(port))
        self.conn = rpc.ChatServerStub(channel)
        self.listAccounts()
        # Let user create an account or login
        self.authenticate()
        # create new listening thread for when new message streams come in
        self.dequeue()
        listen_thread = threading.Thread(target=self.__listen_for_messages)
        send_thread =  threading.Thread(target=self.client_write)

        print("starting threads")
        listen_thread.start()
        send_thread.start()


    def authenticate(self):
        print(bcolors.OKGREEN + "Would you like to CREATE an account or LOGIN to an existing user from above? " + bcolors.ENDC)
        decision = input("Type " + bcolors.BOLD + "C" + bcolors.ENDC + " to create an account. Type " + bcolors.BOLD + "L" + bcolors.ENDC + " to login in." )
        while (decision != "C" and decision != "L"):
            print("please type a valid decision.")
            decision = input("Type " + bcolors.BOLD + "C" + bcolors.ENDC + " to create an account. Type " + bcolors.BOLD + "L USERNAME" + bcolors.ENDC + " to login into USERNAME." )
        if decision == "C":
            # Create Account
            while not self.account.loggedIn:
                message = input("What username would you like to create?\n")
                acc = chat.Account()
                acc.username = message
                acc.created = False
                acc.loggedIn = False
                accVerification = self.conn.createAccount(acc)
                if accVerification.created:
                    self.account = accVerification
                    print(bcolors.OKGREEN + self.account.username + " has been successfully created and logged in." + bcolors.ENDC)
                else:
                    print(bcolors.FAIL + "Account creation failed. Make sure it's a user that doesn't already exist." + bcolors.ENDC)
        elif decision == "L":
            # Attempt to Login
                while not self.account.loggedIn:
                    message = input("What username would you like to Log into?\n")
                    acc = chat.Account()
                    acc.username = message
                    acc.created = False
                    acc.loggedIn = False
                    accVerification = self.conn.login(acc)
                    if accVerification.created:
                        self.account = accVerification
                        print(bcolors.OKGREEN + "Login-Successful." + bcolors.ENDC)
                    else:
                        print(bcolors.FAIL + "Login failed. Make sure user exists and/or that user isn't already logged in (active)" + bcolors.ENDC)


    def __listen_for_messages(self):
        """
        This method will be ran in a separate thread as the main/ui thread, because the for-in call is blocking
        when waiting for new messages
        """
        print("starting listening thread")
        for note in self.conn.ChatStream(self.account):  # this line will wait for new messages from the server!
            if (note.recipient == self.account.username) or (note.recipient == "all"):
                print(bcolors.OKCYAN + "[" + note.sender + "] " + bcolors.ENDC + note.message)  # debugging statement

    def listAccounts(self):
        allAccounts = self.conn.listAccounts(chat.Empty())

        if allAccounts.username == '':
            print("The server has no accounts.")
        else:
            allAccounts = allAccounts.username.split("|")
            print(bcolors.OKGREEN + "The server holds the following accounts." + bcolors.ENDC)
            for account in allAccounts:
                print(" -- > " + account)

    def unpackRecipient(self, message):
        recipient = message.split("->")
        recipient = recipient[0]
        return recipient

    def unpackMessage(self, message):
        message = message.split("->")
        message = message[1]
        return message

    def deleteAccount(self):
        if self.conn.deleteAccount(self.account).message == "DELETED.":
            #sucessfully deleted
            print("Your account has been deleted. Your client connection will end. Bye, Bye")
            print(bcolors.BOLD + bcolors.FAIL + "EXITING CLIENT PROGRAM." + bcolors.ENDC)
            os.kill(os.getpid(), signal.SIGINT)
        else:
            print(bcolors.FAIL + "Your account was not able to be deleted." + bcolors.ENDC)
        
    def client_write(self):
        """
        This method is called when user enters something into the textbox
        """
        print("starting sending thread")

        while True:
            message = input(bcolors.BOLD +"COMMANDS" + bcolors.ENDC + ": " + bcolors.BOLD + "\n" +"LA" + bcolors.ENDC + " - List accounts. "+ bcolors.BOLD + "\n" + "USERNAME-> MESSAGE" + bcolors.ENDC+ " - Send USERNAME MESSAGE." + "\n" + bcolors.BOLD + "DA" + bcolors.ENDC + " - Delete your account."+"\n" + bcolors.BOLD + "Q" + bcolors.ENDC + " - Quit client program."+"\n")
            if message == "LA":
                self.listAccounts()
            elif message == "DA":
                self.deleteAccount()    
            elif message == "Q":
                os.kill(os.getpid(), signal.SIGINT)   
            elif "->" not in message:
                print(bcolors.WARNING + "NEED TO SPECIFY USER. Correct usage: USER-> Message." + bcolors.ENDC)
            elif "|" in message:
                print(bcolors.WARNING + "Unfortunately, we do not support | as a character in our chat." + bcolors.ENDC)
            else:    
                recipient = self.unpackRecipient(message)
                message = self.unpackMessage(message)

                n = chat.Note()  # create protobug message (called Note)
                n.sender = self.account.username  # set the username
                n.message = message  # set the actual message of the note
                n.recipient = recipient
                messageVerification = self.conn.sendNote(n)
                if messageVerification.message == "USER-DOES-NOT-EXIST.":
                    print(bcolors.FAIL + bcolors.BOLD + recipient + bcolors.ENDC + bcolors.FAIL +" DOES NOT EXIST." + bcolors.ENDC)
                elif messageVerification.message == "QUEUED-MESSAGE-SENT.":
                    print(bcolors.OKBLUE + recipient + " is not currently active, but the message will be delivered when they login."+ bcolors.ENDC)
                elif messageVerification.message == "MESSAGE-SENT.":
                    print(bcolors.OKGREEN + "message to " + recipient + "sucessfuly delivered. "+ bcolors.ENDC)
                      # send the Note to the server
    def dequeue(self):
        allMessages = self.conn.dequeue(self.account)
        if allMessages.message == '':
            return
        else:
            allMessages = allMessages.message.split("|")
            for message in allMessages:
                print(bcolors.OKCYAN + message + bcolors.ENDC)

if __name__ == '__main__':
    c = Client()  # this starts a client and thus a thread which keeps connection to server open