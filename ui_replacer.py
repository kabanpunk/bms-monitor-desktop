'self.plot_widget = QtWidgets.QWidget -> self.plot_widget = pg.PlotWidget'
'QtWidgets.QTableWidget -> CustomQTableWidget'

'''
from widgets.custom_table_widget import CustomQTableWidget
import pyqtgraph as pg
'''

import os

os.system(r'pyuic5 .\resources\MainWindow.ui -o .\resources\MainWindow_ui.py')

f = open(r'.\resources\MainWindow_ui.py', 'r+', encoding='utf-8')
t = f.read()
t = t.replace('self.plot_widget = QtWidgets.QWidget', 'self.plot_widget = pg.PlotWidget')
t = t.replace('QtWidgets.QTableWidget', 'CustomQTableWidget')

s = '''
from widgets.custom_table_widget import CustomQTableWidget
import pyqtgraph as pg
'''
s += t

f.write(s)
f.close()