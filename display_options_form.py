import glob
import sys

import serial
from PyQt5 import QtWidgets
from PyQt5.QtCore import pyqtSignal

from resources.DisplayOptionsWidget_ui import Ui_Form


class DisplayOptionsForm(QtWidgets.QWidget):
    apply_display_options = pyqtSignal(bool, int)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Загрузка UI страницы.
        self.__ui = Ui_Form()
        self.__ui.setupUi(self)

        self.__ui.pushButton_apply.clicked.connect(self.__apply)
        self.__ui.checkBox.clicked.connect(self.__checkbox_clicked)

    def __checkbox_clicked(self, value):
        if value:
            self.__ui.lineEdit_count.setEnabled(False)
        else:
            self.__ui.lineEdit_count.setEnabled(True)
        print(f'[__checkbox_clicked]: {value}')

    def __apply(self):
        if not self.__ui.lineEdit_count.text():
            count = 0
        else:
            count = int(self.__ui.lineEdit_count.text())
        self.apply_display_options.emit(
            self.__ui.checkBox.isChecked(),
            count
        )
        ...
