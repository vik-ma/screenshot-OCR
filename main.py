import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QLabel, QWidget, QDesktopWidget, QPushButton, QSplashScreen, QRubberBand, QGridLayout, QLineEdit, QPlainTextEdit, QListWidget, QMessageBox, QErrorMessage, QFileDialog, QComboBox, QStatusBar, QCheckBox
from PyQt5.QtGui import QFont, QPixmap, QColor, QWindow, QMouseEvent, QGuiApplication, QClipboard, QImage
from PyQt5.QtCore import QPoint, Qt, QRect, QSize, QBuffer
from PIL import Image
import pytesseract as ocr
from configparser import ConfigParser
import pathlib
import io
from datetime import datetime

DESKTOP = pathlib.Path.home() / 'Desktop'
ocr.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

config = ConfigParser(default_section=None, dict_type=dict, allow_no_value=True)
has_config = pathlib.Path("config.ini").exists()

def write_config():
    """Write changed values to config.ini."""
    with open("config.ini", "w") as configfile:
        config.write(configfile)

def get_time_string():
    date_string = datetime.now().strftime("SSOCR-%Y%m%d-%H%M%S-%f")
    return date_string

if has_config:
    config.read("config.ini")
    ocr.pytesseract.tesseract_cmd = config.get("USERCONFIG", "tesseract_path")
