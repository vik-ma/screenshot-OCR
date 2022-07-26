import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QLabel, QWidget, QDesktopWidget, QPushButton, QSplashScreen, QRubberBand, QGridLayout, QLineEdit
from PyQt5.QtGui import QFont, QPixmap, QColor, QWindow, QMouseEvent, QGuiApplication
from PyQt5.QtCore import QPoint, Qt, QRect, QSize
from PIL import Image
import pytesseract as ocr

ocr.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Screenshot OCR")
        self.setGeometry(0, 0, 1200, 800)

        #Display window in the center of the screen
        qtRectangle = self.frameGeometry()
        centerPoint = QDesktopWidget().availableGeometry().center()
        qtRectangle.moveCenter(centerPoint)
        self.move(qtRectangle.topLeft())

        self._centralWidget = QWidget(self)
        self.setCentralWidget(self._centralWidget)

        self.textbox = QLineEdit(self)
        self.textbox.move(400,300)
        self.textbox.resize(700,300)

        self.create_buttons()

    def create_buttons(self):
        self.test_button = QPushButton(self)
        self.test_button.setText("TEST")
        self.test_button.setFont(QFont("arial", 20, QFont.Bold))
        self.test_button.setGeometry(5, 350, 100, 40)
        self.test_button.clicked.connect(lambda:self.new_snippet("primary"))

        self.snippet_all_button = QPushButton("Take Snippet All Monitors", self)
        self.snippet_all_button.setFont(QFont("arial", 35, QFont.Bold))
        self.snippet_all_button.setGeometry(15, 40, 130, 60)
        self.snippet_all_button.adjustSize()
        self.snippet_all_button.setShortcut("S")
        self.snippet_all_button.clicked.connect(lambda:self.new_snippet("all"))

        self.snippet_primary_button = QPushButton("Take Snippet Primary Monitor", self)
        self.snippet_primary_button.setFont(QFont("arial", 35, QFont.Bold))
        self.snippet_primary_button.setGeometry(15, 120, 130, 60)
        self.snippet_primary_button.adjustSize()
        self.snippet_primary_button.setShortcut("P")
        self.snippet_primary_button.clicked.connect(lambda:self.new_snippet("primary"))

        self.ocr_button = QPushButton("OCR", self)
        self.ocr_button.setFont(QFont("arial", 35, QFont.Bold))
        self.ocr_button.setGeometry(15, 200, 130, 60)
        self.ocr_button.adjustSize()
        self.ocr_button.setShortcut("O")
        self.ocr_button.clicked.connect(self.read_image)

    def new_snippet(self, monitor):
        """
        Create dim Splashscreen object and show dim Splashscreen.

        Also responsible for tracking mouse and capturing screenshot.
        """
        self.snippet = CreateSnippet(monitor)
        self.snippet.show()

    def read_image(self):
        img = Image.open("test.png")
        img_text = ocr.image_to_string(img)
        print(img_text)
        self.textbox.setText(img_text)

    def test(self):
        pass
class CreateSnippet(QSplashScreen):
    """QSplashScreen, that track mouse event for capturing screenshot."""
    def __init__(self, monitor):
        super().__init__()
        self.origin = QPoint(0,0)
        self.end = QPoint(0,0)

        self.rubberband = QRubberBand(QRubberBand.Rectangle, self)
        
        #The leftmost x-value, might be negative
        self.x_min = 0
        #The topmost y-value, might be negative
        self.y_min = 0

        #'monitor' specifies which screens(s) to draw Splashscreen on
        if monitor == "all":
            self.dim_screen_all()
        elif monitor == "primary":
            self.dim_screen_primary()

    def dim_screen_primary(self):
        """Fill splashScreen with black color and reduce the widget opacity to create dim screen effect on only the primary screen."""
        screen_geometry = QGuiApplication.primaryScreen().geometry()
        screen_pixelmap = QPixmap(screen_geometry.width(), screen_geometry.height())
        screen_pixelmap.fill(QColor(0,0,0))
        self.setPixmap(screen_pixelmap)
        self.setWindowOpacity(0.4)

    def dim_screen_all(self):
        """
        Fill splashScreen with black color and reduce the widget opacity to create dim screen effect on all screens.

        This will not work for very weird multiple-monitor positions or difference in resolutions between monitors.
        """

        screen_geometry = QGuiApplication.primaryScreen().virtualGeometry()     #Get the combined geometry of all monitors
        all_screens = QGuiApplication.screens()

        x_values = []
        y_values = []
        for screen in all_screens:
            #Updates the leftmost and topmost values
            if self.x_min > screen.geometry().left():
                self.x_min = screen.geometry().left()
            if self.y_min > screen.geometry().top():
                self.y_min = screen.geometry().top()

            #Create a list based on maximum coordinates for every monitor
            x_values.append(screen.geometry().right())
            y_values.append(screen.geometry().bottom())
            
            #Delete these later if not used
            #if xmax < screen.geometry().right():
            #    xmax = screen.geometry().right()+1
            #if ymax < screen.geometry().bottom():
            #    ymax = screen.geometry().bottom()+1
        
        width = 0
        height = 0
        if len(all_screens) % 2 == 0:
            #If even number of monitors, multiply width by 1.5 if monitors are stacked horizontally and vice versa
            #Normal width/height doesn't work for even amount of monitors
            if max(x_values)-min(x_values) > max(y_values)-min(y_values):
                #If the disparity between top and bottom x-values are greater than the y-values it means the monitors are stacked horizontally
                width = int(screen_geometry.width()*1.5)
                height = screen_geometry.height()
            else:
                #If the monitors are stacked vertically
                width = screen_geometry.width()
                height = int(screen_geometry.height()*1.5)
        else:
            #If odd number of monitors, proceed as usual
            width = screen_geometry.width()
            height = screen_geometry.height()

        screen_pixelmap = QPixmap(width, height)
        screen_pixelmap.fill(QColor(0,0,0))

        #Always place dim/pixmap in center regardless of monitor position
        avg_x = int(sum(x_values)/len(x_values))
        avg_y = int(sum(y_values)/len(y_values))
        self.move(avg_x, avg_y)

        self.setPixmap(screen_pixelmap)
        
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

            screen = QGuiApplication.primaryScreen()
            #Corrects grabWindow to the right coordinates if x_min or y_min are negative
            selected_pixel_map = screen.grabWindow(0, x_pos+self.x_min, y_pos+self.y_min, width, height)

            selected_pixel_map.save("test.png", "png")



def main():
    """Main function."""
    app = QApplication([])
    mw = MainWindow()
    mw.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()