# Import modules used
import sys
import threading
import socket
import os
import signal
from message import Message
from datetime import datetime, timedelta
import calendar
import customtkinter as ctk
from tkcalendar import DateEntry
from data_file import times, test_events

# Defined header length throughout wire protocol
HEADER_LENGTH = 10
HOST = "127.0.0.1"
SERVERSTATE = 1
ACTIVECONNECTION = None

# Constants used in text styling


class bcolors:
    HEADER = "\033[95m"
    OKBLUE = "\033[94m"
    OKCYAN = "\033[96m"
    OKGREEN = "\033[92m"
    WARNING = "\033[93m"
    FAIL = "\033[91m"
    ENDC = "\033[0m"
    BOLD = "\033[1m"
    UNDERLINE = "\033[4m"


# Creates an encoded bitstring from a message using our wire protocol


def encoded_message(message):
    message = message.encode("utf-8")
    header = f"{len(message) :< {HEADER_LENGTH}}".encode("utf-8")
    return header + message


def display_month(year, month, today, highlighted_days):
    # create a calendar object
    cal = calendar.monthcalendar(year, month)

    # create a header for the calendar
    title = calendar.month_name[month] + " " + str(year)
    header = "{:^55}".format(title)
    # create a list of day labels
    day_labels = ["Mo\t", "Tu\t", "We\t", "Th\t", "Fr\t", "Sa\t", "Su"]

    # create a string for the calendar days
    days_str = ""
    for week in cal:
        week_str = ""
        for day in week:
            if day == 0:
                week_str += "  \t"
            else:
                string = str(day)
                if day in highlighted_days:
                    string = bcolors.WARNING + string + bcolors.ENDC
                    store = "{:<2}\t".format(string.strip())
                    if day == today:
                        store = bcolors.BOLD + store + bcolors.ENDC
                else:
                    store = "{:>2}\t".format(day)
                    if day == today:
                        store = bcolors.BOLD + bcolors.OKGREEN + store + bcolors.ENDC
                week_str += store
        days_str += week_str.rstrip() + "\n"

    # combine the header, day labels, highlighted days, and calendar days into a single string
    output = header + "\n" + " ".join(day_labels) + "\n" + days_str

    # print the output string
    print(output)


def day_of_year_to_date(year, day):
    day = int(day)
    # Assuming 'day' variable contains the day of the year (1-365)
    # and 'date' variable contains the original date object
    start_of_year = datetime(year, 1, 1)
    date_from_day = start_of_year + timedelta(days=day - 1)

    # Extract the month and day from the new date object
    month = date_from_day.month
    day = date_from_day.day
    print("month is " + str(month) + " day is " + str(day))
    return day


