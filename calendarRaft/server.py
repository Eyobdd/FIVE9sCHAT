import threading
import socket
import sys
from message import Message
from command import Command
import time
import pickle
import os
from datetime import datetime
from event import Event

class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


# START socket connections to the two other servers in the system.
socket1 = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
socket2 = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

HEADER_LENGTH = 10
HOST = '127.0.0.1'
# HOST = "127.0.0.1"
PORT = int(sys.argv[1])



# RAFT vars
state = "F"
if PORT == 12340:
    heartbeat = 1
if PORT == 12341:
    heartbeat = 0.4
if PORT == 12342:
    heartbeat = 2

serverDrops = 0
voted = False
votes = 0
startedHeartBeat = False
stopwatch = time.perf_counter()
term = 0
# number of servers
N = 3

# UNIT TEST Init
TESTING_PERSISTENCE = False
simData = "12341calendarLog.pickle"
sim = {}
with open(simData, 'rb') as handle:
        sim = pickle.load(handle)
if sys.argv[2] == "1":
    print("we will be running Unit tests")
    TESTING_PERSISTENCE = True


# Connect sockets to server
myServer = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
myServer.bind((HOST, PORT))
myServer.listen()


ports = [12340, 12341, 12342]
serverActives = [0,0,0]
ME = ports.index(PORT)
serverActives[ME] = 1


# Stores active socket
clients = []

# Stores active usernames
usernames = [] 

# Stores server connections
servers = []

# Stores all active users {username:socket} pairs
clientID = {}

# Stores if a user is online or not all accounts {username:Boolean}
loginStatus = {}

# The server is always online so users cannot log into the server account
loginStatus['SERVER'] = True

# Will update this in our heart beat
leader = ''

# Stores all messages to offline users {username: Message()}
queueCounter = 0

# Stores all events {username: Events} pairs
calendar = {}

# Load calendar log (different case if we are unit testing)


filename = str(PORT) + "calendarLog.pickle"
if os.path.isfile(filename):
    with open(filename, 'rb') as handle:
        calendar = pickle.load(handle)
    if (TESTING_PERSISTENCE):
        print(bcolors.BOLD + bcolors.OKCYAN + "UNIT TEST: Loads own calendar log history from disk ✅" + bcolors.ENDC)
else:
    calendar = {}

# Convert queued messages into a structure we can send over the sockets.
pickleMessage = pickle.dumps(calendar)

 # Make the server active.
loginStatus['SERVER'] = True

def sendToServers(message):
    if ME == 0:
        if serverActives[1] == 1:
            socket1.send(message)
        if serverActives[2] == 1:
            socket2.send(message)
    if ME == 1:
        if serverActives[0] == 1:
            socket1.send(message)
        if serverActives[2] == 1:
            socket2.send(message)
    if ME == 2:
        if serverActives[1] == 1:
            socket1.send(message)
        if serverActives[0] == 1:
            socket2.send(message)

def getTime():
    global stopwatch
    return time.perf_counter() - stopwatch

def resetHeartBeat():
    global stopwatch
    stopwatch = time.perf_counter()

def sendHeartBeat():
    global term
    message = "E: " + str(term) + ":" + str(PORT)
    message = encoded_message(message)
    sendToServers(message)


def startElection():
    global state
    global term
    state = "C"
    term +=1
    # Request a vote from the other servers.
    message = "RV:" + str(term) + ":" + str(PORT)
    message = encoded_message(message)
    sendToServers(message)


def startHeartBeat():
    global state
    resetHeartBeat()
    while True:

        if serverDrops > 1:
                state = "L"

        if state == "F":
            if serverDrops > 1:
                state = "L"
            t = getTime()
            if t > heartbeat:
                print(bcolors.WARNING + "HEARTBEAT" + bcolors.ENDC + str(t))
                resetHeartBeat()
                startElection()
                # transition to be candidate
                
        if state == "L":
            time.sleep(heartbeat)
            sendHeartBeat()

