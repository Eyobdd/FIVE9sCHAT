HEADER_LENGTH = 1024

class Message:
    def __init__(self, sender, recipient, data):
        self.sender = sender
        self.recipient = recipient
        self.data = data 

    def send():
        header = f"{len(data) :< {HEADER_LENGTH}}".encode('utf-8')
        encoded_message = f"M:{sender}:{data}".encode('utf-8')
        recipient.send(header+encoded_message)

    @staticmethod
    def createMessageFromBuffer(header):
        #break down raw packet and construct message
        sender = header[1]
        recipient = header[2]
        data = header[3]
        return Message(sender, recipient, data)