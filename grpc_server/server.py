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
        
        if request.username not in self.accounts.keys():
            #Str that request.created = False -- so we will return back to client that the account was not created.
            return request
        elif self.accounts[request.username].loggedIn:
            # Don't login if user is already active on the server
            return request
        else:
            active = chat.Account()
            active.username = request.username
            active.created = True
            active.loggedIn = True
            self.accounts[active.username].loggedIn = True
            return active

    def deleteAccount(self, request: chat.Account, context):
       del self.accounts[request.username]
       verification = chat.Str()
       verification.sender = self.serverAcc.username
       verification.recipient =  request.username
       verification.message = "DELETED."
       return verification

    def sendStr(self, request: chat.Str, context):
        """
        This method is called when a clients sends a Str to the server.

        :param request:
        :param context:
        :return:
        """
        print("message is being sent from " + request.sender)
        if request.recipient not in self.accounts.keys():
            # attempting to send to a user who does not exist.
            error = chat.Str()
            error.sender = self.serverAcc.username
            error.recipient = request.sender
            error.message = "USER-DOES-NOT-EXIST."

            return error
        # User exist -- but is not logged in.
        elif not self.accounts[request.recipient].loggedIn:
            if not self.queuedMessages or not self.queuedMessages[request.recipient]:
                self.queuedMessages[request.recipient] = []
            self.queuedMessages[request.recipient].append(request)

            success = chat.Str()
            success.sender = self.serverAcc.username
            success.recipient = request.sender
            success.message = "QUEUED-MESSAGE-SENT."
            return success
        # User exists and is logged in.
        else:
            print(self.accounts[request.recipient].loggedIn)
            print("[{}] {}".format(request.sender, request.message))
            # Add it to the chat history
            self.chats.append(request)
            success = chat.Str()
            success.sender = self.serverAcc.username
            success.recipient = request.sender
            success.message = "MESSAGE-SENT."
            return success  # something needs to be returned required by protobuf language, we just return empty msg
    
    def dequeue (self, request: chat.Account, context):
        allMessages = ''
        print(request.username)
        print(self.queuedMessages)
        if not self.queuedMessages:
            print("queued messages is empty")
            empty = chat.Str()
            empty.sender = self.serverAcc.username
            empty.recipient = request.username
            empty.message = ''
            return empty
        if not self.queuedMessages[request.username]:
            print("We hit this line")
            self.queuedMessages[request.username] = []
            empty = chat.Str()
            empty.sender = self.serverAcc.username
            empty.recipient = request.username
            empty.message = ''
            print("We returned empty because user was just created.")
            return empty
        else:
            for message in self.queuedMessages[request.username]:
                allMessages += "|" + "[" + message.sender + "] " + message.message
            
            dequeued = chat.Str()
            dequeued.sender = self.serverAcc.username
            dequeued.recipient = request.username
            dequeued.message = allMessages
            return dequeued


if __name__ == '__main__':
    port = 12341 

    # Set the maximum number of client connections (workers) to 10.
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))  # create a gRPC server
    rpc.add_ChatServerServicer_to_server(ChatServer(), server)  # register the server to gRPC
    # gRPC basically manages all the threading and server responding logic, which is perfect!
    print('Starting server. Listening...')
    server.add_insecure_port('10.250.92.212:' + str(port))
    server.start()
    # Server starts in background (in another thread) so keep waiting
    # if we don't wait here the main thread will end, which will end all the child threads, and thus the threads
    # from the server won't continue to work and stop the server
    while True:
        time.sleep(64 * 64 * 100)