def sendVoteResponse(response, p):
        if ME == 0:
            if p == 12341:
                socket1.send(response)
            else:
                socket2.send(response)
        elif ME == 1:
            if p == 12340:
                socket1.send(response)
            else:
                socket2.send(response)
        elif ME == 2:
            if p == 12341:
                socket1.send(response)
            else:
                socket2.send(response)

# Equality checking of message logs -- used for unit tests
def calendarLogEquals(d1, d2):
    for u in d2:
        for i in range(len(d2[u])):
            if not d2[u][i] == d2[u][i]:
                return False
    return True
    
# Encode the message before sending in sockets
def encoded_message(message):
    message = message.encode('utf-8')
    header = f"{len(message) :< {HEADER_LENGTH}}".encode('utf-8')
    return header+message

# Function sends encoded message to username
def sendToClient(username, message):

    # Creates Message() object
    message = Message(username, "SERVER", message)

    # Finds socket associated with user
    client = clientID[username]

    # Sends encoded message to that user
    client.send(message.encode())

# Function receives data from client
def receiveData(client):
    data = client.recv(HEADER_LENGTH).decode('utf-8')
    data_length = int(data.strip())
    try:
        data = client.recv(data_length).decode('utf-8')
    except:
        print("possible non-string bytes")
        data = client.recv(data_length)
        print(data)
    return data

# Received a message from another server, now act on that message.
def serverProtocol(data):
    global state
    global term
    global votes
    global voted
    global leader
    resetHeartBeat()
    dataSplit = data.split(":")
    if dataSplit[0] == "M":
        # we have a message -- add it to the queued messages
        m = Message.createMessageFromBuffer(data)
        m.print()

    elif dataSplit[0] == "C":

        # account was created on a leader server -- we need to replicate it here
        username = dataSplit[1]
        loginStatus[username] = False
        print("usernames: ", loginStatus)

    elif dataSplit[0] == "D":
        # account was deleted on a leader server -- we need to replicate it here

        username = dataSplit[1]
        del loginStatus[username]
        print("ACCOUNT: " + username + " has been attempted to be deleted")
        print("usernames: ", loginStatus)

    elif dataSplit[0] == "E":
        t = int(dataSplit[1])
        p = int(dataSplit[2])
        state = "F"
        voted = False
        votes = 0
        if t > term:
            term = t
        leader = p
        resetHeartBeat()
    elif dataSplit[0] == "RV":
        # We recieved a request for a vote
        print("recieved a request for a vote", data)
        t = int(dataSplit[1])
        p = int(dataSplit[2])

        print("term", t)
        print("port", p)
        if (not (term > t)) and (not voted):
            # Accept vote and send acceptance

            print("accepted vote for ", p)
            response = "VA:" + str(PORT)
            response = encoded_message(response)
            sendVoteResponse(response, p)
        else:

            print("rejected vote for ", p)
            response = "VR:"
            response = encoded_message(response)
            sendVoteResponse(response, p)
        voted = True
    elif dataSplit[0] == "VA":
        print("recieved an acceptance from", dataSplit[1])
        votes +=1
        if (1 + votes) >= (N+1)/2 and (state == "C"):
            #majority votes. Become Leader.
            state = "L"
            print(bcolors.BOLD + bcolors.WARNING + "I AM TRUEST LEADER." + bcolors.ENDC)




