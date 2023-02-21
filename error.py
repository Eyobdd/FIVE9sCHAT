class Error:
    def __init__ (self,socket,message):
        self.socket = 
        self.message = message
        # self.bool = False

    @staticmethod
    def createError(message):
        return Error(message)