
# CS262 FIVE9sCHAT (Design Exercise #3 Fault tolerant and Persistent)

This repository includes code for the 2-fault tolerant socket-server implementation (where we design our own wire protocol) a basic chat application (FIVE9sCHAT). 

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

**First Clone this branch**

    git clone https://github.com/Eyobdd/FIVE9sCHAT/tree/aneesh2faulttolerance
   Then CD into it
   

    cd FIVE9sCHAT
 Install the requirements
 

    sudo python3 -m pip install grpcio
    pip3 install --upgrade google-api-python-client
    python3 -m pip install --user grpcio-tools

  
# Run the Socket Servers (S1, S2, S3)

To run the socket-server example cd into the socket_server project folder **(in three terminals)**

    cd demo3Servers 

### Run the Servers (make sure HOST is set to your IP/localhost) (in three terminals)

 Run `python3 server.py 12340 0` in terminal one (this is the leader)
 Run `python3 server.py 12341 0` in terminal two
 Run `python3 server.py 12342 0` in terminal three

The 0/1 flag (the last argument) is for unit testing.

### Open up a client or two (make sure the HOST is the same as your server HOST)

    cd demo3Servers 
   Run `python3 client.py` in a terminal to open up a client. 


# Client Usage

 - The client will display the instructions.
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

# Engineering Notebook, Documentation, Design, Unit Tests,  and, decisions

If you would like to look at why and how we implemented each function, class, and how we structured out project. The document also shows how we ran unit tests, how we tested for message persistence and synchronization -- visit this [document](https://docs.google.com/document/d/1Jo6KQknoYV3AZgKZV2iSqN19xsV2lISwxZoacWMQzBY/edit?usp=sharing)
