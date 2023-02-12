import socket
import select

HEADER_LENGTH = 10
IP = "127.0.0.1"
PORT = 1234

server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

# avoids port conflicts -- allows us to reconnect
server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

server_socket.bind((IP, PORT))

server_socket.listen()

# Initialized with server socket, client sockets will be added to this
sockets_list = [server_socket]

# dictionary {clients socket : user data}
clients = {}


def recieve_message(client_socket):
    try:
        message_header = client_socket.recv(HEADER_LENGTH)

        # if no message header recieved then client closed connection
        if not len(message_header):
            return False

        # gets the length of the message sent to client
        message_length = int(message_header.decode("utf-8").strip())

        #  returns dictionary with header and data aka the message
        # TODO think about how long the message is and implement safe guards!
        return {"header": message_header, "data": client_socket.recv(message_length)}

    # User closes out of their chat app
    except:
        return False


while True:
    # select() takes in 3 params: read-sockets list, write-sockets list, error-sockets list
    read_sockets, _, exception_sockets = select.select(sockets_list, [], sockets_list)

    for notified_socket in read_sockets:

        # Case: New connection to server (handle and logic for new connection)
        if notified_socket == server_socket:

            # Accepts the connection information and distructs into variables
            client_socket, client_address = server_socket.accept()

            # Get header data and message data
            user = recieve_message(client_socket)

            # Checks if user has disconnected
            if user is False:
                continue

            # Adds user to connected client list
            sockets_list.append(client_socket)

            # Updates the server information for client
            clients[client_socket] = user

            # Success message (client_address[0] is the IP and client_address[1] is the Port)
            print(f"Accepted new connection from {client_address[0]}:{client_address[1]} username: {user['data'].decode('utf-8')}")

        # Not a new connection to server
        else:
            message = recieve_message(notified_socket)

            # User disconnects - remove socket connection and information
            if message is False:
                print(
                    f"Closed connection from {clients[notified_socket]['data'].decode('utf-8')}")

                sockets_list.remove(notified_socket)
                del clients[notified_socket]
                continue

            # Get stored user header and data
            user = clients[notified_socket]

            # Print success message
            # TODO: I am unsure about the difference between user['data'] and message['data]... They should be the same value
            print(
                f"Received message from {user['data'].decode('utf-8')}: {message['data'].decode('utf-8')}")

            # Share message with everybody!!
            for client_socket in clients:

                # Send to everyone but the sender
                if client_socket != notified_socket:

                    # Sends to all users user data and then message data in a string
                    client_socket.send(
                        user['header']+user['data']+message['header']+message['data'])

    # If there are sockets with exceptions we disconnect them
    for notified_socket in exception_sockets:
        sockets_list.remove(notified_socket)
        del clients[notified_socket]
