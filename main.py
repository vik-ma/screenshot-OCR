import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QLabel, QWidget, QDesktopWidget, QPushButton, QSplashScreen, QRubberBand, QGridLayout, QLineEdit, QPlainTextEdit, QListWidget
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

        self.textbox = QPlainTextEdit(self)
        self.textbox.setFont(QFont("verdana", 15))
        self.textbox.setGeometry(400, 300, 700, 300)
        #self.textbox.setReadOnly(True)

        self.lang_listbox = QListWidget(self)
        self.lang_listbox.setGeometry(150, 200, 240, 110)
        self.lang_listbox.itemClicked.connect(self.lang_listbox_click)

        self.add_lang_listbox = QListWidget(self)
        self.add_lang_listbox.setGeometry(150, 350, 240, 110)


        self.avail_langs = {}           #Dictionary of available languages in Tesseract installation (k = Tesseract langcode, v = Full language name)
        self.avail_langs_swapped = {}   #Dictionary of available languages in Tesseract installation (k = Full language name, v = Tesseract langcode)
        self.avail_langs_index = []     #Indexed list of alphabetically sorted available full language names
        self.load_langs()

        self.selected_lang = self.get_main_lang()
        self.additional_lang_set = set()    #Set to store added language parameters

        self.lang_param_label = QLabel(self)
        self.lang_param_label.setText("Additional languages")
        self.lang_param_label.move(800, 140)
        self.lang_param_label.setFont(QFont("arial", 20, QFont.Bold))
        self.lang_param_label.adjustSize()
        self.lang_param_listbox = QListWidget(self)
        self.lang_param_listbox.setGeometry(800, 180, 240, 110)

        self.lang_label = QLabel(self)
        self.lang_label.move(400,250)
        self.lang_label.setFont(QFont("arial", 20, QFont.Bold))
        self.update_lang()

        self.create_buttons()

    def create_buttons(self):
        self.test_button = QPushButton(self)
        self.test_button.setText("TEST")
        self.test_button.setFont(QFont("arial", 20, QFont.Bold))
        self.test_button.setGeometry(5, 650, 100, 40)
        self.test_button.clicked.connect(self.test)

        self.snippet_all_button = QPushButton("Take Snippet All Monitors", self)
        self.snippet_all_button.setFont(QFont("arial", 35, QFont.Bold))
        self.snippet_all_button.setGeometry(15, 40, 130, 60)
        self.snippet_all_button.adjustSize()
        #self.snippet_all_button.setShortcut("S")
        self.snippet_all_button.clicked.connect(lambda:self.new_snippet("all"))

        self.snippet_primary_button = QPushButton("Take Snippet Primary Monitor", self)
        self.snippet_primary_button.setFont(QFont("arial", 35, QFont.Bold))
        self.snippet_primary_button.setGeometry(15, 120, 130, 60)
        self.snippet_primary_button.adjustSize()
        #self.snippet_primary_button.setShortcut("P")
        self.snippet_primary_button.clicked.connect(lambda:self.new_snippet("primary"))

        self.ocr_button = QPushButton("OCR", self)
        self.ocr_button.setFont(QFont("arial", 35, QFont.Bold))
        self.ocr_button.setGeometry(15, 200, 130, 60)
        self.ocr_button.adjustSize()
        #self.ocr_button.setShortcut("O")
        self.ocr_button.clicked.connect(self.read_image)

        self.clear_button = QPushButton("CLEAR", self)
        self.clear_button.setFont(QFont("arial", 35, QFont.Bold))
        self.clear_button.setGeometry(900, 630, 130, 60)
        self.clear_button.adjustSize()
        self.clear_button.clicked.connect(self.clear_textbox)

        self.copy_button = QPushButton("COPY", self)
        self.copy_button.setFont(QFont("arial", 35, QFont.Bold))
        self.copy_button.setGeometry(400, 630, 130, 60)
        self.copy_button.adjustSize()
        self.copy_button.clicked.connect(self.copy_textbox_contents)

        self.add_lang_button = QPushButton("Add Another Language", self)
        self.add_lang_button.setFont(QFont("Arial", 20, QFont.Bold))
        self.add_lang_button.setGeometry(80, 465, 130, 60)
        self.add_lang_button.adjustSize()
        self.add_lang_button.clicked.connect(self.add_lang_param)

    def load_langs(self):
        languages = ocr.get_languages()
        for lang in languages:
            #Adds the full language name from value in lang_codes_dict if key exists, otherwise adds the langcode's key as value in new dictionary
            self.avail_langs[lang] = lang_codes_dict.setdefault(lang, lang)
            #Adds the full language name to an indexed list
            self.avail_langs_index.append(self.avail_langs[lang])
            #self.lang_listbox.insertItem(index, lang_codes_dict.setdefault(lang, lang)) DELETE IF NOT USED LATER
        #Sorts the language names alphabetically
        self.avail_langs_index.sort(key=str.casefold)
        #Swaps the 'self.avail_langs' values with it's keys
        self.avail_langs_swapped = dict([(value, key) for key, value in self.avail_langs.items()])

        #self.lang_listbox.setSortingEnabled(True) DELETE IF NOT USED LATER
        
        self.lang_listbox.insertItems(0, self.avail_langs_index)
        self.add_lang_listbox.insertItems(0, self.avail_langs_index)
        #Sets the English as default choice for main language
        for index, langs in enumerate(self.avail_langs_index):
            if langs == "English":
                self.lang_listbox.setCurrentRow(index)
                break
        #Sets the first item in list as default choice for additional languages 
        self.add_lang_listbox.setCurrentRow(0)

    def get_main_lang(self):
        return self.lang_listbox.currentItem().text()
    
    def get_additional_lang_index(self):
        return self.add_lang_listbox.currentRow()

    def get_lang_index(self):
        return self.lang_listbox.currentRow()

    def lang_listbox_click(self):
        self.selected_lang = self.get_main_lang()
        self.update_lang()

    def update_lang(self):
        self.lang_label.setText(f"Selected Language: {self.selected_lang}")
        self.lang_label.adjustSize()

    def add_lang_param(self):
        new_lang = self.avail_langs_index[self.get_additional_lang_index()]
        if new_lang != self.get_main_lang():
            self.additional_lang_set.add(new_lang)
            self.lang_param_listbox.clear()
            self.lang_param_listbox.addItems(self.additional_lang_set)



    def read_image(self):
        lang_param = self.avail_langs_swapped[self.get_main_lang()]
        #Checks if there are any added languages
        for lang in self.additional_lang_set:
            #Adds the language(s) to the lang parameter
            lang_param += f"+{self.avail_langs_swapped[lang]}"
        print(self.get_main_lang(), self.additional_lang_set, lang_param)
        img = Image.open("test.png")
        img_text = ocr.image_to_string(img, lang=lang_param).strip()
        self.textbox.setPlainText(img_text)
        
    def new_snippet(self, monitor):
        """
        Create dim Splashscreen object and show dim Splashscreen.

        Also responsible for tracking mouse and capturing screenshot.
        """
        self.snippet = CreateSnippet(monitor, self)
        self.snippet.show()

    def clear_textbox(self):
        self.textbox.clear()

    def copy_textbox_contents(self):
        pass

    def test(self):
        print(self.avail_langs[0])