def protocol_action(obj):
    # global leader
    print(leader)

    # If the object is a Message() then we try to send the message
    if isinstance(obj, Message):

        # If recipient exists -> sends error to client if they do not
        if obj.recipient not in loginStatus:
            # doesNotExist = "The user you are trying to contact does not exist."
            # doesNotExist = Message(obj.sender, "SERVER", doesNotExist)
            # sendToClient(obj.sender, doesNotExist.encode())

            sendToClient(obj.sender, "The user you are trying to contact does not exist.")

        # If recipient is logged-out -> Alerts sender and and queues the message
        elif not loginStatus[obj.recipient]:
            # notlogin = obj.recipient + " is not logged in. But your message will be delivered"
            # notlogin = Message(obj.sender, "SERVER", notlogin)
            # sendToClient(obj.sender,notlogin.encode())

            sendToClient(obj.sender, f"{obj.recipient} is not logged in. But your message will be delivered")


        # Else sends the message to recipient and delivery confirmation to sender
        elif (clientID[obj.recipient] in clients):
            # success = "Your message has successfully delivered."
            # success = Message(obj.sender, "SERVER", success)
            # sendToClient(obj.recipient, obj.encode())
            # sendToClient(obj.sender, success.encode())
            clientID[obj.recipient].send(obj.encode())
            sendToClient(obj.sender, "Your message has successfully delivered.")
    
    # If the object is a Command() then we execute the command
    if isinstance(obj, Command):
        print(obj.actionType)
        
        # If Command type is DA -> Delete Account
        if obj.actionType == "DA":
                
            # User must be online execute this Command so no checks are needed

            # Send confirmation to user
            # success = "Account-Successfully-Deleted"
            # success = Message(obj.username, "SERVER", success)
            # sendToClient(obj.username, success.encode())
            sendToClient(obj.username,"Account-Successfully-Deleted")
            message = "D:" + obj.username
            message = encoded_message(message)
            sendToServers(message)
            

            # Remove user from loginStatus and clientID list
            del loginStatus[obj.username]
            del clientID[obj.username]

            # Only delete from queued messages if user had queued messages. 
            
        # If Command type is LA -> Lists all stored accounts with their login status
        
        elif obj.actionType == "L":
            print("OBJ USERNAME:",obj.username)
            # If user does not exist -> send client login failure message
            if obj.username not in loginStatus:
                failed = "Login-Failed"
                sendToClient(obj.username,failed)

            # If user is already active -> alert client!
            elif loginStatus[obj.username]:
                active = "Account-Already-Active"
                sendToClient(obj.username,active)

            # If username exists and is not active -> log user in
            else:
                # Log user in
                clients.append(obj.socket)
                usernames.append(obj.username)
                clientID[obj.username] = obj.socket
                loginStatus[obj.username] = True

                # Send confirmation message
                sendToClient(obj.username,"Login-Successful.")

                # Broadcast connection and deliver messages and authenticate client
                # client_auth = True
            
        
        elif obj.actionType == "SL":
            print("Leader Port:",obj.data)
            message = f"SL:{leader}"
            sendToClient(obj.username,message)
            
            
        elif obj.actionType == "LA":

            ## Generate account list
            allAccounts = 'LA|'

            # Append (active) or (inactive) to every username
            for account in obj.data:

                #  If username is active
                if obj.data[account]:
                    status = 'active'

                # If username is not active
                else:
                    status = 'inactive'
                
                # Add account status to list with "|", as a divider
                allAccounts += account + " ( " + status + " )" + "|"

            # Remove the last "|" if accounts exists 
            if len(allAccounts) > len("LA|"):
                allAccounts = allAccounts[:-1]

            # Sends list to client to display
            # allAccounts = Message(obj.username, "SERVER", allAccounts)
            # sendToClient(obj.username, allAccounts.encode())
            sendToClient(obj.username, allAccounts)

        elif obj.actionType == "DE":

            print("calendar before", calendar)
            title = obj.data.title
            day = obj.data.date

            try:
                for event in calendar[day]:
                    if event.title == title:
                        calendar[day].remove(event)
            except Exception as e:
                print(" so we're trying to delete an event, but an error", e)
            
            print("calendar after", calendar)
            sendToClient(obj.username,"Event-Deleted")
        elif obj.actionType == "DC":
            print("Display Calendar Request")
            calendar_events = "DC|"
            
            try:
                for day in calendar:
                    print("DAY",day)
                    for event in calendar[day]:
                        print("Event:",event)
                        calendar_events += str(event.title) +"*"+ event.date +"*"+ str(event.start_time) +" - "+ str(event.end_time)+"|"
            except Exception as e:
                print("Calendar Events Error:",e)
            
            print("EVENTS:",calendar_events)
            if len(calendar_events) > len("DC|"):
                calendar_events = calendar_events[:-1]
            
            
            print("Object Username:",obj.username)
            print("Calendar Events",calendar_events)
            sendToClient(obj.username, calendar_events)
            
            
            
    if isinstance(obj, Event):
        
        print("EVENT OBJECT:",obj.username)
        print("Calendar before:",calendar)
        # Does this startTime have overlapping events
        try:
            calendar[obj.date].append(obj)
        except Exception as error:
            calendar[obj.date] = []
            calendar[obj.date].append(obj)
        
        # log
        with open(filename, 'wb') as handle:
            pickle.dump(calendar, handle, protocol=pickle.HIGHEST_PROTOCOL)


        sendToClient(obj.username, "Event-Created")
        for event in calendar[obj.date]:
            if obj.overlapping(event.start_time,event.end_time):
                sendToClient(obj.username, "Over-Lapping-Event")

        print("Calendar after:",calendar)


