while True:
    message = input(bcolors.BOLD +"COMMANDS" + bcolors.ENDC + ": " + bcolors.BOLD + "\n" +"LA" + bcolors.ENDC + " - List accounts. "+ bcolors.BOLD + "\n" + "USERNAME-> MESSAGE" + bcolors.ENDC+ " - Send USERNAME MESSAGE." + "\n" + bcolors.BOLD + "DA" + bcolors.ENDC + " - Delete your account."+"\n" + bcolors.BOLD + "Q" + bcolors.ENDC + " - Quit client program."+"\n")
    if message == "LA":
        self.listAccounts()
    elif message == "DA":
        self.deleteAccount()    
    elif message == "Q":
        os.kill(os.getpid(), signal.SIGINT)   
    elif "->" not in message:
        print(bcolors.WARNING + "NEED TO SPECIFY USER. Correct usage: USER-> Message." + bcolors.ENDC)
    elif "|" in message:
        print(bcolors.WARNING + "Unfortunately, we do not support | as a character in our chat." + bcolors.ENDC)
    else:    
        recipient = self.unpackRecipient(message)
        message = self.unpackMessage(message)

        n = chat.Note()  # create protobug message (called Note)
        n.sender = self.account.username  # set the username
        n.message = message  # set the actual message of the note
        n.recipient = recipient
        messageVerification = self.conn.sendNote(n)
        if messageVerification.message == "USER-DOES-NOT-EXIST.":
            print(bcolors.FAIL + bcolors.BOLD + recipient + bcolors.ENDC + bcolors.FAIL +" DOES NOT EXIST." + bcolors.ENDC)
        elif messageVerification.message == "QUEUED-MESSAGE-SENT.":
            print(bcolors.OKBLUE + recipient + " is not currently active, but the message will be delivered when they login."+ bcolors.ENDC)
        elif messageVerification.message == "MESSAGE-SENT.":
            print(bcolors.OKGREEN + "message to " + recipient + "sucessfuly delivered. "+ bcolors.ENDC)
                # send the Note to the server