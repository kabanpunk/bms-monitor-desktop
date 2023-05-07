from PyQt5 import QtCore, QtGui
from PyQt5.QtCore import QPoint
from PyQt5.QtGui import QColor
from PyQt5.QtWidgets import QTableWidget


class CustomQTableWidget(QTableWidget):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setMouseTracking(True)

    def set_row_color(self, row_index, color):
        for j in range(self.columnCount()):
            self.item(row_index, j).setBackground(color)

    def mouseMoveEvent(self, event):
        if event.buttons() == QtCore.Qt.NoButton:
            row = self.rowAt(event.y())

            for i in range(self.rowCount()):
                self.set_row_color(i, QColor(255, 255, 255, 127))

            if row > 0:
                self.set_row_color(row, QColor(60, 60, 60, 127))
