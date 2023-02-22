from concurrent import futures

import grpc
import time

import chat_pb2 as chat
import chat_pb2_grpc as rpc


class ChatServer(rpc.ChatServerServicer):  # inheriting here from the protobuf rpc file which is generated

    def __init__(self):
        # List with all the chat history
        self.chats = []
        
        # List keeping track of all of the accounts
        self.accounts = {}
        self.serverAcc = chat.Account()
        self.serverAcc.username = 'SERVER'
        self.serverAcc.created = True
        self.serverAcc.loggedIn = True
        self.queuedMessages = {}
        self.accounts['SERVER'] = self.serverAcc


    # The stream which will be used to send new messages to clients
    def ChatStream(self, request_iterator, context):
        """
        This is a response-stream type call. This means the server can keep sending messages
        Every client opens this connection and waits for server to send new messages

        :param request_iterator:
        :param context:
        :return:
        """
        lastindex = 0
        # For every client a infinite loop starts (in gRPC's own managed thread)
        while context.is_active():
            # Check if there are any new messages
            while len(self.chats) > lastindex:
                n = self.chats[lastindex]
                lastindex += 1
                yield n
        self.accounts[request_iterator.username].loggedIn = False
        
        print(request_iterator.username + " disconnected")
    

    def createAccount(self, request: chat.Account, context):
        # notice we check the equality of the string because we don't have an object equality check
        if request.username in self.accounts.keys():
            #note that request.created = False -- so we will return back to client that the account was not created.
            return request
        else:
            request.created = True
            request.loggedIn = True
            self.accounts[request.username] = request
            return request#some vertification

    def listAccounts(self, request, context):
        accountString = ''
        for account in self.accounts:
            status = ''
            if self.accounts[account].loggedIn:
                status = 'active'
            else:
                status = 'inactive'
            accountString += "|" + account + " ( " + status + " )"

        
        allAccounts = chat.Account()
        allAccounts.username = accountString
        allAccounts.created = True
        return allAccounts

    def login(self, request: chat.Account, context):
        
        if request.username not in self.accounts.keys():
            #note that request.created = False -- so we will return back to client that the account was not created.
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
       verification = chat.Note()
       verification.sender = self.serverAcc.username
       verification.recipient =  request.username
       verification.message = "DELETED."
       return verification

    def sendNote(self, request: chat.Note, context):
        """
        This method is called when a clients sends a Note to the server.

        :param request:
        :param context:
        :return:
        """
        print("message is being sent from " + request.sender)
        if request.recipient not in self.accounts.keys():
            # attempting to send to a user who does not exist.
            error = chat.Note()
            error.sender = self.serverAcc.username
            error.recipient = request.sender
            error.message = "USER-DOES-NOT-EXIST."

            return error
        # User exist -- but is not logged in.
        elif not self.accounts[request.recipient].loggedIn:
            if not self.queuedMessages or not self.queuedMessages[request.recipient]:
                self.queuedMessages[request.recipient] = []
            self.queuedMessages[request.recipient].append(request)

            success = chat.Note()
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
            success = chat.Note()
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
            empty = chat.Note()
            empty.sender = self.serverAcc.username
            empty.recipient = request.username
            empty.message = ''
            return empty
        if not self.queuedMessages[request.username]:
            print("We hit this line")
            self.queuedMessages[request.username] = []
            empty = chat.Note()
            empty.sender = self.serverAcc.username
            empty.recipient = request.username
            empty.message = ''
            print("We returned empty because user was just created.")
            return empty
        else:
            print("The user exists in queuedMessages")
            for message in self.queuedMessages[request.username]:
                allMessages += "|" + "[From " + message.sender + "] " + message.message
            
            dequeued = chat.Note()
            dequeued.sender = self.serverAcc.username
            dequeued.recipient = request.username
            dequeued.message = allMessages
            return dequeued


if __name__ == '__main__':
    port = 11912  # a random port for the server to run on
    # the workers is like the amount of threads that can be opened at the same time, when there are 10 clients connected
    # then no more clients able to connect to the server.
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))  # create a gRPC server
    rpc.add_ChatServerServicer_to_server(ChatServer(), server)  # register the server to gRPC
    # gRPC basically manages all the threading and server responding logic, which is perfect!
    print('Starting server. Listening...')
    server.add_insecure_port('[::]:' + str(port))
    server.start()
    # Server starts in background (in another thread) so keep waiting
    # if we don't wait here the main thread will end, which will end all the child threads, and thus the threads
    # from the server won't continue to work and stop the server
    while True:
        time.sleep(64 * 64 * 100)
