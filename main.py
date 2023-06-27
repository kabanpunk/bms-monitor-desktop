import requests as requests
from PyQt5 import QtWidgets, QtCore
from PyQt5.QtWidgets import QApplication, QWidget, QTableWidget, QTableWidgetItem, QVBoxLayout, QFileDialog, \
    QProgressBar
import sys, json
import datetime

from pyqtgraph import mkPen
from pyqtgraph.graphicsItems.ScatterPlotItem import Symbols

from connection_input_form import ConnectionInputForm
from progress_bar_dialog import ProgressDialog
from resources.MainWindow_ui import Ui_MainWindow
from random import randint
import pyqtgraph as pg

from serial_thread import SerialThread

from byte_operations import int16_into_two_ints, two_ints_into16

from enum import Enum


class PackageCodes(Enum):
    SETTING_THRESHOLD = 10
    ERASE_FILE = 11
    INIT_DOWNLOAD = 12
    LOGGING = 13
    ERROR = 14
    REQUEST_DATA = 15
    DATA = 16
    FILE_SECTION = 17
    END_DOWNLOAD = 18
    START_DOWNLOAD = 19
    FILE_SIZE = 20
    TEST = 21


class MainWindow(QtWidgets.QMainWindow):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Загрузка UI страницы.
        self.__ui = Ui_MainWindow()
        self.__ui.setupUi(self)

        self.__local_filename = 'data.bdt'
        self.__file_size = 0
        self.__already_downloaded = 0
        self.__buffer: bytes = b''

        self.__is_connected = False

        # self.setWindowTitle("PyQt5 QTableView")
        # self.setGeometry(500, 400, 500, 300)
        self.setup_cells_table()

        self.__ui.action_3.triggered.connect(self.__action_import)
        self.__ui.action_4.triggered.connect(self.__connect)
        self.__ui.action_5.triggered.connect(self.__erase_sd)
        self.__ui.action_2.triggered.connect(self.__test)
        self.__ui.action.triggered.connect(self.__download)
        self.__ui.pushButton.clicked.connect(self.__start_cycle)

        self.__serial_thread: SerialThread = SerialThread()

        self.data = {}
        self.show()
    def __test(self):
        self.__serial_thread.write({
            "code": PackageCodes.TEST.value
        })
    def __handle_json_data_received(self, data: dict):
        print('Received form serial:', data, type(data))
        if data["code"] == PackageCodes.DATA.value:
            self.__update_table(data)
        elif data["code"] == PackageCodes.START_DOWNLOAD.value:
            self.__serial_thread.set_mode_to_bytes()
        elif data["code"] == PackageCodes.FILE_SIZE.value:
            print('WTF', data)
            self.__file_size = data["file_size"]

    def __handle_bytes_data_received(self, data: bytes):
        # TODO: Сепарировать логику загрузки
        self.__already_downloaded += len(data)
        self.progress_dialog.update_progress(round((self.__already_downloaded - 1) / self.__file_size * 100))
        self.__buffer += data
        if data[-1] == 0xa0:
            print('STOPED')
            self.__serial_thread.set_mode_to_json()
            with open(self.__local_filename, 'wb') as file:
                file.write(self.__buffer[:-1])
            self.__buffer = b''
            self.__already_downloaded = 0
            self.__file_size = 0


    def __closeEvent(self, event):
        self.__serial_thread.stop()
        self.__serial_thread.wait()

    def __start_cycle(self):
        threshold = float(self.__ui.lineEdit_3.text())
        self.__serial_thread.write({
            "code": PackageCodes.SETTING_THRESHOLD.value,
            "threshold": threshold
        })

    def __erase_sd(self):
        print('erasing sd card...')
        self.__serial_thread.write({
            "code": PackageCodes.ERASE_FILE.value
        })

    def __connect(self):
        self.__connection_input_form = ConnectionInputForm()
        self.__connection_input_form.received_connection_data.connect(self.__received_connection_data)
        self.__connection_input_form.show()

    def __received_connection_data(self, port, baud_rate):
        self.__serial_thread = SerialThread(port, baud_rate)
        self.__serial_thread.json_data_received.connect(self.__handle_json_data_received)
        self.__serial_thread.bytes_data_received.connect(self.__handle_bytes_data_received)
        self.__serial_thread.start()

    def __update_table(self, data: dict):
        amperage = float(data['amperage'])
        current_time = float(data['current_time'])
        self.__ui.label_time_out.setText(str(round(current_time, 3)))
        self.__ui.label_amperage_out.setText(str(round(amperage, 3)))
        for i in range(1, 17):
            self.__ui.tableWidget.setItem(i, 0, QTableWidgetItem(str(i)))
            self.__ui.tableWidget.setItem(i, 1, QTableWidgetItem(str(round(data['voltages'][i - 1], 3))))
            self.__ui.tableWidget.setItem(i, 2, QTableWidgetItem(str(round(data['whs'][i - 1], 3))))

    def __download(self):
        self.__serial_thread.write({
            "code": PackageCodes.INIT_DOWNLOAD.value
        })

        self.progress_dialog = ProgressDialog()
        self.progress_dialog.show()

    def __action_import(self):
        self.data = {}

        file_name = QFileDialog.getOpenFileName(self, 'Open file',
                                                'c:\\', "BMS data files (*.bdt)")
        print(file_name[0])
        with open(file_name[0]) as f:
            while True:
                line = f.readline()

                if not line:
                    break

                line_data = line.split(';')
                current_time = float(line_data[0])
                amperage = float(line_data[1])

                for cell_num in range(1, 17):
                    cell_voltage = float(float(line_data[cell_num + 1]))

                    if cell_num in self.data:
                        self.data[cell_num][0].append(current_time)
                        self.data[cell_num][1].append(cell_voltage)
                    else:
                        self.data[cell_num] = ([current_time], [cell_voltage])

    def table_clicked(self, item):
        self.__ui.plot_widget.clear()
        self.__ui.tableWidget.selectRow(item.row())
        self.__ui.plot_widget.plot(self.data[item.row()][0], self.data[item.row()][1])

        print("You clicked on {0}x{1}".format(item.column(), item.row()))

    def setup_cells_table(self):
        self.__ui.tableWidget.clicked.connect(self.table_clicked)

        self.__ui.tableWidget.setRowCount(17)
        self.__ui.tableWidget.setColumnCount(3)

        self.__ui.tableWidget.setItem(0, 0, QTableWidgetItem("#"))
        self.__ui.tableWidget.setItem(0, 1, QTableWidgetItem("Напряжение"))
        self.__ui.tableWidget.setItem(0, 2, QTableWidgetItem("Ватт-часы"))
        self.__ui.tableWidget.setColumnWidth(0, 37)

        for i in range(1, 17):
            self.__ui.tableWidget.setItem(i, 0, QTableWidgetItem(str(i)))
            self.__ui.tableWidget.setItem(i, 1, QTableWidgetItem('-'))
            self.__ui.tableWidget.setItem(i, 2, QTableWidgetItem('-'))


def main():
    app = QtWidgets.QApplication(sys.argv)
    main_window = MainWindow()
    main_window.show()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
