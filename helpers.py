import Account
import Message

# TODO Login and Register will need to be in another earlier function
def Act(obj,data,client,clientDict):
    type_ = data[0]
    match type_ :

        # Message type -> call send message on object
        case "M":
            recipient = data[1]

            # Does recipient exist?
            if recipient in clientDict:

                recipient_account = clientDict[recipient]
                recipient_online = recipient.online
                
                # if recipient online -> send message
                if recipient_online: 
                    obj.send()
                # if recipient offline -> queue messsage
                else:
                    recipient_account.queueMessage(obj)
            else:
                # TODO Send Error to sender!


        # Login type -> call login method on object // TODO IDK if this is true but its late I will fix tmr need to do more logic on this side
        case "L":
            username = data[1]
            exists = username in clientDict
            if exists:
                # find the account via username and login
                clientDict[username].login(exists,client)
            else:
                # sends login error
                Account.login(exists,client)

        # Delete type -> call delete method on object
        case "D":
            exists = obj.username in clientDict
            if exists:
                # deletes object from account dictionary
                del clientDict[obj.username]
                # send confirmation method
                obj.delete(exists)
            else:
                # Sends error message
                Account.delete(exists)


def unpack(data,client,clientDict):
    type_ = data[0]

    match type_:

        case "M":
            recipient = data[1]
            sender = data[2]
            message = data[3]
            return Message.createMessageFromBuffer(sender,recipient,data)
        
         # Register type -> call register method
        case "R":
            username = data[1]
            is_taken = username in clientDict
            if is_taken:
                # Sends error message to user
                Account.registerAccount(client,is_taken,username)
                # Create error class
            else:
                # Adds new account to client dictionary and send confirmation message
                obj = Account.registerAccount(client,is_taken,username)
                clientDict[username] = obj
                return obj