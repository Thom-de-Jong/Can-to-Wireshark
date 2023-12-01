import win32pipe, win32file
import subprocess
import struct
from typing import Any

from ctypes import *
from string import *
import platform

import can
import time

import argparse

class PipedReader(can.Listener):
    def __init__(self, pipe: int, *args: Any, **kwargs: Any) -> None:
        self.pipe = pipe
        super().__init__(*args, **kwargs)

    def on_message_received(self, msg: can.Message) -> None:
        newTimestamp = int(msg.timestamp * 1000000)
        data_str = '0x'
        for i in range(msg.dlc):
            data_str += '{:02x}'.format(msg.data[i]) + " "

        # SocketCAN - Header
        socketcan_header = msg.arbitration_id
        # if (options.extended):
        if msg.is_extended_id:
            socketcan_header = socketcan_header | (1 << 31)
        socketcan_header = (socketcan_header).to_bytes(4, byteorder='big')

        # SocketCAN - Length / Number of data bytes
        socketcan_length = msg.dlc.to_bytes(4, byteorder='little')
        
        # SocketCAN - CAN data (max. 8 bytes)
        socketcan_data = bytes(msg.data)

        # SocketCAN - Complete Frame
        # Combine elements into "complete" SocketCAN frame
        socketcan_frame = socketcan_header + socketcan_length + socketcan_data
        socketcan_frame_length = len(socketcan_frame)

        # Send received message to pipe
        packet_header = struct.pack("=IIII",
            newTimestamp // 1000000,        # timestamp seconds
            (newTimestamp - (newTimestamp // 1000000) * 1000000 ),  # timestamp microseconds
            socketcan_frame_length,        # number of octets of packet saved in file
            socketcan_frame_length,        # actual length of packet
        )
        try:
            win32file.WriteFile(self.pipe, packet_header)
            # Header is immediately followed by corresponding packet data = msg
            win32file.WriteFile(self.pipe, socketcan_frame)
        except Exception:
            pass


def main():
    # Parse CMD line arguments
    parser = argparse.ArgumentParser(description='Receives CAN messages and forwards them to pipe to be read and analyzed in WireShark')
    parser.add_argument('-i', '--interface', default='pcan', help='the CAN interface to read from')
    parser.add_argument('-c', '--channel', help='the CAN channel to read from')
    parser.add_argument('-b', '--baudrate', default=250000, type=int, help='the CAN baudrate of the bus')
    parser.add_argument('-v', '--verbose', action='store_true', help='activate extended debug logging to console')
    options = parser.parse_args()

    bus = None
    print('Current options: ', options)

    match (options.interface):
        case 'pcan':
            bus = can.Bus(interface="pcan", channel=options.channel, bitrate=options.baudrate)
        case 'canable':
            if options.channel == None:
                options.channel = "canable gs_usb"
            bus = can.Bus(interface="gs_usb", channel=options.channel, index=0, bitrate=options.baudrate)
        case other:
            print('Unknown interface specified:', options.interface)
            print('Known interface are: pcan, canable')
            exit(1)

    # Create the named pipe \\.\pipe\CAN
    CAN_pipe = win32pipe.CreateNamedPipe(
            r'\\.\pipe\CAN',
            win32pipe.PIPE_ACCESS_OUTBOUND,
            win32pipe.PIPE_TYPE_MESSAGE | win32pipe.PIPE_WAIT,
            1, 65536, 65536,
            300,
            None
        )

    # Open Wireshark, configure pipe interface and start capture (not mandatory, you can also do this manually)
    proc=subprocess.Popen(['C:\\Program Files\\Wireshark\\Wireshark.exe', r'-i\\.\pipe\CAN','-k'])

    # Connect to pipe
    win32pipe.ConnectNamedPipe(CAN_pipe, None)

    # Send header to pipe
    data = struct.pack("=IHHiIII",
            0xa1b2c3d4,   # magic number
            2,            # major version number
            4,            # minor version number
            0,            # GMT to local correction
            0,            # accuracy of timestamps
            65535,        # max length of captured packets, in octets
            227,          # data link type (DLT)   //  227 = SocketCAN
        )
    win32file.WriteFile(CAN_pipe, data)

    reader = PipedReader(CAN_pipe)
    listners = [reader]

    if (options.verbose):
        listners.append(can.Printer())

    # Start listening to the canbus
    notifier = can.Notifier(bus, listners)

    # Wait for user input to exit
    input("Press [ENTER] to exit\n")

    # Disconnect from named pipe
    win32pipe.DisconnectNamedPipe(CAN_pipe)

    # Stop listening to the canbus
    notifier.stop()

    # Shutdown the canbus
    bus.shutdown()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        pass