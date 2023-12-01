# Can to Wireshark
Python script to record CAN messages and forward them via pipes to WireShark.

On Linux, most CAN adapters use SocketCAN which can be opened in Wireshark out of the box.
On windows, users are expected to use the software provided by the manufacturer wich is not so nice.

This script can be run on windows in order to pipe the CAN messages into Wireshark.

## Usage
Implemented interfaces are: "pcan", "canable"

```
usage: Can-To-Wireshark.py [-h] [-i INTERFACE] [-c CHANNEL] [-b BAUDRATE] [-v]      

Receives CAN messages and forwards them to pipe to be read and analyzed in WireShark

options:
  -h, --help            show this help message and exit
  -i INTERFACE, --interface INTERFACE
                        the CAN interface to read from
  -c CHANNEL, --channel CHANNEL
                        the CAN channel to read from
  -b BAUDRATE, --baudrate BAUDRATE
                        the CAN baudrate of the bus
  -v, --verbose         activate extended debug logging to console
```

## Default
```
python ./Can-to-Wireshark.py
```
I the same as
```
python ./Can-to-Wireshark.py -i pcan -c PCAN_USBBUS1 -b 250000
```

## ToDo
Implement and test all other interfaces provided by python-can.
If you want to contribure, you are free to open a pull request.
