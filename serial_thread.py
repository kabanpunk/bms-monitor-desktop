import json
import sys
from enum import Enum

from PyQt5.QtWidgets import QApplication, QMainWindow, QTextEdit
from PyQt5.QtCore import QThread, pyqtSignal
import serial

import serial
from typing import Union


class DataTransferMode(Enum):
    JSON = 1
    BYTES = 2


class WriteSerialThreadException(Exception):
    """
    Exception raised for errors that occur during writing data to Serial.

    Attributes:
        ser (Union[serial.Serial, None]): The Serial object being used for communication.
        running (bool): Indicates whether the serial thread is running or not.
    """

    def __init__(self, ser: serial.Serial | None, running: bool):
        super().__init__()
        self.ser = ser
        self.running = running

    def __str__(self) -> str:
        if not isinstance(self.ser, serial.Serial):
            return "Invalid Serial object provided."
        if not self.running:
            return "Serial thread is not running."

        error_message = "Error writing data to Serial. "
        if self.ser.is_open:
            error_message += "Serial port is open."
        else:
            error_message += "Serial port is closed."
        return error_message


class SerialThread(QThread):
    json_data_received = pyqtSignal(dict)
    bytes_data_received = pyqtSignal(bytes)

    def __init__(self, serial_port=None, baud_rate=None):
        super().__init__()
        self.__serial_port = serial_port
        self.__baud_rate = baud_rate
        self.__running = False
        self.__ser = serial.Serial()
        self.__mode: DataTransferMode = DataTransferMode.JSON

    def set_mode_to_json(self):
        self.__mode = DataTransferMode.JSON

    def set_mode_to_bytes(self):
        self.__mode = DataTransferMode.BYTES

    def run(self):
        self.__running = True
        self.__ser = serial.Serial(self.__serial_port, self.__baud_rate, timeout=1)
        while self.__running:
            if self.__ser.in_waiting:
                if self.__mode == DataTransferMode.JSON:
                    line = self.__ser.readline().decode('utf-8').strip()
                    self.json_data_received.emit(json.loads(line))
                elif self.__mode == DataTransferMode.BYTES:
                    bytes_data = self.__ser.read(self.__ser.in_waiting)
                    self.bytes_data_received.emit(bytes_data)

    def stop(self):
        self.__running = False
        if self.__ser:
            self.__ser.close()

    def write(self, data: dict):
        if self.__ser and self.__running:
            serialized = json.dumps(data) + '\n'
            self.__ser.write(serialized.encode('utf-8'))
        else:
            raise WriteSerialThreadException(self.__ser, self.__running)