else:
    #Creates default config.ini if it doesn't exist
    config.add_section("DEFAULT")
    config.add_section("USERCONFIG")
    for section in config.sections():
        config.set(section, "tesseract_path", str(ocr.pytesseract.tesseract_cmd))
        config.set(section, "default_lang_main", "English")
        config.set(section, "default_is_combo", str(False))
        config.set(section, "default_lang_combo", "")
        config.set(section, "lastdir", str(DESKTOP))
        config.set(section, "autosavetxt", str(False))
        config.set(section, "autosaveimg", str(False))
        config.set(section, "autocopy", str(False))
        config.set(section, "savetxtpath", "")
        config.set(section, "saveimgpath", "")
    config.add_section("SAVED_LANG_COMBOS")
    write_config()

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
        self.textbox.setReadOnly(True)
        
        self.saved_lang_combos_menu = QComboBox(self)
        self.saved_lang_combos_menu.setGeometry(20, 520, 300, 35)
        self.saved_lang_combos_menu.setFont(QFont("verdana", 15))
        self.saved_lang_combos_menu.activated.connect(self.set_lang_combo)

        self.lang_listbox = QListWidget(self)
        self.lang_listbox.setGeometry(150, 200, 240, 110)
        self.lang_listbox.itemClicked.connect(self.lang_listbox_click)

        self.add_lang_listbox = QListWidget(self)
        self.add_lang_listbox.setGeometry(150, 350, 240, 110)

        self.lang_label = QLabel(self)
        self.lang_label.move(400,250)
        self.lang_label.setFont(QFont("arial", 20, QFont.Bold))

        self.lang_param_listbox = QListWidget(self)
        self.lang_param_listbox.setGeometry(800, 120, 240, 110)

        self.additional_lang_set = set()    #Set to store added language parameters

        self.avail_langs = {}           #Dictionary of available languages in Tesseract installation (k = Tesseract langcode, v = Full language name)
        self.avail_langs_swapped = {}   #Dictionary of available languages in Tesseract installation (k = Full language name, v = Tesseract langcode)
        self.avail_langs_index = []     #Indexed list of alphabetically sorted available full language names
        self.load_lang_combos()
        self.load_langs()

        self.selected_lang = self.get_main_lang()

        self.lang_param_label = QLabel(self)
        self.lang_param_label.setText("Additional languages")
        self.lang_param_label.move(800, 80)
        self.lang_param_label.setFont(QFont("arial", 20, QFont.Bold))
        self.lang_param_label.adjustSize()

        self.update_lang()

        self.create_buttons()
    
        self.auto_save_txt = config.getboolean("USERCONFIG", "autosavetxt")
        self.auto_save_img = config.getboolean("USERCONFIG", "autosaveimg")
        self.auto_copy_output = config.getboolean("USERCONFIG", "autocopy")
        self.create_checkboxes()

    def create_buttons(self):
        self.test_button = QPushButton(self)
        self.test_button.setText("TEST")
        self.test_button.setFont(QFont("arial", 20, QFont.Bold))
        self.test_button.setGeometry(5, 750, 100, 40)
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
        self.ocr_button.clicked.connect(self.ocr_image)

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
        self.add_lang_button.setFont(QFont("arial", 20, QFont.Bold))
        self.add_lang_button.setGeometry(80, 465, 130, 60)
        self.add_lang_button.adjustSize()
        self.add_lang_button.clicked.connect(self.add_lang_param)

        self.remove_add_lang_button = QPushButton("Remove Additional Language", self)
        self.remove_add_lang_button.setFont(QFont("arial", 20, QFont.Bold))
        self.remove_add_lang_button.setGeometry(800, 240, 130, 60)
        self.remove_add_lang_button.adjustSize()
        self.remove_add_lang_button.clicked.connect(self.remove_lang_param)

        self.set_default_lang_button = QPushButton("Set selected language as default", self)
        self.set_default_lang_button.setFont(QFont("arial", 20, QFont.Bold))
        self.set_default_lang_button.setGeometry(600, 10, 130, 60)
        self.set_default_lang_button.adjustSize()
        self.set_default_lang_button.clicked.connect(self.set_default_lang_main)

        self.save_lang_combo_button = QPushButton("Save Language Combo", self)
        self.save_lang_combo_button.setFont(QFont("arial", 20, QFont.Bold))
        self.save_lang_combo_button.setGeometry(20, 560, 130, 60)
        self.save_lang_combo_button.adjustSize()
        self.save_lang_combo_button.clicked.connect(self.save_lang_combo)

        self.remove_lang_combo_button = QPushButton("Remove Language Combo", self)
        self.remove_lang_combo_button.setFont(QFont("arial", 20, QFont.Bold))
        self.remove_lang_combo_button.setGeometry(20, 600, 130, 60)
        self.remove_lang_combo_button.adjustSize()
        self.remove_lang_combo_button.clicked.connect(self.remove_lang_combo)

        self.set_lang_combo_button = QPushButton("Set Language Combo", self)
        self.set_lang_combo_button.setFont(QFont("arial", 20, QFont.Bold))
        self.set_lang_combo_button.setGeometry(20, 640, 130, 60)
        self.set_lang_combo_button.adjustSize()
        self.set_lang_combo_button.clicked.connect(self.set_lang_combo)

        self.save_lang_combo_default_button = QPushButton("Set Language Combo As Default", self)
        self.save_lang_combo_default_button.setFont(QFont("arial", 20, QFont.Bold))
        self.save_lang_combo_default_button.setGeometry(20, 680, 130, 60)
        self.save_lang_combo_default_button.adjustSize()
        self.save_lang_combo_default_button.clicked.connect(self.save_lang_combo_default)

        self.edit_textbox_button = QPushButton("EDIT", self)
        self.edit_textbox_button.setFont(QFont("arial", 35, QFont.Bold))
        self.edit_textbox_button.setGeometry(550, 630, 130, 60)
        self.edit_textbox_button.adjustSize()
        self.edit_textbox_button.clicked.connect(self.set_textbox_readonly)

        self.restore_default_cfg_button = QPushButton("Restore Default Configuration", self)
        self.restore_default_cfg_button.setFont(QFont("arial", 20, QFont.Bold))
        self.restore_default_cfg_button.setGeometry(750, 750, 130, 60)
        self.restore_default_cfg_button.adjustSize()
        self.restore_default_cfg_button.clicked.connect(self.restore_default_config)
        
        self.read_image_file_button = QPushButton("Read Image From File", self)
        self.read_image_file_button.setFont(QFont("arial", 20, QFont.Bold))
        self.read_image_file_button.setGeometry(150, 750, 130, 60)
        self.read_image_file_button.adjustSize()
        self.read_image_file_button.clicked.connect(self.read_image_file)

        self.save_txt_button = QPushButton("Save output to txt file", self)
        self.save_txt_button.setFont(QFont("arial", 20, QFont.Bold))
        self.save_txt_button.setGeometry(750, 700 , 130, 60)
        self.save_txt_button.adjustSize()
        self.save_txt_button.clicked.connect(lambda:self.save_txt_file(self.textbox.toPlainText()))

    def create_checkboxes(self):
        self.save_txt_checkbox = QCheckBox("Save output as .txt", self)
        self.save_txt_checkbox.move(500, 700)
        self.save_txt_checkbox.adjustSize()
        self.save_txt_checkbox.setChecked(self.auto_save_txt)
        self.save_txt_checkbox.stateChanged.connect(self.save_txt_clicked)

        self.save_img_checkbox = QCheckBox("Save snippet as .png", self)
        self.save_img_checkbox.move(500, 720)
        self.save_img_checkbox.adjustSize()
        self.save_img_checkbox.setChecked(self.auto_save_img)
        self.save_img_checkbox.stateChanged.connect(self.save_img_clicked)

        self.auto_copy_checkbox = QCheckBox("Automatically copy output to clipboard", self)
        self.auto_copy_checkbox.move(500, 740)
        self.auto_copy_checkbox.adjustSize()
        self.auto_copy_checkbox.setChecked(self.auto_copy_output)
        self.auto_copy_checkbox.stateChanged.connect(self.auto_copy_clicked)

    def save_txt_clicked(self):
        state = self.save_txt_checkbox.isChecked()
        self.auto_save_txt = state
        config.set("USERCONFIG", "autosavetxt", str(state))
        write_config()

    def save_img_clicked(self):
        state = self.save_img_checkbox.isChecked()
        self.auto_save_img = state
        config.set("USERCONFIG", "autosaveimg", str(state))
        write_config()
    
    def auto_copy_clicked(self):
        state = self.auto_copy_checkbox.isChecked()
        self.auto_copy_output = state
        config.set("USERCONFIG", "autocopy", str(state))
        write_config()

    def load_lang_combos(self):
        for item in config['SAVED_LANG_COMBOS']:
            self.saved_lang_combos_menu.addItem(item)

    def load_langs(self):
        languages = ocr.get_languages()
        for lang in languages:
            #Adds the full language name from value in lang_codes_dict if key exists, otherwise adds the langcode's key as value in new dictionary
            self.avail_langs[lang] = lang_codes_dict.setdefault(lang, lang)
            #Adds the full language name to an indexed list
            self.avail_langs_index.append(self.avail_langs[lang])
        #Sorts the language names alphabetically
        self.avail_langs_index.sort(key=str.casefold)
        #Swaps the 'self.avail_langs' values with it's keys
        self.avail_langs_swapped = dict([(value, key) for key, value in self.avail_langs.items()])
        
        self.lang_listbox.insertItems(0, self.avail_langs_index)
        self.add_lang_listbox.insertItems(0, self.avail_langs_index)

        self.update_all_lang_selection()

    def get_main_lang(self):
        return self.lang_listbox.currentItem().text()
    
    def get_additional_lang_index(self):
        return self.add_lang_listbox.currentRow()

    def get_lang_index(self):
        return self.lang_listbox.currentRow()

    def lang_listbox_click(self):
        self.selected_lang = self.get_main_lang()
        self.update_lang()

    def set_default_lang_main(self):
        config.set("USERCONFIG", "default_lang_main", self.selected_lang)
        config.set("USERCONFIG", "default_is_combo", str(False))
        config.set("USERCONFIG", "default_lang_combo", "")
        write_config()

    def update_lang(self):
        self.lang_label.setText(f"Selected Language: {self.selected_lang}")
        self.lang_label.adjustSize()

    def add_lang_param(self):
        new_lang = self.avail_langs_index[self.get_additional_lang_index()]
        if new_lang != self.get_main_lang():
            #Doesn't add language to parameters if it is already the selected main language
            self.additional_lang_set.add(new_lang)
            self.update_lang_param_listbox()

    def remove_lang_param(self):
        row = self.lang_param_listbox.currentRow()
        if row >= 0:
            #Does nothing if no item in listbox is currently selected
            lang = self.lang_param_listbox.currentItem().text()
            self.additional_lang_set.remove(lang)
            self.update_lang_param_listbox()

    def update_lang_param_listbox(self):
        self.lang_param_listbox.clear()
        self.lang_param_listbox.addItems(self.additional_lang_set)

    def get_lang_combo(self):
        lang_param = self.avail_langs_swapped[self.selected_lang]
        #Checks if there are any added languages
        for lang in self.additional_lang_set:
            #Adds the language(s) to the lang parameter
            lang_param += f"+{self.avail_langs_swapped[lang]}"
        return lang_param
    
    def set_lang_combo(self):
        if len(self.saved_lang_combos_menu) > 0:
            langs = self.saved_lang_combos_menu.currentText().split("+")
            self.selected_lang = self.avail_langs[langs[0]]
            self.additional_lang_set.clear()
            for lang in langs[1::]:
                self.additional_lang_set.add(self.avail_langs[lang])
            self.update_lang()
            self.update_lang_param_listbox()

    def save_lang_combo(self):
        if len(self.additional_lang_set) > 0:
            lang_combo = self.get_lang_combo()
            config.set("SAVED_LANG_COMBOS", lang_combo)
            write_config()
            self.saved_lang_combos_menu.clear()
            self.load_lang_combos()

    def remove_lang_combo(self):
        option = self.saved_lang_combos_menu.currentText()
        config.remove_option("SAVED_LANG_COMBOS", option)
        write_config()
        self.saved_lang_combos_menu.clear()
        self.load_lang_combos()
        if len(self.saved_lang_combos_menu) == 0 and config.getboolean("USERCONFIG", "default_is_combo") is True:
            self.set_default_lang_main()
            self.additional_lang_set.clear()
        self.reset_gui()

    def save_lang_combo_default(self):
        if len(self.additional_lang_set) > 0:
            self.save_lang_combo()
            lang_combo = self.get_lang_combo()
            config.set("USERCONFIG", "default_lang_combo", lang_combo)
            config.set("USERCONFIG", "default_is_combo", str(True))
            write_config()

    def read_image_buffer(self, pixmap):
        screenshot = QImage()
        screenshot = pixmap.toImage()
        buffer = QBuffer()
        buffer.open(QBuffer.ReadWrite)
        screenshot.save(buffer, "PNG")
        newimg = Image.open(io.BytesIO(buffer.data()))
        buffer.close()
        self.ocr_image(newimg)

    def read_image_file(self):
        lastdir = config.get("USERCONFIG", "lastdir")
        file, check = QFileDialog.getOpenFileName(None, "Select File",
                                                  lastdir, "All Files (*)")
        if check:
            get_dir = file.rsplit("/",1)[0]
            config.set("USERCONFIG", "lastdir", get_dir)
            write_config()
            try:
                img = Image.open(file)
                self.ocr_image(img)
            except:
                error_msg = QMessageBox()
                error_msg.setIcon(QMessageBox.Critical)
                error_msg.setText("Error reading file!")
                error_msg.setInformativeText("The selected file is not a valid image file.")
                error_msg.setWindowTitle("Error")
                error_msg.exec_()

    def ocr_image(self, image):
        lang_param = self.get_lang_combo()
        print(lang_param)
        img_text = ocr.image_to_string(image, lang=lang_param).strip()
        self.textbox.setPlainText(img_text)
        if self.auto_copy_output:
            self.copy_textbox_contents()
        if self.auto_save_txt:
            self.save_txt_file(img_text)

    def save_txt_file(self, output):
        date_string = get_time_string()
        if output != "":
            with open(f"{date_string}.txt", "w", encoding="utf-8") as file:
                file.write(output)

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
        if self.textbox.toPlainText() != "":
            clipboard = QApplication.clipboard()
            clipboard.setText(self.textbox.toPlainText())
        
    def set_textbox_readonly(self):
        if self.textbox.isReadOnly() is True:
            self.textbox.setReadOnly(False)
        else:
            self.textbox.setReadOnly(True)

    def update_all_lang_selection(self):
        if config.getboolean("USERCONFIG", "default_is_combo") is False:
            #If user has only set one language as default
            main_lang = config.get("USERCONFIG", "default_lang_main")
        else:
            #If user has set a language combination as default
            lang_combo = config.get("USERCONFIG", "default_lang_combo").split("+")
            main_lang = self.avail_langs[lang_combo[0]]
            self.saved_lang_combos_menu.setCurrentText(config.get("USERCONFIG", "default_lang_combo"))
            self.set_lang_combo()
        #Sets the default language as the current choice for main language
        for index, langs in enumerate(self.avail_langs_index):
            if langs == main_lang:
                self.lang_listbox.setCurrentRow(index)
                break
        #Sets the first item in list as default choice for additional languages 
        self.add_lang_listbox.setCurrentRow(0)

    def reset_gui(self):
        self.additional_lang_set.clear()
        self.update_lang_param_listbox()
        self.update_all_lang_selection()
        self.selected_lang = self.get_main_lang()
        self.update_lang()

    def restore_default_config(self):
        """Overwrite [USERCONFIG] with [DEFAULT] in config.ini if user selects "Yes"."""
        self.confirmbox = QMessageBox().question(self, "Restore Default Configuration", "Are you sure you want to restore default configuration?\nThis can not be undone.", QMessageBox().Yes | QMessageBox().No)
        if self.confirmbox == QMessageBox.Yes:
            default_config = config.items("DEFAULT")
            for k, v in default_config:
                config.set("USERCONFIG", k, v)
            write_config()
            self.reset_gui()


    def test(self):
        print(f"{get_time_string()}.png")





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
            self.mainwindow.read_image_buffer(selected_pixel_map)
            
            if self.mainwindow.auto_save_img:
                date_string = get_time_string()
                selected_pixel_map.save(f"{date_string}.png", "png")

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