# Thread that listens for communications from the server
def client_receive(connection):
    global SERVERSTATE
    while True:
        try:
            # Receives data sent by server
            data_header = connection.recv(HEADER_LENGTH).decode("utf-8")
            data_length = int(data_header.strip())
            data = connection.recv(data_length).decode("utf-8")

            # Converts received data into a message object
            data = Message.createMessageFromBuffer(data)

            # Checks if message sender is SERVER
            if data.sender == "SERVER":
                print("DATA DATA is ", data.data)

                # If message object doesn't encode properly
                if data.data[0] == "<":
                    continue

                # If SERVER is sending a list of active accounts
                if data.data[0:3] == "LA|":
                    # Unpacks the sent list
                    allAccounts = data.data.split("|")[1:]

                    # Prints list
                    print(
                        bcolors.OKGREEN
                        + "The server holds the following accounts."
                        + bcolors.ENDC
                    )
                    for account in allAccounts:
                        print(" -- > " + account)
                elif data.data[0:3] == "QE|":
                    allEvents = data.data.split("|")[1:]
                    print("---Events---\n")
                    for event in allEvents:
                        print(event)

                elif data.data[0:3] == "DC|":
                    try:
                        allEvents = data.data.split("|")[1:]
                        print("Events", allEvents)
                        now = datetime.now()
                        days = []
                        for day in allEvents:
                            days.append(day_of_year_to_date(2023, day))

                        print("DAYS", days)
                        display_month(now.year, now.month, now.day, days)
                    except Exception as e:
                        print("ERROR:", e)
                    # If SERVER Confirms account is successfully deleted
                elif data.data == "Account-Successfully-Deleted":
                    # Print message to console
                    print(
                        "Your account has been deleted. Your client connection will end. Bye, Bye"
                    )
                    print(
                        bcolors.BOLD
                        + bcolors.FAIL
                        + "EXITING CLIENT PROGRAM."
                        + bcolors.ENDC
                    )

                    # Exits terminal and closes socket
                    os.kill(os.getpid(), signal.SIGINT)

                # If SERVER cannot find and delete account
                elif data.data == "Account-Does-Not-Exist":
                    print(bcolors.FAIL + data.data + bcolors.ENDC)

                # If SERVER creates an event
                elif data.data == "Event-Created":
                    print(bcolors.OKBLUE + data.data + bcolors.ENDC)

                # If SERVER deletes an event
                elif data.data == "Event-Deleted":
                    print(bcolors.OKBLUE + data.data + bcolors.ENDC)

                # If SERVER is sending a broadcast message
                else:
                    print(
                        bcolors.OKCYAN
                        + "["
                        + data.sender
                        + "] "
                        + bcolors.ENDC
                        + data.data
                    )

            # If the message is sent from another user
            if data.sender != "SERVER":
                print(
                    bcolors.OKCYAN + "[" + data.sender + "] " + bcolors.ENDC + data.data
                )

        # Any general errors are caught here
        except Exception as e:
            print("ERROR:", e)
            print(
                bcolors.WARNING
                + "SERVER DROPPED. RECONNECTING. PRESS ENTER. "
                + bcolors.ENDC
            )
            connection.close()
            SERVERSTATE = 10
            sys.exit()


# Thread that sends authenticated communication to the server


