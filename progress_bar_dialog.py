from PyQt5.QtCore import Qt, QThread, pyqtSignal
from PyQt5.QtWidgets import QApplication, QDialog, QProgressBar, QVBoxLayout, QPushButton, QLabel


class ProgressDialog(QDialog):
    def __init__(self):
        super().__init__()

        self.setWindowTitle('Прогресс')
        self.setFixedSize(300, 100)

        self.completed = False

        self.label = QLabel()
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setAlignment(Qt.AlignCenter)

        layout = QVBoxLayout()
        layout.addWidget(self.label)
        layout.addWidget(self.progress_bar)

        self.setStyleSheet("""
            QDialog {
                background-color: #2b2b2b;
            }

            QLabel {
                color: #a9b7c6;
                font-size: 16px;
                padding: 5px;
            }

            QProgressBar {
                border: 2px solid grey;
                border-radius: 5px;
                text-align: center;
            }

            QProgressBar::chunk {
                background-color: #6897bb;
            }
        """)

        self.setLayout(layout)

    def update_progress(self, value):
        self.progress_bar.setValue(value)
        if value == 100:
            self.label.setText("Загрузка завершена")
            self.completed = True

    def closeEvent(self, event):
        if not self.completed:
            print("Загрузка еще не завершена")
        event.accept()