from concurrent import futures

import grpc
import time

import chat_pb2 as chat
import chat_pb2_grpc as rpc

# inherited from RPC generated class
class ChatServer(rpc.ChatServerServicer): 

    def __init__(self):
        # Keep track of server-wide chat history
        self.chats = []
        
        # Keep track of server accounts
        self.accounts = {}

        # Keep track of queued messages for all accounts
        self.queuedMessages = {}

        # Create the SERVER account -- make sure it's always active 
        # (so no client can log into it)
        self.serverAcc = chat.Account()
        self.serverAcc.username = 'SERVER'
        self.serverAcc.created = True
        self.serverAcc.loggedIn = True
        self.accounts['SERVER'] = self.serverAcc


    # This is a response-stream type call. 
    # This is how the server keeps sending messages to the clients.
    # Every request_account (client is the context) opens this connection 
    # and waits for server to send new messages.
    
    def ChatStream(self, request_account, context):
        
        messageCount = 0
        
        # while the client is logged in
        while context.is_active():
            # Check if there are any new messages
            while len(self.chats) > messageCount:
                n = self.chats[messageCount]
                messageCount += 1
                yield n

        # If the client is not logged in, log them out (change them to inactive)
        self.accounts[request_account.username].loggedIn = False
        print(request_account.username + " disconnected")
    
    # Takes in a chat.Account() and returns a chat.Account()
    def createAccount(self, request: chat.Account, context):
        
        # Make sure that username does not already exist
        if request.username in self.accounts.keys():
            # request.created = False -- so we will return back to client 
            # the original account (which was not created).
            return request
        else:
            # Change the request account properties such that 
            # it is now created and logged in
            request.created = True
            request.loggedIn = True
            self.accounts[request.username] = request

            # return that changed account back 
            # so that client knows it has been created and logged in
            return request
    
    def listAccounts(self, request, context):
        # We need to merge every account + active or inactive status 
        # because proto3 does not support array or list class property
        accountString = ''
        for account in self.accounts:
            status = ''
            if self.accounts[account].loggedIn:
                status = 'active'
            else:
                status = 'inactive'
            accountString += "|" + account + " ( " + status + " )"

        # Return all of the accounts as the username of the account. 
        allAccounts = chat.Str()
        allAccounts.sender = self.serverAcc.username
        allAccounts.recipient = 'unauthenticated user'
        allAccounts.message = accountString
        return allAccounts

    def login(self, request: chat.Account, context):
        
        # Check is username exists.
        if request.username not in self.accounts.keys():
            #Str that request.created = False -- so we will return back to client that the account was not created.
            return request
        elif self.accounts[request.username].loggedIn:
            # Don't login if user is already active on the server
            return request

        # Else -- Username exists and is not already active on the sever
        else:
            active = chat.Account()
            active.username = request.username

            # Set auth properties to True
            active.created = True
            active.loggedIn = True

            # return valid authorized account back to client
            self.accounts[active.username].loggedIn = True
            return active

    def deleteAccount(self, request: chat.Account, context):
       del self.accounts[request.username]
       verification = chat.Str()
       verification.sender = self.serverAcc.username
       verification.recipient =  request.username
       verification.message = "DELETED."
       return verification

    # Important note: this function is called when the CLIENT sends a message 
    # to the SERVER (not the other way around)
    def sendStr(self, request: chat.Str, context):

        # Check if client is attempting to send to a User who does not exist.
        if request.recipient not in self.accounts.keys():
            error = chat.Str()
            error.sender = self.serverAcc.username
            error.recipient = request.sender
            error.message = "USER-DOES-NOT-EXIST."
            return error

        # User exists -- but is not logged in.
        elif not self.accounts[request.recipient].loggedIn:

            # Don't add message to chat history -- we need to add to queued message
            if not self.queuedMessages or not self.queuedMessages[request.recipient]:
                # Create a list to store queued messages for user if they don't already have one
                self.queuedMessages[request.recipient] = []
            # Add message to queue
            self.queuedMessages[request.recipient].append(request)

            # Notify client that message was queued for recipient
            success = chat.Str()
            success.sender = self.serverAcc.username
            success.recipient = request.sender
            success.message = "QUEUED-MESSAGE-SENT."
            return success

        # User exists and is logged in.
        else:
            # Add the message to the chat history -- which will be streamed to the clients (broadcasted)
            self.chats.append(request)

            # Return a message sent verification message to client
            success = chat.Str()
            success.sender = self.serverAcc.username
            success.recipient = request.sender
            success.message = "MESSAGE-SENT."
            return success

    # Sends queued messages all as one string (because proto doesn't support lists or arrays)
    def dequeue (self, request: chat.Account, context):
        allMessages = ''

        # Queued messages is empty -- return empty string
        if not self.queuedMessages:
            empty = chat.Str()
            empty.sender = self.serverAcc.username
            empty.recipient = request.username
            empty.message = ''
            return empty
        # List to store queued messages for user does not exist
        if not self.queuedMessages[request.username]:

            # So we create the list and return empty string (since no queued messages exist)
            self.queuedMessages[request.username] = []
            empty = chat.Str()
            empty.sender = self.serverAcc.username
            empty.recipient = request.username
            empty.message = ''
            return empty
        
        # Queued messages exist -- we merge them off of "|" and return them as one message
        else:
            for message in self.queuedMessages[request.username]:
                allMessages += "|" + "[" + message.sender + "] " + message.message
            
            dequeued = chat.Str()
            dequeued.sender = self.serverAcc.username
            dequeued.recipient = request.username
            dequeued.message = allMessages
            return dequeued

if __name__ == '__main__':
    # Set port
    port = 12341 

    # Set the maximum number of client connections (workers) to 10.
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))  

    # Create and register the gRPC server
    rpc.add_ChatServerServicer_to_server(ChatServer(), server)

    # Start the server on our IP and Port.
    server.add_insecure_port('10.250.92.212:' + str(port))
    server.start()

    # Server starts in background (in another thread) so keep waiting -- because
    # if we don't, then the main thread will end, ending the children threads
    while True:
        time.sleep(64 * 64 * 100)
