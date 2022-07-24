import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QLabel, QWidget, QDesktopWidget, QPushButton
from PyQt5.QtGui import QFont


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Screenshot OCR")
        self.setGeometry(0, 0, 700, 400)

        #Display window in the center of the screen
        qtRectangle = self.frameGeometry()
        centerPoint = QDesktopWidget().availableGeometry().center()
        qtRectangle.moveCenter(centerPoint)
        self.move(qtRectangle.topLeft())

        self._centralWidget = QWidget(self)
        self.setCentralWidget(self._centralWidget)

        self.create_buttons()

    def create_buttons(self):
        self.test_button = QPushButton(self)
        self.test_button.setText("TEST")
        self.test_button.setFont(QFont("arial", 20, QFont.Bold))
        self.test_button.setGeometry(5, 350, 100, 40)
        self.test_button.clicked.connect(self.test)

    def test(self):
        pass


def main():
    """Main function."""
    app = QApplication([])
    mw = MainWindow()
    mw.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()