# Protocol unpack returns Message() and Command() from protocol buffers
# Takes a client socket and encoded buffer data
def protocol_unpack(client):
    global leader
    # Receives bits from client and converts to buffer(encoded)
    data = receiveData(client)
    
    if leader == '':
        leader = PORT
    print("HERE IS THE LEADER'S PORT:",leader)
   
    # Buffer data and splits on the colon 
    dataSplit = data.split(":",3)
    print("Incoming Data:",data)

    # Retrieves type of message/command from buffer data
    type_ = dataSplit[0]
    
    if type_ == "L":
        username = dataSplit[1]
        c = Command.createCommandFromBuffer(client,data,username,type_)
        print("C is:",c,username)
        return c

    # If type is M -> create and return Message() object
    if type_ == "M":

        # Return Message()
        return Message.createMessageFromBuffer(data)

    if type_ == "CE":
        e = Event.createEventFromBuffer(data)
        print("E is ", e)
        return e

    if type_ == "DE":

        print("receiving a delete action (unpack)")
        username = dataSplit[1]
        title = dataSplit[2]
        day = dataSplit[3]
        start_time = "0"
        end_time = "0"
        
        e = Event(username, title, day, start_time, end_time)
        return Command.createCommandFromBuffer(client, e, username, type_)

    if type_ == "SL":
        # Get username from buffer
        username = dataSplit[1]
        
        return Command.createCommandFromBuffer(client,leader,username,type_)

    # If type is LA -> create and return Command() object
    elif type_ == "LA":
        
        # Get username from buffer
        username = dataSplit[1]

        # Return Command() with server login status information
        return Command.createCommandFromBuffer(client, loginStatus ,username,type_)

    # If type is DA -> create and return Command() object
    elif type_ == "DA":

        # Get username from buffer
        username = dataSplit[1]

        # Return Command() 
        return Command.createCommandFromBuffer(client, None ,username,type_)
    
    elif type_ == "DC":
        username = dataSplit[1]
        
        return Command.createCommandFromBuffer(client,calendar,username,type_)
    
# Function sends a message to all active accounts 
def broadcast(message):
    
    # Loops through all active users
    for client in clients:

        # Finds username and creates a message object
        index = clients.index(client)
        username = usernames[index]
        
        # # Sends message to user
        sendToClient(username,message)

# Finds most recent active server (in the order of server 1,2,3)

