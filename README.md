# CS262 FIVE9sCHAT (Wire Protocol Design Exercise)

This repository includes code for both the socket-server implementation (where we design our own wire protocol) and the grpc implementation of a basic chat application (FIVE9sCHAT). 

The application allows for the following features (**client side)**:

 - Listing all accounts (and whether they are active or inactive) on the
   server. 
  
 - Creating an account.

 

 - Logging into an account.
 - Deleteing an account.

 

 - Sending a message to an account (whether they are active or   
   inactive).

 

 - Recieving messages.
 - Recieving "old" messages that were    sent to you when you were
   logged out.
 - Quiting the client.

# Installation

**Requirements:**  Python 3 or 3+, grpcio==1.9.0, grpcio-tools==1.9.0, google-api-python-client, protobuf==3.18.3, six==1.11.0

Open up terminal

**First Clone this repository**

    git clone https://github.com/Eyobdd/FIVE9sCHAT.git
   Then CD into it
   

    cd FIVE9sCHAT
 Install the requirements
 

    sudo python3 -m pip install grpcio
    pip3 install --upgrade google-api-python-client
    python3 -m pip install --user grpcio-tools

  
# Socket Server

To run the socket-server example cd into the socket_server project folder

    cd socket_server 

### Run the Server

First, make sure the HOST variable in line 9 of `server.py` is set to your IP address. If you are running it on your laptop, you can always use your localhost address 127.0.0.1.

Then run `python3 server.py`


### Open up a client
For the client to run, make sure you set the correct host (the same host that you set in  server.py). This can be found in line 38, known as the variable address.


You can open any number of terminal windows, each window represents a new client. Each time you open up a new terminal window to start a client, make sure to `cd FIVE9sCHAT/socket_server`.   Then run `python3 client.py`.

# GRPC
To run the grpc chat server example cd into the grpc_server project folder

    cd grpc_server 

### Run the Server

First, make sure the HOST variable in line 201 of `server.py` is set to your IP address. If you are running it on your laptop, you can always use your localhost address 127.0.0.1.

Then run `python3 server.py`

### Open up a client
For the client to run, make sure you set the correct host (the same host that you set in  server.py). This can be found in line 12, known as the variable address.


You can open any number of terminal windows, each window represents a new client. Each time you open up a new terminal window to start a client, make sure to `cd FIVE9sCHAT/grpc_server`.   Then run `python3 client.py`.

# Client Usage

 - Both client programs (socket and GRPC) will display the instructions.
   The client will show you which accounts currently exist on the server
   and their activity status.
 - The client will ask you to create an account or login -- type C to
   create an account and type L to login into an account.
 - Then enter the username for the account you are trying to create or
   trying to loginto The client will display a success or failure
   message (in which case it will prompt you again to create or login).

Once you have created an account or logged in, you can chat with other users, display the current users, delete your account, or quit the program. Again, the program displays this but here are the commands:

  

 - Type `LA` to list the accounts.

   

 - Type `USERNAME-> Message` to send a specific message to USERNAME.
       **Note there should be no space in between the USERNAME and the message indicator ->** For example `USERNAME -> Message` would
   **not** work.

    

 - Type `DA` to delete your account.

	

 - Type `Q` to log out or quit the program.

# Documentation, Design, Unit Tests,  and, decisions

If you would like to look at why and how we implemented each function, class, and how we structured out project -- visit this [document](https://docs.google.com/document/d/11gngpSWqSKRBviOlSrdSWf1R94DzP9_fe0PSbQpAng8/edit?usp=sharing) 
