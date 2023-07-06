import time

import jsons
import requests as requests
from PyQt5 import QtWidgets, QtCore
from PyQt5.QtWidgets import QApplication, QWidget, QTableWidget, QTableWidgetItem, QVBoxLayout, QFileDialog, \
    QProgressBar, QMessageBox, QGraphicsDropShadowEffect
import sys, json
import datetime

from pyqtgraph import mkPen, DateAxisItem, LegendItem, PlotDataItem
from pyqtgraph.graphicsItems.ScatterPlotItem import Symbols

from connection_input_form import ConnectionInputForm
from display_options_form import DisplayOptionsForm
from progress_bar_dialog import ProgressDialog
from qt_graph.custom_scatter_plot import CustomScatterPlot
from resources.MainWindow_ui import Ui_MainWindow
from random import randint
import pyqtgraph as pg

from serial_thread import SerialThread, DataFrame

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


def timestamp(dt: datetime):
    return int(time.mktime(dt.timetuple()))


class TimeAxisItem(pg.AxisItem):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.enableAutoSIPrefix(False)

    def tickStrings(self, values, scale, spacing):
        try:
            return [datetime.datetime.fromtimestamp(value).strftime("%H:%M:%S") for value in values]
        except:
            return [""]


class MainWindow(QtWidgets.QMainWindow):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Загрузка UI страницы.
        self.__ui = Ui_MainWindow()
        self.__ui.setupUi(self)

        # creating a QGraphicsDropShadowEffect object
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(15)

        # Создаем GraphicsLayoutWidget
        # Создаем и добавляем LabelItem
        self.__wh_label = pg.LabelItem(justify='right')
        self.__wh_label_style_promt = "<span style='font-size: 12pt; color: #A9B7C6;'>WH: {}</span>"
        self.__wh_label.setText(self.__wh_label_style_promt.format(''))
        self.__ui.win_plot_widget.addItem(self.__wh_label)
        # Создаем и добавляем PlotWidget
        self.__plot_widget = self.__ui.win_plot_widget.addPlot(row=1, col=0)
        self.__plot_widget.setAxisItems({'bottom': TimeAxisItem(orientation='bottom')})
        self.__plot_widget.setLabel('bottom', "Время")
        self.__plot_widget.setLabel('left', "Напряжение")
        self.__plot_widget.showGrid(x=True, y=True, alpha=1)

        self.__ui.win_plot_widget.setBackground("#2b2b2b")

        self.__x_range = 0

        self.__scatter = CustomScatterPlot(
        )
        self.__plot = PlotDataItem()
        self.__plot_widget.addItem(self.__plot)
        self.__plot_widget.addItem(self.__scatter)

        self.__local_filename = 'data.bdt'

        self.__is_connected = False

        self.__is_end_of_cycle = False

        # self.setWindowTitle("PyQt5 QTableView")
        # self.setGeometry(500, 400, 500, 300)
        self.setup_cells_table()

        self.__ui.action_3.triggered.connect(self.__action_import)
        self.__ui.action_4.triggered.connect(self.__connect)
        self.__ui.action_5.triggered.connect(self.__erase_sd)
        self.__ui.pushButton.clicked.connect(self.__start_cycle)
        self.__ui.action_6.triggered.connect(self.__display_options)

        self.__serial_thread: SerialThread = SerialThread()

        self.__data = {
        }
        self.show()

    def __display_options(self):
        self.__display_options_form = DisplayOptionsForm()
        self.__display_options_form.apply_display_options.connect(self.__apply_display_options)
        self.__display_options_form.show()

    def __apply_display_options(self, check, count):
        if check:
            self.__x_range = 0
        else:
            self.__x_range = count

    def __append_data_frame_to_cache(self, data_frame: DataFrame):
        for cell_num in range(1, 17):
            cell_voltage = data_frame.voltages[cell_num - 1]
            cell_wh = data_frame.whs[cell_num - 1]

            if cell_num in self.__data:
                self.__data[cell_num][0].append(timestamp(data_frame.time))
                self.__data[cell_num][1].append(cell_voltage)
                self.__data[cell_num][2].append(cell_wh)
                n = len(self.__data[cell_num][0])

                if 0 < self.__x_range < n:
                    self.__data[cell_num] = (
                        self.__data[cell_num][0][-self.__x_range:],
                        self.__data[cell_num][1][-self.__x_range:],
                        self.__data[cell_num][2][-self.__x_range:]
                    )
            else:
                self.__data[cell_num] = (
                    [timestamp(data_frame.time)],
                    [cell_voltage],
                    [cell_wh]
                )

    def __point_clicked(self, plot, ev):
        # This function is called when a point is clicked

        # We can use .pointsAt to get a list of all points under the cursor:
        points = self.__scatter.pointsAt(ev.pos())
        if len(points) > 0:
            point = points[0]
            print(point)
            self.__wh_label.setText(self.__wh_label_style_promt.format(point.data()))

    def __add_scatter_plot(self, row):
        self.__plot_widget.removeItem(self.__plot)
        self.__plot_widget.removeItem(self.__scatter)

        self.__scatter = CustomScatterPlot(
            hoverable=True,
            hoverPen=pg.mkPen('w'),
            hoverSize=20,
            size=15,
            brush=pg.mkBrush(118, 255, 164, 255)
        )
        self.__scatter.setData([
            {
                'pos': [x, y],
                'data': d
            }
            for x, y, d in zip(self.__data[row][0], self.__data[row][1], self.__data[row][2])
        ])
        self.__plot = PlotDataItem(self.__data[row][0], self.__data[row][1])
        self.__plot_widget.addItem(self.__plot)
        self.__plot_widget.addItem(self.__scatter)
        self.__scatter.sigClicked.connect(self.__point_clicked)

    def __handle_data_received(self, data_frame: DataFrame):
        if not self.__local_filename:
            return
        if not self.__is_end_of_cycle:
            json_str = jsons.dumps(data_frame)
            with open(self.__local_filename, 'a') as file:
                file.write(json_str + '\n')
        self.__append_data_frame_to_cache(data_frame)

        # self.__ui.plot_widget.clear()
        row = self.__ui.tableWidget.currentRow()
        row = 1 if row < 1 else row
        self.__add_scatter_plot(row)
        self.__update_table(data_frame)

    def __closeEvent(self, event):
        self.__serial_thread.stop()
        self.__serial_thread.wait()

    def __start_cycle(self):
        self.__is_end_of_cycle = False
        file_names = QFileDialog.getSaveFileName(self, 'Save file', './')

        if file_names[0]:
            self.__local_filename = file_names[0]
        else:
            raise FileNotFoundError()

        threshold = float(self.__ui.lineEdit_3.text())
        self.__serial_thread.set_threshold(threshold)

        self.__serial_thread.pause()
        self.__serial_thread.command_auth()
        self.__serial_thread.command_discharge_on()
        self.__serial_thread.resume()

    def __erase_sd(self):
        print('erasing sd card...')
        ...

    def __connect(self):
        self.__connection_input_form = ConnectionInputForm()
        self.__connection_input_form.received_connection_data.connect(self.__received_connection_data)
        self.__connection_input_form.show()

    def __received_connection_data(self, port, baud_rate):
        self.__serial_thread = SerialThread(port, baud_rate)
        self.__serial_thread.data_received.connect(self.__handle_data_received)
        self.__serial_thread.end_cycle.connect(self.__end_of_cycle)
        self.__serial_thread.connect()
        self.__serial_thread.command_auth()
        self.__serial_thread.start()

    def __end_of_cycle(self):
        QMessageBox.information(None, 'Оповещение', f'Конец цикла')

    def __update_table(self, data_frame: DataFrame):
        self.__ui.label_time_out.setText(data_frame.time.strftime('%H:%M:%S'))
        self.__ui.label_amperage_out.setText(str(round(data_frame.amperage, 3)))
        for i in range(16):
            self.__ui.tableWidget.setItem(i + 1, 0, QTableWidgetItem(str(i + 1)))
            self.__ui.tableWidget.setItem(i + 1, 1, QTableWidgetItem(str(round(data_frame.voltages[i], 3))))
            self.__ui.tableWidget.setItem(i + 1, 2, QTableWidgetItem(str(round(data_frame.whs[i], 3))))

    def __action_import(self):
        self.__data = {}

        file_name = QFileDialog.getOpenFileName(self, 'Open file',
                                                'c:\\', "BMS data files (*.bdt)")
        print(file_name[0])

        with open(file_name[0]) as f:
            while True:
                line = f.readline()

                if not line:
                    break

                data_frame = jsons.loads(line, DataFrame)
                self.__append_data_frame_to_cache(data_frame)

    def table_clicked(self, item):
        row = item.row()
        # self.__ui.plot_widget.clear()
        self.__ui.tableWidget.selectRow(row)
        self.__add_scatter_plot(row)

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
