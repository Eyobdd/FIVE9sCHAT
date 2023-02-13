import threading
import socket

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


alias = input('Choose an alias >>> ')
client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client.connect(('127.0.0.1', 59000))


def client_receive():
    while True:
        try:
            message = client.recv(1024).decode('utf-8')
            if "you are now connected!" in message:
                print("We have connected. \n")
            if message == "alias?":
                client.send(alias.encode('utf-8'))
            elif message == "The user you are trying to contact does not exist.":
                print(bcolors.WARNING + message + bcolors.ENDC)
            else:
                print(bcolors.OKBLUE + message + bcolors.ENDC + '\n', end='')
        except:
            print('Error!')
            client.close()
            break


def client_send():
    while True:
        inp = input("What would you like to say? To whom?\n")
        if "->" not in inp:
            print(bcolors.WARNING + "NEED TO SPECIFY USER. Correct usage: USER-> Message." + bcolors.ENDC)
        else:    
            message = f'{alias}-> {inp}'
            client.send(message.encode('utf-8'))
        


receive_thread = threading.Thread(target=client_receive)
receive_thread.start()

send_thread = threading.Thread(target=client_send)
send_thread.start()
