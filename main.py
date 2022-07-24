import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QLabel, QWidget, QDesktopWidget, QPushButton, QSplashScreen, QRubberBand
from PyQt5.QtGui import QFont, QPixmap, QColor, QWindow, QMouseEvent, QGuiApplication
from PyQt5.QtCore import QPoint, Qt, QRect, QSize


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

        self.snippet = CreateSnippet()
    
    def new_snippet(self):
        self.snippet.show()

    def create_buttons(self):
        self.test_button = QPushButton(self)
        self.test_button.setText("TEST")
        self.test_button.setFont(QFont("arial", 20, QFont.Bold))
        self.test_button.setGeometry(5, 350, 100, 40)
        self.test_button.clicked.connect(self.new_snippet)

    def test(self):
        pass
class CreateSnippet(QSplashScreen):
    def __init__(self):
        super().__init__()

        self.origin = QPoint(0,0)
        self.end = QPoint(0,0)

        self.rubberband = QRubberBand(QRubberBand.Rectangle, self)

        self.dim_screen()

    def dim_screen(self):
        #Only primary screen
        screen_geometry = QGuiApplication.primaryScreen().geometry()

        screen_pixelmap = QPixmap(screen_geometry.width(), screen_geometry.height())
        screen_pixelmap.fill(QColor(0,0,0))

        self.setPixmap(screen_pixelmap)
        
        self.setWindowState(Qt.WindowState.WindowFullScreen)
        self.setWindowOpacity(0.4)
        
    def mousePressEvent(self, event):
        """Show rectangle at mouse position when left-clicked"""
        if event.button() == Qt.LeftButton:
            self.origin = event.pos()

            self.rubberband.setGeometry(QRect(self.origin, QSize()))
            self.rubberband.show()

    def mouseMoveEvent(self, event):
        """Resize rectangle as we move mouse, after left-clicked."""
        self.rubberband.setGeometry(QRect(self.origin, event.pos()).normalized())

    def mouseReleaseEvent(self, event):
        """Upon mouse released, ask the main desktop's QScreen to capture screen on defined area."""
        if event.button() == Qt.LeftButton:
            self.end = event.pos()

            self.rubberband.hide()
            self.hide()

            x_pos = 0
            y_pos = 0
            width = 0
            height = 0
            #Creates proper coordinates even if mouse traveled right to left or bottom to top
            if self.end.x() - self.origin.x() > 0:
                x_pos = self.origin.x()
                width = self.end.x() - self.origin.x()
            else:
                x_pos = self.end.x()
                width = self.origin.x() - self.end.x()

            if self.end.y() - self.origin.y() > 0:
                y_pos = self.origin.y()
                height = self.end.y() - self.origin.y()
            else:
                y_pos = self.end.y()
                height = self.origin.y() - self.end.y()

            #Only primary screen
            screen = QGuiApplication.primaryScreen()
            selected_pixel_map = screen.grabWindow(0, x_pos, y_pos, width, height)
            selected_pixel_map.save("test.png", "png")



def main():
    """Main function."""
    app = QApplication([])
    mw = MainWindow()
    mw.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()