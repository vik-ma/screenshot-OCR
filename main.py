import sys
from PyQt5.QtWidgets import QApplication, QLabel, QWidget, QDesktopWidget

def draw_gui():
    app = QApplication([])
    #Create 700x400 resizable GUI
    window = QWidget()
    window.setWindowTitle("Screenshot OCR")
    window.setGeometry(0, 0, 700, 400)

    #Center the window
    qtRectangle = window.frameGeometry()
    centerPoint = QDesktopWidget().availableGeometry().center()
    qtRectangle.moveCenter(centerPoint)
    window.move(qtRectangle.topLeft())

    test_label = QLabel("<h1>TEST LABEL</h1>", parent=window)
    test_label.move(60, 30)

    window.show()

    sys.exit(app.exec_())

draw_gui()