def client_send(connection, state):
    while True:
        if state != SERVERSTATE:
            sys.exit()
        # Asks user for input
        inp = input(
            bcolors.BOLD
            + "COMMANDS"
            + bcolors.ENDC
            + ": "
            + bcolors.BOLD
            + "\n"
            + "LA"
            + bcolors.ENDC
            + " - List accounts. "
            + bcolors.BOLD
            + "\n"
            + "USERNAME-> MESSAGE"
            + bcolors.ENDC
            + " - Send USERNAME MESSAGE."
            + "\n"
            + bcolors.BOLD
            + "DA"
            + bcolors.ENDC
            + " - Delete your account."
            + "\n"
            + bcolors.BOLD
            + "Q"
            + bcolors.ENDC
            + " - Quit client program."
            + "\n"
            + bcolors.BOLD
            + "CE"
            + bcolors.ENDC
            + " - Create Calendar Event."
            + "\n"
            + bcolors.BOLD
            + "DE"
            + bcolors.ENDC
            + " - Delete Calendar Event."
            + "\n"
        )

        # If user enters nothing
        if inp == "":
            print(bcolors.WARNING + "Empty input" + bcolors.ENDC)

        # User enters something
        else:
            # If input is not a message
            if "->" not in inp:
                if inp == "DE":
                    title = ""
                    validNum = False
                    while title == "":
                        title = input("Event Title: ")
                        title = title.strip()

                    while not validNum:
                        try:
                            day = input("Enter the event date (YYYY-MM-DD): ")
                            day = day.strip()
                            date = datetime.strptime(day, "%Y-%m-%d")
                            day = date.timetuple().tm_yday
                            validNum = True
                        except:
                            continue

                    print(
                        "Username: "
                        + username
                        + " | Title: "
                        + title
                        + " | Day:"
                        + str(day)
                    )

                    message = f"DE:{username}:{title}:{day}"
                    message = encoded_message(message)
                    connection.send(message)

                if inp == "CE":
                    title = ""
                    day = ""
                    validNum = False

                    while title.strip() == "":
                        title = input("Event Title: ")

                    while not validNum:
                        try:
                            day = input("Enter a date (YYYY-MM-DD): ")
                            date_str = day.strip()
                            date = datetime.strptime(date_str, "%Y-%m-%d")
                            day = date.timetuple().tm_yday

                            validNum = True
                        except Exception as error:
                            print("something went wrong...", error)
                            continue

                    validNum = False

                    while not validNum:
                        try:
                            start_time = input(
                                "Enter a start time in 24H-time (HH:MM): "
                            )
                            hours, minutes = map(int, start_time.split(":"))
                            start_time = hours * 60 + minutes
                            if start_time < 60 * 24:
                                validNum = True
                            else:
                                print("Enter a start time on the same day")
                        except:
                            continue

                    validNum = False

                    while not validNum:
                        try:
                            end_time = input("How long is this event? (in minutes): ")
                            end_time = start_time + int(end_time.strip())
                            validNum = True
                        except:
                            continue

                    message = f"CE:{username}:{title}:{day}:{start_time}:{end_time}"
                    message = encoded_message(message)
                    connection.send(message)

                # Check if it List Accounts request
                if inp == "LA":
                    # Sends List Accounts request
                    message = f"LA:{username}"
                    message = encoded_message(message)
                    connection.send(message)

                elif inp[0:3] == "QE[":
                    print("user wants to query")
                    date = inp.split("[")
                    date = date[1]
                    date = date[:-1]
                    message = f"QE:{username}:{date}"
                    print("message")
                    connection.send(encoded_message(message))

                elif inp == "DC":
                    # Sends List Accounts request
                    message = f"DC:{username}"
                    message = encoded_message(message)
                    connection.send(message)
                # Check if it is a Delete Account request
                elif inp == "DA":
                    # Sends delete account request with authorized username
                    message = f"DA:{username}"
                    message = encoded_message(message)
                    connection.send(message)

                # Check if the user is trying to quit the program
                elif inp == "Q":
                    # Prints exit message
                    print(
                        bcolors.BOLD
                        + bcolors.FAIL
                        + "EXITING CLIENT PROGRAM."
                        + bcolors.ENDC
                    )

                    # Exits terminal and closes socket
                    os.kill(os.getpid(), signal.SIGINT)
                    break

                # User submitted invalid message syntax
                else:
                    # Prints syntax warning message
                    print(
                        bcolors.WARNING
                        + "NEED TO SPECIFY USER. Correct usage: USER-> Message."
                        + bcolors.ENDC
                    )

            # User submitted valid message syntax
            else:
                # Breaks input into recipient and message based on "->"
                inputList = inp.split("->")
                recipient = inputList[0]
                message = inputList[1]

                # Creates a message object
                message = Message(recipient, username, message)
                message = message.encode()

                # Sends message to server
                connection.send(message)


