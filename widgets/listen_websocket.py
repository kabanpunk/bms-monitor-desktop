import websocket
from PyQt5 import QtWidgets, QtCore
from PyQt5.QtCore import pyqtSignal


class ListenWebsocket(QtCore.QThread):
    on_message_signal = pyqtSignal(str)


    def __init__(self, url='ws://192.168.4.1/ws', parent=None):
        super(ListenWebsocket, self).__init__(parent)

        if url == '':
            pass
        else:
            websocket.enableTrace(True)
            self.__ws = websocket.WebSocketApp(url,
                                    on_message = self.on_message,
                                    on_error = self.on_error,
                                    on_close = self.on_close)

    def run(self):
        #ws.on_open = on_open

        self.__ws.run_forever()

    def send(self, msg):
        self.__ws.send(msg)


    def on_message(self, ws, message):
        self.on_message_signal.emit(message)
        #print(message)

    def on_error(self, ws, error):
        pass
        #print(error)

    def on_close(self, ws):
        pass
        #print("### closed ###")