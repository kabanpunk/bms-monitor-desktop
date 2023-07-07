import json
import sys
from dataclasses import dataclass
from enum import Enum
from datetime import datetime
from PyQt5.QtWidgets import QApplication, QMainWindow, QTextEdit, QMessageBox
from PyQt5.QtCore import QThread, pyqtSignal, QWaitCondition
import serial

import serial
from typing import Union

from byte_operations import two_ints_into16


class DataTransferMode(Enum):
    JSON = 1
    BYTES = 2


class WriteSerialThreadException(Exception):
    """
    Exception raised for errors that occur during writing data to Serial.

    Attributes:
        ser (Union[serial.Serial, None]): The Serial object being used for communication.
    """

    def __init__(self, ser: serial.Serial | None):
        super().__init__()
        self.ser = ser

    def __str__(self) -> str:
        if not isinstance(self.ser, serial.Serial):
            return "Invalid Serial object provided."

        error_message = "Error writing data to Serial. "
        if self.ser.is_open:
            error_message += "Serial port is open."
        else:
            error_message += "Serial port is closed."
        return error_message


def auto_flush(func):
    def wrapper(self):
        func(self)
        QThread.msleep(100)
        self.ser.read(self.ser.in_waiting)

    return wrapper


@dataclass
class DataFrame:
    voltages: list[float]
    whs: list[float]
    sums_whs: list[float]
    amperage: float
    time: datetime


class SerialThread(QThread):
    data_received = pyqtSignal(DataFrame)
    end_cycle = pyqtSignal()

    def __init__(self, serial_port=None, baud_rate=None):
        super().__init__()
        self.__serial_port = serial_port
        self.__baud_rate = baud_rate
        self.__running = False
        self.__pause = False
        self.ser = serial.Serial()
        self.__last_dataframe_time: datetime = datetime.now()
        self.__whs = [0] * 16
        self.__is_end_cells = [0] * 16
        self.__threshold = 0
        self.__is_end_cycle = False
        self.__sums_whs = [0] * 16

    def set_threshold(self, value: float):
        self.__threshold = value

    def complete_cycle(self):
        self.__is_end_cycle = True

    def run(self):
        self.__running = True
        self.__is_end_cycle = False
        self.__last_dataframe_time: datetime = datetime.now()
        while self.__running:
            if not self.__pause:
                self.write(bytes(
                    [0x7e, 0xa1, 0x01, 0x00, 0x00, 0xbe, 0x18, 0x55, 0xaa, 0x55]
                ))

                QThread.msleep(100)
                bytes_data = self.ser.read(self.ser.in_waiting)

                if len(bytes_data) != 152:
                    continue

                time_now = datetime.now()
                hex_data = ' '.join(f'0x{b:02x}' for b in bytes_data)
                amperage = two_ints_into16(bytes_data[77], bytes_data[76]) / 10.
                dt = time_now - self.__last_dataframe_time
                voltages = []
                whs = []
                for i in range(34, 66, 2):
                    idx = (i - 34) // 2
                    cell_voltage = two_ints_into16(bytes_data[i + 1], bytes_data[i]) / 1000

                    if cell_voltage < self.__threshold and not self.__is_end_cells[idx]:
                        print(cell_voltage)
                        self.__is_end_cells[idx] = True
                        QThread.msleep(500)
                        self.command_auth()
                        QThread.msleep(500)
                        self.command_discharge_off()

                        if not self.__is_end_cycle:
                            self.__is_end_cycle = True
                            self.end_cycle.emit()
                    wh = (amperage * cell_voltage * dt.total_seconds()) / 3600.
                    voltages.append(cell_voltage)
                    whs.append(wh)

                    if not self.__is_end_cells[idx]:
                        self.__whs[idx] = whs[idx]
                        self.__sums_whs[idx] += whs[idx]

                data_frame = DataFrame(
                    voltages=voltages,
                    whs=whs,
                    sums_whs=self.__sums_whs,
                    amperage=amperage,
                    time=time_now
                )
                self.__last_dataframe_time = time_now
                self.data_received.emit(data_frame)
                QThread.msleep(1000)
            else:
                QThread.msleep(100)
                continue

    def stop(self):
        self.__running = False
        if self.ser:
            self.ser.close()

    def write(self, data: bytes):
        if self.ser:
            self.ser.write(data)
        else:
            raise WriteSerialThreadException(self.ser)

    def connect(self):
        self.ser = serial.Serial(self.__serial_port, self.__baud_rate, timeout=1)

    @auto_flush
    def command_auth(self):
        self.write(bytes(
            [0x7e, 0xa1, 0x23, 0x6a, 0x01, 0x0c, 0x31, 0x32, 0x33, 0x34, 0x35, 0x36, 0x37, 0x38, 0x39, 0x61, 0x62, 0x63,
             0x20, 0x62, 0xaa, 0x55]
        ))

    @auto_flush
    def command_discharge_on(self):
        self.write(bytes(
            [0x7e, 0xa1, 0x51, 0x03, 0x00, 0x00, 0x79, 0x25, 0xaa, 0x55]
        ))

    @auto_flush
    def command_discharge_off(self):
        self.write(bytes(
            [0x7e, 0xa1, 0x51, 0x01, 0x00, 0x00, 0xd8, 0xe5, 0xaa, 0x55]
        ))

    def pause(self):
        self.__pause = True
        if self.ser.in_waiting:
            print(f'try pause, but in waiting... [{self.ser.in_waiting}]')
            bytes_data = self.ser.read(self.ser.in_waiting)
            hex_data = ' '.join(f'0x{b:02x}' for b in bytes_data)
            print('[read/flush]:', hex_data)
        self.ser.flush()

    def resume(self):
        self.__pause = False
        QThread.msleep(100)
