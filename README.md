# RAFTCal

Welcome to RAFTCal!

This project implements a shared calendar that is persistent and 2-fault tolerant. We achieved this by implementing the RAFT consensus algorithm and building a GUI using the customtkinter Python library.

## Features

- Shared calendar accessible by multiple clients
- RAFT consensus algorithm for reliability and fault tolerance
- Persistent data storage
- Custom GUI built with customtkinter library
- Full event management: Users can easily add, delete, and view events on the shared calendar.





## Requirements

- Python 3.x
- customtkinter
- tkcalendar

## Usage

To start the RAFTCal servers, run the following commands in separate terminals:


Terminal 1: 
```bash
python3 server.py 12340 0
```
Terminal 2: 
```bash
python3 server.py 12341 0
```
Terminal 3: 
```bash
python3 server.py 12342 0
```

This will start 3 servers on ports 12340, 12341, and 12342 respectively.

To start the graphical user interface (GUI), run the following command in another terminal:

```bash
python3 clientGUI.py
```

This will launch the GUI for the RAFTCal calendar. Multiple clients can connect to the server and access the shared calendar. 

## Unit Tests

To run the unit tests, execute the following command in the terminal: 

```
python3 unitTest.py PORT
```

Replace `PORT` with one of the following values: `12340`, `12341`, or `12342`. Start one instance of `unitTest.py` for each of the three ports.

After you have done this, start the graphical user interface (GUI).

Run the following command in another terminal to do this:

```bash
python3 clientGUI.py
```

## Contributors

- [Eyob Davidoff](https://github.com/eyobdd)
- [Aneesh Muppidi](https://github.com/aneeshers)