# Thread to listen to server connection
def handle_server(server, number):
    global calendar
    global queueCounter
    global serverDrops
    global state
    # Set the server's activity as online (since it is connecting to you).
    serverActives[number - 1] = 1
    
    # Synchronize calendar log across servers
    qProposal = server.recv(1024)
    qProposal = pickle.loads(qProposal)
    proposalCount = 0
    for x in qProposal:
        if isinstance(qProposal[x], list):
            proposalCount += len(qProposal[x])
    localCount = 0
    for i in calendar:
        if isinstance(calendar[i], list):
            localCount += len(calendar[i])

    print(bcolors.OKBLUE + "Checking Calendar Log with SERVER" + str(number) + bcolors.ENDC)
    if proposalCount > localCount:
        calendar = qProposal
    
    queueCounter +=1

    print(calendar)
    # Unit test -- see if you synchronized to the right log.
    if (TESTING_PERSISTENCE and queueCounter > 1):

        if calendarLogEquals(sim, calendar):
            print(bcolors.BOLD + bcolors.OKCYAN + "UNIT TEST: SYNCHRONIZES with MOST UPDATED Calendar LOG (SERVER 2) ✅" + bcolors.ENDC)

        else:
            print(bcolors.FAIL + "UNIT TEST: FAILED TO SYNCHRONIZE WITH MOST UPDATED Calendar LOG." + bcolors.ENDC)

    while True:
        try:
            data = receiveData(server)
            serverProtocol(data)
        # This exception handles client crashes and logouts
        except Exception as e:
            serverDrops += 1
            print(bcolors.WARNING + "NUMBER OF SERVERDROPS " + str(serverDrops) + bcolors.ENDC)
            if serverDrops > 1:
                state = "L"
            
            serverActives[number - 1] = 0
            server.close()
            return

# Server thread to handle client <-> server communications
def handle_client(client, server1, server2):

    client_auth = False

    # While user is not authorized attempt to authenticate
    while not client_auth:
         
        # Recieve client Command -- Either type CA (Create Account) or L(Login)
        data = receiveData(client)
        print("User message:",data)
        # Split buffer data and extract the username and type that were sent   
        data = data.split(":",3)
        type_ = data[0]
        username = data[1]
        

        # If type is CA -> attempt to create an account with the username
        if type_ == "CA":

            # If username already exists -> Send client error
            if username in loginStatus:
                success = "Username-Already-Exists."
                success = Message(username, "SERVER", success)
                client.send(success.encode())

            # If username doesn't exist -> Send client account creation confirmation
            else:
                print("ACCOUNT CREATED")
                # Adds user to the server and logs them in
                usernames.append(username)
                clients.append(client)
                clientID[username] = client
                loginStatus[username] = True
                

                message = "C:" + username
                message = encoded_message(message)
                socket1.send(message)
                socket2.send(message)

                # log message as well


                sendToClient(username,"Successful-Account-Creation.")

                # Broadcasts new connection and authenticates connection
                client_auth = True


        # If type is L -> attempt to Login in with username
        elif type_ == "L":
            print("LOGGED IN")

            # If user does not exist -> send client login failure message
            if username not in loginStatus:
                failed = "Login-Failed"
                failed = Message(username,"SERVER", failed)
                client.send(failed.encode())
                print("LOGIN FAILED![sent to",client,"]")
            
            # TODO Allowing user to be authenticated even if someone else is logged in
            # TODO As primary servers switch user must still stay authenticated
            # If user is already active -> alert client!
            elif loginStatus[username]:
                active = "Account-Already-Active"
                active = Message(username, "SERVER", active)
                client.send(active.encode())
                print("ACCOUNT ALREADY ACTIVE!")
                client_auth = True


            # If username exists and is not active -> log user in
            else:
                # Log user in
                clients.append(client)
                usernames.append(username)
                clientID[username] = client
                loginStatus[username] = True

                # Send confirmation message
                sendToClient(username,"Login-Successful.")
                print("LOGIN SUCCESSFUL!")

                # Broadcast connection and deliver messages and authenticate client
                client_auth = True

    # Receives buffers from client and applies wire protocol
    while True:
        try:

            # Applies wire protocol to buffer -> returns a Message() or Command() objects
            obj = protocol_unpack(client)
            if isinstance(obj, Message):
                if ME == 0:
                    if serverActives[1] == 1:
                        socket1.send(obj.encode())
                    if serverActives[2] == 1:
                        socket2.send(obj.encode())
                if ME == 1:
                    if serverActives[0] == 1:
                        socket1.send(obj.encode())
                    if serverActives[2] == 1:
                        socket2.send(obj.encode())
                if ME == 2:
                    if serverActives[1] == 1:
                        socket1.send(obj.encode())
                    if serverActives[0] == 1:
                        socket2.send(obj.encode())
            # Applies an action to the object
            protocol_action(obj)


        # This exception handles client crashes and logouts
        except:

            # Removes client from active user lists
            index = clients.index(client)
            clients.remove(client)

            # Get clients username and then remove them from active user lists
            username = usernames[index]
            usernames.remove(username)

            
            # Only change loginStatus is user account isn't deleted
            if username in loginStatus:
                loginStatus[username] = False

            # Broadcast to everyone that the client disconnected
            broadcast(f'{username} has left the chat room!')
            break


