HEADER_LENGTH = 10

class Message:
    def __init__(self, recipient, sender, message):
        self.sender = sender
        self.recipient = recipient
        self.data = message 

    def encode(self):
        encoded_message = f"M:{self.recipient}:{self.sender}:{self.data}".encode('utf-8')
        header = f"{len(encoded_message) :< {HEADER_LENGTH}}".encode('utf-8')

        return header+encoded_message
    
    @staticmethod
    def createMessageFromBuffer(header):
        #break down raw packet and construct message
        header = header.split(":")
        sender = header[1]
        recipient = header[2]
        data = header[3]
        return Message(sender, recipient, data)