class ErrorWindow(QWidget):
    def __init__(self):
        super().__init__()
        #Error message if no installation of Tesseract is found in set path
        self.no_inst_error_msg = QMessageBox().question(self, "TesseractOCR Not Found", "Tesseract installation not found!\n\nManually add path?", QMessageBox().Yes | QMessageBox().No)
        #Error message if file user selected is not a valid tesseract.exe
        self.file_error_msg = QMessageBox()
        self.file_error_msg.setIcon(QMessageBox.Critical)
        self.file_error_msg.setText("Couldn't open Tesseract!")
        self.file_error_msg.setInformativeText("The file you selected was not a TesseractOCR executable file.")
        self.file_error_msg.setWindowTitle("Invalid File")

        if self.no_inst_error_msg == QMessageBox.Yes:
            #Make user set path to tesseract.exe themself
            self.set_tesseract_path()
        else:
            #Close application if user selects no
            sys.exit()

    def set_tesseract_path(self):
        file, check = QFileDialog.getOpenFileName(None, "Select File",
                                                  "C:/", "Executable files (*.exe);;All Files (*)")
        if check:
            ocr.pytesseract.tesseract_cmd = file
            config.set("USERCONFIG", "tesseract_path", file)
            write_config()
            try:
                #If selected file is valid
                mw = MainWindow()
                mw.show()
            except:
                #Display error message and then close  application
                sys.exit(self.file_error_msg.exec_())
        else:
            #Close application if user cancels filedialog
            sys.exit()
        


def main():
    """Main function."""
    app = QApplication([])
    try:
        mw = MainWindow()
        mw.show()
    except:
        ew = ErrorWindow()

    sys.exit(app.exec_())


if __name__ == "__main__":
    main()