# receive() listens for client and server connections and starts new threads when found
def receive():
    global queueCounter
    global leader
    global state
    # If not a leader -- close connection with client and respond with the leader.

    # When server starts
    print('Openning connection, running, and listening ...')
    
    while True:
        # Accepts new client on client connection
        client, address = myServer.accept()
        # Logs client connection information
        connection = ''
        if str(address[1]) == '12349' or str(address[1]) == '12346':
            connection = "SERVER1"
            # Open up receivng thread with Server 1
            servers.append(client)
            thread = threading.Thread(target=handle_server, args=(client,1))
            thread.start()
        elif str(address[1]) == '12350' or str(address[1]) == '12347':
            connection = "SERVER2"
            # Open up receiving thread with Server 2
            servers.append(client)
            thread = threading.Thread(target=handle_server, args=(client,2))
            thread.start()
        elif str(address[1]) == '12351' or str(address[1]) == '12348':
            connection = "SERVER3"
            # Open up receiving thread with Server 3
            servers.append(client)
            thread = threading.Thread(target=handle_server, args=(client,3))
            thread.start()
        else:
            # Open up a receiving thread with the client
            connection = "CLIENT"
            if state == "F" or state == "C":
                print(bcolors.WARNING + "I AM A FOLLOWER/CANDIDATE AND A CLIENT ATTEMPTED TO CONNECT." + bcolors.ENDC)
                print("SENDING TO(F|C):",client,"LEADER:",leader)
                message = "WL:" + str(leader)
                message = Message(" ", "SERVER", message)
                message = message.encode()
                client.send(message)
                client.close()
            else:
                print("ACCPETING A CONNECTION FROM A CLIENT B/C I AM STATE: ", state)
                print("SENDING TO(L):",client,"LEADER",leader)

                message = "WL:" + str(leader)
                message = Message(" ", "SERVER", message)
                message = message.encode()
                client.send(message)
                thread = threading.Thread(target=handle_client, args=(client, servers[0], servers[1]))
                thread.start()
        
        if not startedHeartBeat and (queueCounter > 1):
            thread = threading.Thread(target=startHeartBeat)
            thread.start()
        
        print((f'connection is established with: {connection}'))




# onConnection() broadcasts a username and dequeues their messages

if __name__ == "__main__":

    time.sleep(4)

    socket1.bind((HOST, PORT + 6))
    socket2.bind((HOST, PORT + 9))
    # attempt to connect to the three servers
    print("MY PORT IS ", PORT)
    if PORT == 12340:
        socket1.connect((HOST, 12341))
        socket2.connect((HOST, 12342))
    elif PORT == 12341:
        socket1.connect((HOST, 12340))
        socket2.connect((HOST, 12342))
    elif PORT == 12342:
        socket1.connect((HOST, 12341))
        socket2.connect((HOST, 12340))
    socket1.send(pickleMessage)
    socket2.send(pickleMessage)
    if (TESTING_PERSISTENCE):
        print(bcolors.BOLD + bcolors.OKCYAN + "UNIT TEST: Sends calendar log to other servers ✅" + bcolors.ENDC)
    receive()