def check_server_connection():
    global SERVERSTATE
    global ACTIVECONNECTION
    print("HERE:", SERVERSTATE)
    # while True:
    # # TRY TO CONNECT TO SERVER 1
    server1GoesThrough = True
    server2GoesThrough = True
    server2GoesThrough = True

    try:
        client1 = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client1.connect((HOST, 12340))
        print("HERE2:")

        # request_message = f"L:{username}"
        # request_message = encoded_message(request_message)
        # client1.send(request_message)
        # Keep track of leader server
        data_header = client1.recv(HEADER_LENGTH).decode("utf-8")
        data_length = int(data_header.strip())
        data = client1.recv(data_length).decode("utf-8")
        print("SERVER LEADER:",data)
        real_leader = int(data.split(":")[4].strip())
        if real_leader != 12340:
            try:
                leader_connection = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                leader_connection.connect((HOST,real_leader))
                ACTIVECONNECTION = leader_connection
                client1.close()
                SERVERSTATE = real_leader-12340+1
            except:
                ACTIVECONNECTION = None
            return
        print("DATA:",data)
        SERVERSTATE = 1
        data_header = client1.recv(HEADER_LENGTH).decode("utf-8")
        data_length = int(data_header.strip())
        data = client1.recv(data_length).decode("utf-8")

        # request_message = f"DC:{username}"
        # request_message = encoded_message(request_message)
        # client1.send(request_message)

        # receive_thread1 = threading.Thread(target=client_receive, args=[client1])
        # receive_thread1.start()

        # send_thread1 = threading.Thread(target=client_send, args=[client1, 1])
        # send_thread1.start()
        print("Connected to server 1")
        ACTIVECONNECTION = client1
    except:
        check_server_connection()
        server1GoesThrough = False

    if not server1GoesThrough:
        server2GoesThrough = True

        # TRY TO CONNECT TO SERVER 2
        try:
            client2 = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            client2.connect((HOST, 12341))
            # print("MADE IT HERE2", username)
            # request_message = f"L:{username}"
            # request_message = encoded_message(request_message)
            # client2.send(request_message)
            data_header = client2.recv(HEADER_LENGTH).decode("utf-8")
            data_length = int(data_header.strip())
            data = client2.recv(data_length).decode("utf-8")
            print("SERVER LEADER:",data.split(":")[4])
            real_leader = int(data.split(":")[4].strip())
            if real_leader != 12341:
                try:
                    leader_connection = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    leader_connection.connect((HOST,real_leader))
                    ACTIVECONNECTION = leader_connection
                    client2.close()
                    SERVERSTATE = real_leader-12340+1
                except:
                    check_server_connection()
                    ACTIVECONNECTION = None
                return

            SERVERSTATE = 2
            data_header = client2.recv(HEADER_LENGTH).decode("utf-8")
            data_length = int(data_header.strip())
            data = client2.recv(data_length).decode("utf-8")
            # receive_thread2 = threading.Thread(target=client_receive, args=[client2])
            # receive_thread2.start()

            # send_thread2 = threading.Thread(target=client_send, args=[client2, 2])
            # send_thread2.start()
            ACTIVECONNECTION = client2
            print("Connected to server 2")
            return
        except:
            server2GoesThrough = False

    if not server2GoesThrough:
        server3GoesThrough = True
        # TRY TO CONNECT TO SERVER 3
        try:
            client3 = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            client3.connect((HOST, 12342))
            
            data_header = client3.recv(HEADER_LENGTH).decode("utf-8")
            data_length = int(data_header.strip())
            data = client3.recv(data_length).decode("utf-8")
            print("SERVER LEADER:",data.split(":")[4])
            real_leader = int(data.split(":")[4].strip())
            if real_leader != 12342:
                try:
                    leader_connection = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    leader_connection.connect((HOST,real_leader))
                    ACTIVECONNECTION = leader_connection
                    client3.close()
                    SERVERSTATE = real_leader-12340+1
                except:
                    check_server_connection()
                    ACTIVECONNECTION = None
                return
            # request_message = f"L:{username}"
            # request_message = encoded_message(request_message)
            # client3.send(request_message)
            SERVERSTATE = 3
            data_header = client3.recv(HEADER_LENGTH).decode("utf-8")
            data_length = int(data_header.strip())
            data = client3.recv(data_length).decode("utf-8")
            # receive_thread3 = threading.Thread(target=client_receive, args=[client3])
            # receive_thread3.start()

            # send_thread3 = threading.Thread(target=client_send, args=[client3, 3])
            # send_thread3.start()
            print("Connected to server 3")
            ACTIVECONNECTION = client3
            return
        except:
            server3GoesThrough = False

        if not server3GoesThrough:
            ACTIVECONNECTION = None
            return


# def start_app():
#     authenticate()
#     # Run the connection code in a separate thread so that it runs in the background
#     print("STARTED")
#     # connect_thread = threading.Thread(target=connect_to_server)
#     # connect_thread.start()

#     # Open the login page of the app

events_added = 0

