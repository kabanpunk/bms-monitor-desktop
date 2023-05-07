import requests as requests
from PyQt5 import QtWidgets, QtCore
from PyQt5.QtWidgets import QApplication, QWidget, QTableWidget, QTableWidgetItem, QVBoxLayout, QFileDialog
import sys, requests, json
import datetime


from pyqtgraph import mkPen
from pyqtgraph.graphicsItems.ScatterPlotItem import Symbols

from qt_graph.BoundTargetItem import BoundTargetItem
from resources.MainWindow_ui import Ui_MainWindow
from random import randint
import pyqtgraph as pg

from widgets.listen_websocket import ListenWebsocket


class MainWindow(QtWidgets.QMainWindow):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Загрузка UI страницы.
        self.__ui = Ui_MainWindow()
        self.__ui.setupUi(self)

        self.__thread = ListenWebsocket(url='')
        self.__is_connected = False

        # self.setWindowTitle("PyQt5 QTableView")
        # self.setGeometry(500, 400, 500, 300)
        self.setup_cells_table()
        self.setup_main_table()

        self.__ui.action_3.triggered.connect(self.__action_import)
        self.__ui.action_4.triggered.connect(self.__connect)
        self.__ui.action_5.triggered.connect(self.__erase_sd)
        self.__ui.action.triggered.connect(self.__download)

        self.data = {}

        self.show()

    def __erase_sd(self):
        print('erasing sd card...')
        print(requests.get('http://192.168.4.1/del'))

    def __connect(self):
        def url_checker(url):
            try:
                # Get Url
                get = requests.get(url)
                # if the request succeeds
                if get.status_code == 200:
                    print (f"{url}: is reachable")
                    return True
                else:
                    print (f"{url}: is Not reachable, status_code: {get.status_code}")
                    return False

            # Exception
            except requests.exceptions.RequestException as e:
                # print URL with Errs
                print (f"{url}: is Not reachable \nErr: {e}")
                return False

        if url_checker('http://192.168.4.1/'):
            self.__thread = ListenWebsocket(url='ws://192.168.4.1/ws')
            self.__thread.on_message_signal.connect(self.__on_message)
            self.__thread.start()

    def __on_message(self, message):
        message_json = json.loads(message)
        amperage = float(message_json['amperage'])
        current_time = float(message_json['current_time'])
        self.__ui.tableWidget_2.setItem(1, 0, QTableWidgetItem(str(datetime.timedelta(hours=current_time))))
        self.__ui.tableWidget_2.setItem(1, 1, QTableWidgetItem(str(round(amperage, 3))))
        for i in range(1, 17):
            self.__ui.tableWidget.setItem(i, 0, QTableWidgetItem(str(i)))
            self.__ui.tableWidget.setItem(i, 1, QTableWidgetItem(str( round(message_json['voltages'][i-1], 3) )))
            self.__ui.tableWidget.setItem(i, 2, QTableWidgetItem(str( round(message_json['whs'][i-1], 3) )))
        print(f'[main]: {message_json}')

    def __download(self):


        local_filename = 'data.bdt'
        url = 'http://192.168.4.1/download'

        with requests.get(url, stream=True) as r:
            print(r)
            print("START DOWNLAOD")
            with open(local_filename, 'wb') as file:
                # Get the total size, in bytes, from the response header
                total_size = int(r.headers.get('Content-Length'))
                print('total_size: ', total_size)
                # Define the size of the chunk to iterate over (Mb)
                chunk_size = 4096
                dl = 0
                # iterate over every chunk and calculate % of total
                for i, chunk in enumerate(r.iter_content(chunk_size=chunk_size)):
                    dl += len(chunk)
                    file.write(chunk)
                    # calculate current percentage
                    c = 100 * dl / total_size
                    # write current % to console, pause for .1ms, then flush console
                    print(f"\r{round(c, 4)}%")
        #print('DOWNLOAD ACTION')

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

    def __create_point(
            self,
            curve: pg.PlotDataItem,
            pos=None,
    ) -> BoundTargetItem:
        curves = [p.curve for p in self.__points] + [curve]
        if len(curves) != len(set(curves)):
            print('fuck')
            return BoundTargetItem(curve)

        # TODO: цвета, символы и прочее должны быть вынесены в конфиг файлы
        point = BoundTargetItem(
            curve, pos,
            size=20,
            symbol=Symbols[self.__options_widget.point_symbol],
            pen=self.__options_widget.point_color,
            label=lambda _, y: f"{y:.4f}",
            labelOpts={
                "offset": QtCore.QPointF(0, -20),
                "color": "#004DFF"
            }
        )
        point.update_pos()

        if self.__options_widget.ox_fixation:
            point.fix_on_ox()
        else:
            point.free_movement_on_ox()

        self.__points.append(point)
        return point

    def setup_main_table(self):
        self.__ui.tableWidget_2.setRowCount(2)
        self.__ui.tableWidget_2.setColumnCount(2)

        self.__ui.tableWidget_2.setItem(0, 0, QTableWidgetItem("Время"))
        self.__ui.tableWidget_2.setItem(0, 1, QTableWidgetItem("Ток"))
        self.__ui.tableWidget_2.setColumnWidth(0, 154)

        self.__ui.tableWidget_2.setItem(1, 0, QTableWidgetItem('-'))
        self.__ui.tableWidget_2.setItem(1, 1, QTableWidgetItem('-'))


def main():
    app = QtWidgets.QApplication(sys.argv)
    main_window = MainWindow()
    main_window.show()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
