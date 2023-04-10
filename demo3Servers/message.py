HEADER_LENGTH = 10

# Message objects are created from buffer in protocol_unpack
# and initialized in protocol_action and handel client in socket_server/server.py
# Data Stored:
#  - sender -> message sender username
#  - recipient -> message recipient username
#  - data -> the message to be sent to the recipient
class Message:
    # Initalize Message() object
    def __init__(self, recipient, sender, message):
        self.sender = sender
        self.recipient = recipient
        self.data = message 

    # Returns the message encoded with header(also encoded)
    def encode(self):
        encoded_message = f"M:{self.recipient}:{self.sender}:{self.data}".encode('utf-8')
        header = f"{len(encoded_message) :< {HEADER_LENGTH}}".encode('utf-8')

        return header+encoded_message
    def encodeJustMessage(self):
        encoded_message = f"M:{self.recipient}:{self.sender}:{self.data}".encode('utf-8')
        return encoded_message
    
    def print(self):
        print("sender: ", self.sender)
        print("recipient: ", self.recipient)
        print("message: ", self.data)
        
    # Creates a Message() object from buffer
    @staticmethod
    def createMessageFromBuffer(header):
        #break down raw packet and construct message
        header = header.split(":",3)
        sender = header[1]
        recipient = header[2]
        data = header[3]
        return Message(sender, recipient, data)