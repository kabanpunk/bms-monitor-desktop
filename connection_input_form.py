import glob
import sys

import serial
from PyQt5 import QtWidgets
from PyQt5.QtCore import pyqtSignal

from resources.ConnectionInputWidget_ui import Ui_Form


def serial_ports():
    """ Lists serial port names

        :raises EnvironmentError:
            On unsupported or unknown platforms
        :returns:
            A list of the serial ports available on the system
    """
    if sys.platform.startswith('win'):
        ports = ['COM%s' % (i + 1) for i in range(256)]
    elif sys.platform.startswith('linux') or sys.platform.startswith('cygwin'):
        # this excludes your current terminal "/dev/tty"
        ports = glob.glob('/dev/tty[A-Za-z]*')
    elif sys.platform.startswith('darwin'):
        ports = glob.glob('/dev/tty.*')
    else:
        raise EnvironmentError('Unsupported platform')

    result = []
    for port in ports:
        try:
            s = serial.Serial(port)
            s.close()
            result.append(port)
        except (OSError, serial.SerialException):
            pass
    return result


class ConnectionInputForm(QtWidgets.QWidget):
    received_connection_data = pyqtSignal(str, int)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Загрузка UI страницы.
        self.__ui = Ui_Form()
        self.__ui.setupUi(self)

        self.__ui.pushButton_connect.clicked.connect(self.__connect)
        for port in serial_ports():
            self.__ui.comboBox_port.addItem(port)

    def __connect(self):
        self.received_connection_data.emit(
            self.__ui.comboBox_port.currentText(),
            int(self.__ui.comboBox_baudrate.currentText())
        )
        self.close()
