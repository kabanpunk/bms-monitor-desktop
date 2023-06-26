import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QTextEdit
from PyQt5.QtCore import QThread, pyqtSignal
import serial


class SerialThread(QThread):
    data_received = pyqtSignal(bytes)

    def __init__(self, serial_port=None, baud_rate=None):
        super().__init__()
        self.serial_port = serial_port
        self.baud_rate = baud_rate
        self.running = False
        self.ser = None

    def run(self):
        self.running = True
        self.ser = serial.Serial(self.serial_port, self.baud_rate, timeout=1)
        while self.running:
            if self.ser.in_waiting:
                data = self.ser.read(self.ser.in_waiting)
                self.data_received.emit(data)

    def stop(self):
        self.running = False
        if self.ser:
            self.ser.close()

    def write(self, data):
        if self.ser and self.running:
            self.ser.write(data)