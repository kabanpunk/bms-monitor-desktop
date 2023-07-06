import pyqtgraph as pg
from pyqtgraph.Qt import QtCore, QtGui


class CustomScatterPlot(pg.ScatterPlotItem):
    sigClicked = QtCore.pyqtSignal(object, object)  # Signal emitted when the item is clicked

    def __init__(self, *args, **kwargs):
        pg.ScatterPlotItem.__init__(self, *args, **kwargs)

    def mouseClickEvent(self, ev):
        if ev.button() == QtCore.Qt.LeftButton:
            self.sigClicked.emit(self, ev)
            ev.accept()
        else:
            ev.ignore()


