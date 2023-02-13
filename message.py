class Message:
    def __init__(self, sender, recipient, data):
        self.sender = sender
        self.recipient = recipient
        self.data = data 

    @staticmethod
    def createMessageFromBuffer(header):
        #break down raw packet and construct message
        sender = header[1]
        recipient = header[2]
        data = header[3]
        return Message(sender, recipient, data)

    def createBufferFromMessage():
