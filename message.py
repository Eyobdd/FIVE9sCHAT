class Message:
    def __init__(self, sender, recipient, data):
        self.sender = sender
        self.recipient = recipient
        self.data = data
    def encodeData():
        self.data = self.data.encode('UTF-8')
    def decodeData():
        self.data = self.data.decode('UTF-8')


    @staticmethod
    def createMessageFromBuffer(data):
        #break down raw packet and construct message
        sender = ""
        recipient = ""
        data = ""

        return Message(sender, recipient, data)

    def createBuffer