#!/usr/bin/env python3
# coding: utf-8
"""
ATEMsocket: A socket that simulates the behaviour of Arduino's socket
to keep the ATEMConnectionManager class as close as possible to the original.
Part of the PyATEMMax library.
"""

from typing import Any, List, Optional, Union

import socket
import logging
from re import findall

from .ATEMProtocol import ATEMProtocol
from .ATEMUtils import hexStr


class ATEMUDPSocket():
    """
    This class emulates the behaviour of Arduino's UDP socket.

    Its purpose is to keep the code as close as possible to the original.
    """

    def __init__(self):
        """Create a ATEMUDPSocket object."""

        self.log = logging.getLogger('ATEMsocket')
        self.log.debug("Initializing")
        self.setLogLevel(logging.CRITICAL)  # Initially silent

        super().__init__()

        self.atem: ATEMProtocol = ATEMProtocol()
        self._socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self._socket.setblocking(False)

        self.connected = False

        self._buffer = []
        self.record_timer = {"hour":0, "minutes":0, "seconds":0}
        self.disk_stat    = False
        self.record_stat  = False
        

    def connect(self, ip: str) -> None:
        """
        Connect to a specified IP address and port.

        From: https://www.arduino.cc/en/Reference/ClientConnect
        """

        if self.connected:
            self.log.debug("Closing previous connection")
            self.stop()

        port = self.atem.UDPPort
        address = (ip, port)
        self.log.info(f"Connecting to {ip}:{port}")
        self._socket.connect(address)
        self.connected = True


    def stop(self) -> Any:
        """
        Disconnect from the server.

        From: https://www.arduino.cc/en/Reference/ClientStop
        """

        if self.connected:
            # No need to close an UDP socket in Python, and
            #  it does close the file descriptor...
            # self._socket.close()
            self.connected = False

        self.flushInputBuffer()


    def parsePacket(self) -> int:
        """
        Check for the presence of a UDP packet.

        parsePacket() must be called before reading the buffer.

        Returns:
            number of available bytes

        From: https://www.arduino.cc/en/Reference/EthernetUDPParsePacket
        """

        try:
            data, _ = self._socket.recvfrom(10240)
        except socket.error:
            data = []

        if data:
            self._buffer.extend(data)
            # print(data)
            self.AtemStatus(data)
            self.log.debug(f"Received {len(data)} new bytes [{hexStr(data)}] - " \
                            f" {self.available()} bytes available")

        return self.available()

    def AtemStatus(self, data):

            commands = {
                "RTMS": "record_update",
                "RTMR": "Recording Duration",
                "RTMD": "disk_update",
                "RMSu": "record settings"
            }
            for command in commands:
                index = data.find(bytes(command, 'utf-8'))
                if(index != -1):
                    start = index + 4
                    if(command == "RTMS"):
                        end = 12
                        rtms_data  = data[start: index+end]
                        start = 0
                        end   = 2
                        rec_status = rtms_data[start:end]
                        # print(rtms_data)
                        rec_status = int.from_bytes(rec_status, byteorder='big')
                        raw_rec  = rec_status
                        rec_status = self.__RecordingErrors(rec_status) or rec_status
                        print("*************************** Media Status ***************************")
                        print("rec status" , rec_status, raw_rec)
                        print("*************************** Media Status ***************************")
                        self.record_stat = rec_status
                        rec_time_left = rtms_data[4:8]
                        rec_time_left = int.from_bytes(rec_time_left, byteorder='big')/60
                        print("time left", rec_time_left)
                        # print(rec_status[1] << 4)           

                    if(command == "RTMD"):
                        
                        RTMD_LIST = []

                        count = data.count(bytes(command, 'utf-8'))
                        end   = 24
                        indices = [i for i in range(len(data)) if data.startswith(bytes(command, 'utf-8'), i)]

                        # print(indices)
                        # print("$$"* 100)
                        for i in indices:
                            temp = data[i:i+32]
                            RTMD_LIST.append(temp)
                            # print(data[i:i+32])
                            # print("--"* 100)
                        # print("##"*100)
                        for i in RTMD_LIST:
                            try:
                                start = 0+4
                                end   = start+4
                                disk_id   = i[start:end]
                                start = end
                                end   = end + 4
                                disk_time = i[start:end]
                                start = end
                                end   = end + 2
                                disk_stat = i[start:end]
                                is_del    = i[start+1:end]

                                start = end
                                end   = 26

                                volume_name = i[start:end]
                                disk_time   = int.from_bytes(disk_time, byteorder='big')/60
                                delete_flag = 1<<5
                                disk_stat   = int.from_bytes(disk_stat, byteorder='big', signed="True")
                                value       = disk_stat
                                is_del      = bool.from_bytes(is_del, byteorder='big' )
                                is_delete   = (value & delete_flag) == delete_flag
                                status      = value & (~delete_flag)

                                out_status  = status | (delete_flag if is_delete else 0 )

                                # if(not is_delete):
                                #     print("raw stat", disk_stat)
                                #     print("is del", is_del)
                                #     print("is_delete", is_delete)
                                #     print("input status", status)
                                #     print("out status", self.__diskStates(out_status))
                                #     self.disk_stat = self.__diskStates(out_status)
                                #     # print("DISK STATUS",  self.__diskStates(status))
                                #     print("disk time", disk_time)
                                #     print("volume name", volume_name.decode())
                            except Exception as e:
                                print(e)


                        # end = 10*8
                        # rtmd_data = data[start: index+end]
                        # print(rtmd_data)
                        # start = 0
                        # end   = 4
                        # disk_id   = rtmd_data[start:end]
                        # start = end
                        # end   = end + 4
                        # disk_time = rtmd_data[start:end]
                        # start = end
                        # end   = end + 2
                        # disk_stat = rtmd_data[start:end]
                        
                        # start = end
                        # end   = 22
                        # volume_name = rtmd_data[start:end]
                        # # print("RTMD:", rtmd_data)
                        # disk_time = int.from_bytes(disk_time, byteorder='big')/60
                        # ds = disk_stat
                        # disk_stat = int.from_bytes(disk_stat, byteorder='big', signed="True")

                        # print("%%"*100)
                        # print("full data", data)
                        # print("raw disk stat", ds)
                        # print("Disk Stats", self.__diskStates(disk_stat))
                        # print("disk time", disk_time)
                        # print("volume name", volume_name.decode())
                        # print("%%"*100)
                        
                    if(command == "RTMR"):
                        end = 8
                        rmtr_data = data[start: index+end]
                        rec_hour     = rmtr_data[0:1]
                        rec_hour     = int.from_bytes(rec_hour, byteorder='big')
                        rec_minutes  = rmtr_data[1:2]
                        rec_minutes  = int.from_bytes(rec_minutes, byteorder='big')
                        rec_seconds  = rmtr_data[2:3]
                        rec_seconds  = int.from_bytes(rec_seconds, byteorder='big')

                        self.record_timer['hour']    = rec_hour
                        self.record_timer['minutes'] = rec_minutes
                        self.record_timer['seconds'] = rec_seconds

                        if(rec_seconds > 2):
                            self.record_stat = True
                        else:
                            self.record_stat = False
                        # print("record Timer", rec_hour, rec_minutes, rec_seconds)

                    if(command == "RMSu"):
                        print("record settings")                        

    def __RecordingErrors(self, state):
        data = {
            0     : "No media", 
            2     : False,
            4     : "media full",
            8     : "media error",
            16    : "media unformatted",
            32    : "Dropping frames",
            32768 : "unknown"  
        }
        if(state in data):
            return data[state]
        return "unknown"

    def __recordingStatus(self, state):
        data = {
            0   : "idle",
            1   : "recording",
            128 : "stopping"
        }
        if(state in data):
            return data[state]
        return "unknown"

    def __diskStates(self, state):
        data = {
            1:"idle",
            2:"unformatted",
            4:"active",
            8:"recording"
        }
        if(state in data):
            return data[state]
        return "unknown"


    def available(self):
        """
        Get the number of bytes (characters) available for reading from the buffer.

        This is data that's already arrived.

        From: https://www.arduino.cc/en/Reference/EthernetUDPAvailable
        """

        return len(self._buffer)


    def read(self, buffer: List[int], maxSize: Optional[int] =None):
        """
        Read UDP data from the specified buffer.

        If no arguments are given, it will return the next character in the buffer.

        From: https://www.arduino.cc/en/Reference/EthernetUDPRead
        """

        # Clear buffer before receiving
        buffer[:] = []

        # Get data from the internal buffer
        count = 0
        maxCount = maxSize if maxSize else 9999999999999
        while count < maxCount:
            if self.available():
                buffer.append(self._buffer.pop(0))
                count += 1
            else:
                break

        return count


    def write(self, payload: Union[List[int], bytes], length: Optional[int] =None):
        """
        Write data to the server the client is connected to.

        This data is sent as a byte or series of bytes.

        From: https://www.arduino.cc/en/Reference/ClientWrite
        """

        if isinstance(payload, List):
            outbuf = bytes(payload)
        else:
            outbuf = payload

        outbuf = outbuf[:length] if length else outbuf

        self.log.debug(f"Sending buffer [{hexStr(outbuf)}]")
        return self._socket.send(outbuf)


    def flushInputBuffer(self):
        """Flush the input buffer"""

        oldbuffer = [b for b in self._buffer]
        self._buffer = []

        self.log.debug(f"Buffer flushed. Data: [{hexStr(oldbuffer)}]")
        return oldbuffer


    def peek(self):
        """Get a copy of the input buffer"""

        return [b for b in self._buffer]


    def setLogLevel(self, level: int) -> None:
        """
        Set the logging output level.

        Args:
            level (int): logging level as per Python's logging library
        """

        self.log.setLevel(level)