class CreateSnippet(QSplashScreen):
    """QSplashScreen, that track mouse event for capturing screenshot."""
    def __init__(self, monitor, mainwindow):
        super().__init__()
        self.mainwindow = mainwindow

        self.origin = QPoint(0,0)
        self.end = QPoint(0,0)

        self.rubberband = QRubberBand(QRubberBand.Rectangle, self)
        
        #The leftmost x-value, might be negative
        self.x_min = 0
        #The topmost y-value, might be negative
        self.y_min = 0

        #Variable 'monitor' specifies which screens(s) to draw Splashscreen on
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
        self.mainwindow.hide()
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
        self.mainwindow.hide()
        self.setWindowOpacity(0.4)
    
    def keyPressEvent(self, event):
        """Interrupt snippet function when pressing escape."""
        if event.key() == Qt.Key_Escape:
            self.rubberband.hide()
            self.hide()
            self.mainwindow.show()

    def mousePressEvent(self, event):
        """Show rectangle at mouse position when left-clicked."""
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
            self.mainwindow.show()

#Stores the full language names as values for corresponding language code key
lang_codes_dict = {
    "afr": "Afrikaans",
    "amh": "Amharic",
    "ara": "Arabic",
    "asm": "Assamese",
    "aze": "Azerbaijani",
    "aze_cyrl": "Azerbaijani - Cyrilic",
    "bel": "Belarusian",
    "ben": "Bengali",
    "bod": "Tibetan",
    "bos": "Bosnian",
    "bre": "Breton",
    "bul": "Bulgarian",
    "cat": "Catalan; Valencian",
    "ceb": "Cebuano",
    "ces": "Czech",
    "chi_sim": "Chinese - Simplified",
    "chi_tra": "Chinese - Traditional",
    "chr": "Cherokee",
    "cos": "Corsican",
    "cym": "Welsh",
    "dan": "Danish",
    "dan_frak": "Danish - Fraktur (contrib)",
    "deu": "German",
    "deu_frak": "German - Fraktur (contrib)",
    "dzo": "Dzongkha",
    "ell": "Greek, Modern (1453-)",
    "eng": "English",
    "enm": "English, Middle (1100-1500)",
    "epo": "Esperanto",
    "equ": "Math / equation detection module",
    "est": "Estonian",
    "eus": "Basque",
    "fao": "Faroese",
    "fas": "Persian",
    "fil": "Filipino (old - Tagalog)",
    "fin": "Finnish",
    "fra": "French",
    "frk": "German - Fraktur",
    "frm": "French, Middle (ca.1400-1600)",
    "fry": "Western Frisian",
    "gla": "Scottish Gaelic",
    "gle": "Irish",
    "glg": "Galician",
    "grc": "Greek, Ancient (to 1453) (contrib)",
    "guj": "Gujarati",
    "hat": "Haitian; Haitian Creole",
    "heb": "Hebrew",
    "hin": "Hindi",
    "hrv": "Croatian",
    "hun": "Hungarian",
    "hye": "Armenian",
    "iku": "Inuktitut",
    "ind": "Indonesian",
    "isl": "Icelandic",
    "ita": "Italian",
    "ita_old": "Italian - Old",
    "jav": "Javanese",
    "jpn": "Japanese",
    "kan": "Kannada",
    "kat": "Georgian",
    "kat_old": "Georgian - Old",
    "kaz": "Kazakh",
    "khm": "Central Khmer",
    "kir": "Kirghiz; Kyrgyz",
    "kmr": "Kurmanji (Kurdish - Latin Script)",
    "kor": "Korean",
    "kor_vert": "Korean (vertical)",
    "kur": "Kurdish (Arabic Script)",
    "lao": "Lao",
    "lat": "Latin",
    "lav": "Latvian",
    "lit": "Lithuanian",
    "ltz": "Luxembourgish",
    "mal": "Malayalam",
    "mar": "Marathi",
    "mkd": "Macedonian",
    "mlt": "Maltese",
    "mon": "Mongolian",
    "mri": "Maori",
    "msa": "Malay",
    "mya": "Burmese",
    "nep": "Nepali",
    "nld": "Dutch; Flemish",
    "nor": "Norwegian",
    "oci": "Occitan (post 1500)",
    "ori": "Oriya",
    "osd": "Orientation and script detection module",
    "pan": "Panjabi; Punjabi",
    "pol": "Polish",
    "por": "Portuguese",
    "pus": "Pushto; Pashto",
    "que": "Quechua",
    "ron": "Romanian; Moldavian; Moldovan",
    "rus": "Russian",
    "san": "Sanskrit",
    "sin": "Sinhala; Sinhalese",
    "slk": "Slovak",
    "slk_frak": "Slovak - Fraktur (contrib)",
    "slv": "Slovenian",
    "snd": "Sindhi",
    "spa": "Spanish; Castilian",
    "spa_old": "Spanish; Castilian - Old",
    "sqi": "Albanian",
    "srp": "Serbian",
    "srp_latn": "Serbian - Latin",
    "sun": "Sundanese",
    "swa": "Swahili",
    "swe": "Swedish",
    "syr": "Syriac",
    "tam": "Tamil",
    "tat": "Tatar",
    "tel": "Telugu",
    "tgk": "Tajik",
    "tgl": "Tagalog (new - Filipino)",
    "tha": "Thai",
    "tir": "Tigrinya",
    "ton": "Tonga",
    "tur": "Turkish",
    "uig": "Uighur; Uyghur",
    "ukr": "Ukrainian",
    "urd": "Urdu",
    "uzb": "Uzbek",
    "uzb_cyrl": "Uzbek - Cyrilic",
    "vie": "Vietnamese",
    "yid": "Yiddish",
    "yor": "Yoruba"
}


def main():
    """Main function."""
    app = QApplication([])
    mw = MainWindow()
    mw.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()