if __name__ == "__main__":
    # Create a socket and connect to the server
    SERVERSTATE = 1
    auth = False
    username = ""
    selected_days = []
    removed_widgets = []


    ctk.set_appearance_mode("dark")
    ctk.set_default_color_theme("dark-blue")

    root = ctk.CTk()
    root.title("Calendar Manager")
    root.geometry("1200x800")

    # Call start_app() after the main window is created
    # root.after(0, start_app)

    theme = {
        "primary": "#191970",
        "secondary": "#005A9C",
        "medium": "#b3cee5",
        "light": "#f0f8ff",
        "selected": "#339933",
        "font": ctk.CTkFont(family="Roboto"),
    }

    def on_enter(event):
        parent = event.widget.winfo_parent()
        button = root.nametowidget(parent)
        if button.cget("fg_color") != theme["selected"]:
            if isinstance(button, ctk.CTkButton):
                button.configure(fg_color=theme["secondary"], text_color=theme["light"])

    def on_leave(event):
        parent = event.widget.winfo_parent()
        button = root.nametowidget(parent)
        if button.cget("fg_color") != theme["selected"]:
            if isinstance(button, ctk.CTkButton):
                button.configure(fg_color=theme["light"], text_color=theme["secondary"])
            # button = buttons.get(event.widget)
            # button.configure(fg_color=theme["light"], text_color=theme["secondary"])
    def add_events():
        global events_added
        added_events = [
            {
                "day": "05-08-23",
                "title": "Pick lunch spot with friends",
                "start": "11:00 AM",
                "end": "12:00 PM"
            },
            {
                "day": "05-10-23",
                "title": "Talk about crypto with Prof. Waldo",
                "start": "2:15 PM",
                "end": "3:30 PM"
            },
            {
                "day": "05-12-23",
                "title": "Final Paper Due",
                "start": "5:00 PM",
                "end": "5:00 PM"
            },
            {
                "day": "05-19-23",
                "title": "Study Group",
                "start": "7:00 PM",
                "end": "9:00 PM"
            }
        ]
        test_events.append(added_events[events_added])
        events_added+=1
    def show_events():
        def destroy_widgets(widget):
            removed_widgets.append(widget)
            widget.grid_remove()
            
        
        for widget in root.grid_slaves(row=1, column=1):
            widget.destroy()
        display_frame = ctk.CTkFrame(root)
        display_frame.grid(row=1, column=1, pady=10)

        display_label = ctk.CTkLabel(
            root, text="Upcoming Events:", anchor="center"
        )
        display_label.grid(
            row=0,
            column=1,
            pady=10,
            padx=10,
        )
        validrows=0
        for event in range(len(test_events)):
            
            event_frame = ctk.CTkFrame(display_frame)
            print("HERE:",test_events[event])
            event_frame.grid(row=validrows,pady=5,padx=10)
            event_frame.grid(sticky="w")

            validrows+=1

            
            day_label = ctk.CTkLabel(event_frame,text=test_events[event]["day"]+" | ")
            day_label.grid(row=0,column=0,padx=(5,0))
            
            title_label = ctk.CTkLabel(event_frame,text=test_events[event]["title"]+" | ")
            title_label.grid(row=0,column=1)
            
            duration = ctk.CTkLabel(event_frame,text=test_events[event]["start"]+" - "+test_events[event]["end"])
            duration.grid(row=0,column=2,padx=(0,5))
            
            delete_button = ctk.CTkButton(event_frame,text="Delete",width=15,command=lambda: destroy_widgets(event_frame))
            delete_button.grid(row=0,column=3,padx=5,pady=5)
            
            print("Day:",datetime.strptime(test_events[event]["day"],"%m-%d-%y").day)
            print("Days:",selected_days)
            print("Not-Selected:",str(int(datetime.strptime(test_events[event]["day"],"%m-%d-%y").day)) not in selected_days)
            if event_frame in removed_widgets or len(selected_days) != 0 and str(int(datetime.strptime(test_events[event]["day"],"%m-%d-%y").day)) not in selected_days:
                    event_frame.grid_forget()
            # delete_button.bind("<Button-1>",destroy_widgets)


    def on_click(event):
        parent = event.widget.winfo_parent()
        button = root.nametowidget(parent)
        print("Selected Days Before:",selected_days)

        if button.cget("fg_color") == theme["secondary"]:
            print("Clicked",int(button.cget("text")))
            button.configure(fg_color=theme["selected"], text_color=theme["light"])
            if str(int(button.cget("text"))) not in selected_days:
                selected_days.append(str(int(button.cget("text"))))
        elif (
            button.cget("fg_color") == theme["light"]
            or button.cget("fg_color") == theme["selected"]
        ):
            print("Unclicked")
            button.configure(fg_color=theme["light"], text_color=theme["secondary"])
            selected_days.remove(str(int(button.cget("text"))))
        print("Selected Days After:",selected_days)
        show_events()

    def show_calendar():
        def create_event(title, day, start, end):
            global date_entry
            command = f"CE:USERNAME:{title}:{day}:{start}:{end}"
            print("Created Event:", command)
            add_events()
            title_entry.delete(0, "end")
            today = datetime.now()
            date_entry = DateEntry(
                event_frame, year=today.year, month=today.month, day=today.day
            )
            start_time_combobox.set("Set Start Time")
            end_time_combobox.set("Set End Time")

        title_label = ctk.CTkLabel(
            root,
            text=datetime.now().strftime("%B"),
            font=ctk.CTkFont(family="Roboto", size=16),
        )
        title_label.grid(row=0, column=0, pady=(10, 0), padx=10)

        calendar_frame = ctk.CTkFrame(root)
        calendar_frame.grid(row=1, column=0, pady=(0, 10), padx=20)

        today = datetime.now()
        cal = calendar.Calendar(firstweekday=calendar.SUNDAY)
        month_days = cal.itermonthdates(today.year, today.month)
        
        for i, date in enumerate(month_days):
            btn_frame = ctk.CTkFrame(calendar_frame)
            btn_frame.grid(row=(i // 7), column=i % 7, sticky="nsew")
            if datetime.now().month != date.month:
                btn = ctk.CTkButton(
                    btn_frame,
                    text=date.strftime("%d"),
                    width=4,
                    fg_color=theme["medium"],
                    text_color=theme["primary"],
                )
            else:
                btn = ctk.CTkButton(
                    btn_frame,
                    text=date.strftime("%d"),
                    width=4,
                    fg_color=theme["light"],
                    text_color=theme["secondary"],
                )
                btn.bind("<Enter>", on_enter)
                btn.bind("<Leave>", on_leave)

            btn.grid(row=0, column=0, sticky="nsew", padx=10, pady=5)
            btn.bind("<Button-1>", on_click)

        event_frame = ctk.CTkFrame(root)
        event_frame.grid(row=2, column=0, pady=10)

        title_label = ctk.CTkLabel(event_frame, width=100, text="Title:", anchor="e")
        title_label.grid(row=1, column=0, pady=(10, 0), padx=10)

        title_entry = ctk.CTkEntry(event_frame)
        title_entry.grid(row=1, column=1, pady=(10, 0), padx=10)

        date_label = ctk.CTkLabel(
            event_frame, width=100, text="Date(MM/DD/YY):", anchor="e"
        )
        date_label.grid(row=2, column=0, pady=(10, 0), padx=10)

        date_entry = DateEntry(event_frame, width=12, borderwidth=2)
        date_entry.grid(row=2, column=1, pady=(10, 0), padx=10)

        def on_start_time_changed(*args):
            if start_time.get():
                x=3
                # st_in_dt = datetime.strptime(start_time.get(), "%I:%M %p")
                # if st_in_dt.time():
                #     start_time_combobox.configure(border_color="red")
                # else:
                #     start_time_combobox.configure(border_color="")
            else:
                start_time_combobox.configure(border_color="")

        def on_end_time_changed(*args):
            if end_time.get():
                et_in_dt = datetime.strptime(end_time.get(), "%I:%M %p")
                if et_in_dt < datetime.strptime(start_time.get(), "%I:%M %p"):
                    end_time_combobox.configure(border_color="red")
                else:
                    end_time_combobox.configure(border_color="")
            else:
                end_time_combobox.configure(border_color="")

        start_time = ctk.StringVar()

        start_time_label = ctk.CTkLabel(
            event_frame, width=100, text="Start Time:", anchor="e"
        )
        start_time_label.grid(row=3, column=0, pady=(10, 0), padx=10)

        start_time_combobox = ctk.CTkComboBox(
            event_frame, variable=start_time, values=times, state="readonly"
        )
        start_time_combobox.grid(row=3, column=1, pady=(10, 0), padx=10)
        start_time.trace_add("write", on_start_time_changed)

        end_time = ctk.StringVar()

        end_time_label = ctk.CTkLabel(
            event_frame, width=100, text="End Time:", anchor="e"
        )
        end_time_label.grid(row=4, column=0, pady=(10, 0), padx=10)

        # if start_time.get() != "":
        #     st_in_dt = datetime.strptime(start_time.get(), "%I:%M %p")
        #     print(st_in_dt)
        #     valid_end_times = [
        #         time for time in times if datetime.strptime(time, "%I:%M %p") > st_in_dt
        #     ]

        # if len(valid_end_times) == 0:
        #     valid_end_times = ["Select Start Time First"]

        end_time_combobox = ctk.CTkComboBox(
            event_frame, variable=end_time, values=times, state="readonly"
        )

        end_time_combobox.grid(row=4, column=1, pady=(10, 0), padx=10)
        end_time.trace_add("write", on_end_time_changed)

        create_button = create_button = ctk.CTkButton(
            event_frame,
            text="Create Event",
            width=15,
            command=lambda: create_event(
                title_entry.get(), date_entry.get(), start_time.get(), end_time.get()
            ),
        )

        create_button.grid(row=5, column=0, columnspan=2, pady=20, padx=10)
        create_button.bind(
            "<Button-1>",
            create_event(title_entry, date_entry, start_time.get(), end_time.get()),
        )

            
            
            
            

    def authenticate():
        def login():
            username = username_entry.get()
            print(f"L:{username}")
            if username.strip() == "":
                username_entry.configure(border_color="red")
                username_entry.delete(0, "end")
                return
            if username != "":
                username_entry.configure(border_color="#979DA2")
                  
               
            login_frame.pack_forget()
            print("CONNECTION-BEFORE:", ACTIVECONNECTION)
            check_server_connection()
            print("CONNECTION-AFTER:", ACTIVECONNECTION)
            
            if not ACTIVECONNECTION:
                
                error_frame = ctk.CTkFrame(root)
                error_frame.pack(pady=40,padx=40)
                
                error_label = ctk.CTkLabel(root,text="Unable to connect to servers.\nPlease try again soon...",anchor="center")
                error_label.pack(pady=40,padx=40)
                return

            message = f"L:{username}"
            message = encoded_message(message)
            ACTIVECONNECTION.send(message)   
            
            data_header = ACTIVECONNECTION.recv(HEADER_LENGTH).decode("utf-8")
            data_length = int(data_header.strip())
            print("Data from:",ACTIVECONNECTION)
            data = ACTIVECONNECTION.recv(data_length).decode("utf-8")
            
            print("DATA2:",data)
            
            data_header = ACTIVECONNECTION.recv(HEADER_LENGTH).decode("utf-8")
            data_length = int(data_header.strip())
            print("Data from:",ACTIVECONNECTION)
            data = ACTIVECONNECTION.recv(data_length).decode("utf-8")
            
            
            
            show_calendar()
            show_events()
            
            

        login_frame = ctk.CTkFrame(root)
        login_frame.pack(padx=40, pady=40)

        title = ctk.CTkLabel(
            login_frame,
            text="RAFT-CAL V.1",
            anchor="center",
            font=ctk.CTkFont(family="Roboto", size=44, weight="bold"),
        )
        title.grid(
            row=0,
            column=0,
            columnspan=2,
            padx=20,
            pady=20,
        )

        username_label = ctk.CTkLabel(login_frame, text="Username:", anchor="center")
        username_label.grid(row=1, column=0, padx=10, pady=10)

        username_entry = ctk.CTkEntry(login_frame)
        username_entry.grid(row=1, column=1, padx=10, pady=10)

        login_button = ctk.CTkButton(
            login_frame, text="Login", width=100, command=login
        )
        login_button.grid(row=2, column=0, columnspan=2, padx=20, pady=20)

        
    authenticate()

    # Run the main loop of the application
    root.mainloop()
