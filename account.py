HEADER_LENGTH = 1024

class Account:
    def __init__(self, socket,username):
        self.socket = user_socket
        self.username = username
        self.online = True
        self.queuedMessages = []

    def sendConfirmation(socket,message):
        message = f"M:{username}:SERVER:{message}".encode('utf-8')
        header = f"{len(message) :< {HEADER_LENGTH}}".encode('utf-8')
        socket.send(header+message)


    def deliverQueuedMessages():
        if queuedMessages == []:
            return sendConfirmation(socket,"No waiting messages!")
        for message in queuedMessages:
            message.send()
            queuedMessages = []

    # TODO this function needs to move outside of the account object
    def login(exists,client):
        if not exists:
            return sendConfirmation(client,"User does not exist!")
        online = True
        return sendConfirmation(client,"User Logged in Successfully")

    def logout():
        online = False
        socket.close()
        

    def delete(exists):
        if not exists:
            return sendConfirmation(socket,"User unable to be deleted!")
        sendConfirmation(socket,"Account successfully deleted!")
        socket.close()

    def queueMessage(message_obj):
        queuedMessages.append(message_obj)


    @staticmethod
    def registerAccount(socket, is_taken,username):
        if is_taken:
            return sendConfirmation(socket,"Username is already taken!")
        sendConfirmation(socket,"Account has been created!")
        return Account(socket, username)