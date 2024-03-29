import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QLabel, QWidget, QDesktopWidget, QPushButton, QSplashScreen, QRubberBand, QPlainTextEdit, QListWidget, QMessageBox, QFileDialog, QComboBox, QCheckBox
from PyQt5.QtGui import QFont, QPixmap, QColor, QGuiApplication, QImage, QIcon, QCursor
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

def get_time_string() -> str:
    """Generate a string based on current date and time."""
    date_string = datetime.now().strftime("SSOCR-%Y%m%d-%H%M%S-%f")
    return date_string

if has_config:
    #Changes variables to saved settings in config.ini
    config.read("config.ini")
    ocr.pytesseract.tesseract_cmd = config.get("USERCONFIG", "tesseract_path")
else:
    #Creates default config.ini if it doesn't exist
    config.add_section("DEFAULT")
    config.add_section("USERCONFIG")
    for section in config.sections():
        #Path to TesseractOCR.exe
        config.set(section, "tesseract_path", str(ocr.pytesseract.tesseract_cmd))
        #Language to be automatically selected on application launch if default_is_combo is False
        config.set(section, "default_lang_main", "English")
        #Setting to load saved language combination instead of just one language if True
        config.set(section, "default_is_combo", str(False))
        #Language combination to be automatically selected on application launch if default_is_combo is True
        config.set(section, "default_lang_combo", "")
        #Last directory of file selected from read_image_file function
        config.set(section, "lastdir", str(DESKTOP))
        #Setting to automatically save OCR output as txt file if True
        config.set(section, "autosavetxt", str(False))
        #Setting to save screenshot snippet as png file if True
        config.set(section, "autosaveimg", str(False))
        #Setting to automatically copy OCR output to user clipboard if True
        config.set(section, "autocopy", str(False))
        #Setting to disable all keyboard shortcut in application if True
        config.set(section, "disable_shortcuts", str(False))
        #Custom save folder for saved txt files (Default is root folder of application)
        config.set(section, "savetxtpath", "")
        #Custom save folder for saved image files (Default is root folder of application)
        config.set(section, "saveimgpath", "")
    config.add_section("SAVED_LANG_COMBOS")
    write_config()

class MainWindow(QMainWindow):
    """Construct the GUI for the application."""
    def __init__(self):
        super().__init__()
        self.setWindowIcon(QIcon('screenshot_ocr-icon.png'))
        self.setWindowTitle("Screenshot OCR")
        self.setFixedSize(830, 460)

        #Display window in the center of the screen
        qtRectangle = self.frameGeometry()
        centerPoint = QDesktopWidget().availableGeometry().center()
        qtRectangle.moveCenter(centerPoint)
        self.move(qtRectangle.topLeft())

        self._centralWidget = QWidget(self)
        self.setCentralWidget(self._centralWidget)

        #Settings section top-most y-position
        self.s_s_y_pos = 261
        #Settings section y-offset between items
        self.s_s_y_offset = 21
        #Height for buttons with small_bold_font
        self.small_button_height = 24

        #Create font templates
        self.textbox_font = QFont("verdana", 10)
        self.dropdown_font = QFont("arial", 13, QFont.Bold)
        self.title_font = QFont("arial", 12, QFont.Bold)
        self.big_button_font = QFont("arial", 16, QFont.Bold)
        self.medium_bold_font = QFont("arial", 11, QFont.Bold)
        self.medium_font = QFont("arial", 12)
        self.small_bold_font = QFont("arial", 10, QFont.Bold)
        self.small_font = QFont("arial", 10)

        #Title label for the application in red text
        self.ocr_label = QLabel("Image OCR", self)
        self.ocr_label.setFont(QFont("arial", 23, QFont.Bold))
        self.ocr_label.adjustSize()
        self.ocr_label.move(9, 7)
        self.ocr_label.setStyleSheet("color: #fa0032;")

        #Label underneath snippet_button describing its function
        self.snippet_label = QLabel("OCR from a snippet of any screen\n(Shortcut: 'S')", self)
        self.snippet_label.adjustSize()
        self.snippet_label.move(9, 85)

        #Label underneath read_image_file_button describing its function
        self.read_file_label = QLabel("OCR from a local image file\n(Shortcut: 'F')", self)
        self.read_file_label.adjustSize()
        self.read_file_label.move(9, 159)
        
        #Title for lang_listbox in blue text
        self.lang_title_label = QLabel("Language", self)
        self.lang_title_label.move(191, 10)
        self.lang_title_label.setFont(self.title_font)
        self.lang_title_label.adjustSize()
        self.lang_title_label.setStyleSheet("color: #0060e6;")

        #Listbox where the main language being read is selected
        #All available languages in Tesseract-installation will be listed here as their full names (if they have one)
        self.lang_listbox = QListWidget(self)
        self.lang_listbox.setGeometry(191, 31, 140, 110)
        self.lang_listbox.itemClicked.connect(self.lang_listbox_click)

        #Title for lang_param_listbox and add_lang_listbox 
        self.lang_param_label = QLabel("Additional Languages", self)
        self.lang_param_label.move(335, 10)
        self.lang_param_label.setFont(self.title_font)
        self.lang_param_label.adjustSize()

        #Listbox where user selected additional language parameters are shown
        self.lang_param_listbox = QListWidget(self)
        self.lang_param_listbox.setGeometry(334, 31, 140, 110)

        #Listbox where additional language parameters can be selected from
        #This box lists all the same languages as lang_listbox
        self.add_lang_listbox = QListWidget(self)
        self.add_lang_listbox.setGeometry(477, 31, 140, 110)

        #Title for Language Combination section
        self.lang_combo_title_label = QLabel("Language Combinations", self)
        self.lang_combo_title_label.move(626, 10)
        self.lang_combo_title_label.setFont(self.title_font)
        self.lang_combo_title_label.adjustSize()

        #Title for saved_lang_combos_menu
        self.lang_combos_label = QLabel("Saved Language Combos", self)
        self.lang_combos_label.setFont(self.title_font)
        self.lang_combos_label.move(625, 65)
        self.lang_combos_label.adjustSize()

        #Dropdown menu where all saved language combinations are listed
        self.saved_lang_combos_menu = QComboBox(self)
        self.saved_lang_combos_menu.setGeometry(625, 85, 190, 25)
        self.saved_lang_combos_menu.setFont(self.dropdown_font)
        self.saved_lang_combos_menu.setCursor(QCursor(Qt.PointingHandCursor))
        self.saved_lang_combos_menu.activated.connect(self.set_lang_combo)
        self.saved_lang_combos_menu.setStyleSheet("color: #0032bd;")

        #Label where the selected main language is displayed in blue text
        self.main_lang_label = QLabel(self)
        self.main_lang_label.move(320, 177)
        self.main_lang_label.setFont(self.title_font)
        self.main_lang_label.setStyleSheet("color: #0060e6;")

        #Set to store added language parameters
        self.additional_lang_set = set()
        #Dictionary of available languages in Tesseract installation (k = Tesseract langcode, v = Full language name)
        self.avail_langs = {}
        #Dictionary of available languages in Tesseract installation (k = Full language name, v = Tesseract langcode)            
        self.avail_langs_swapped = {}
        #Indexed list of alphabetically sorted available full language names   
        self.avail_langs_index = []
        
        #Loads saved language combinations in saved_lang_combos_menu dropdown list
        self.load_lang_combos()

        #Loads all available languages in Tesseract-installation into lang_listbox and add_lang_listbox as their full names
        #Also selects the saved default language or language combination
        self.load_langs()                   

        #String to store the currently selected language
        self.selected_lang = self.get_main_lang()

        #Updates main_lang_label
        self.update_lang()

        #Label that lists the the language parameters used on an image after its been read
        self.read_langs_label = QLabel(self)
        self.read_langs_label.move(321, 401)
        self.read_langs_label.setFont(self.title_font)
        self.read_langs_label.setStyleSheet("color: #e6002e;")
        
        #Creates all buttons in the application
        self.create_buttons()
    
        #Title for section relating to user settings
        self.settings_label = QLabel("Settings", self)
        self.settings_label.setFont(self.title_font)
        self.settings_label.adjustSize()
        self.settings_label.move(8, 240)

        #Booleans storing the value of different user settings
        self.auto_save_txt = config.getboolean("USERCONFIG", "autosavetxt")
        self.auto_save_img = config.getboolean("USERCONFIG", "autosaveimg")
        self.auto_copy_output = config.getboolean("USERCONFIG", "autocopy")
        self.disable_shortcuts = config.getboolean("USERCONFIG", "disable_shortcuts")

        #Label that shows the folder that text files created by the applications will be saved to
        #Will show nothing if user has not specified a folder 
        self.save_txt_folder_label = QLabel(self)
        self.save_txt_folder_label.setFont(self.small_bold_font)
        self.save_txt_folder_label.move(10, self.s_s_y_pos+self.s_s_y_offset*2+3)
        self.save_txt_folder_label.setText(config.get("USERCONFIG", "savetxtpath"))
        self.save_txt_folder_label.adjustSize()
        self.save_txt_folder_label.setStyleSheet("color: #0032bd;")

        #Label that shows the folder that images created by the applications will be saved to
        #Will show nothing if user has not specified a folder 
        self.save_img_folder_label = QLabel(self)
        self.save_img_folder_label.setFont(self.small_bold_font)
        self.save_img_folder_label.move(10, self.s_s_y_pos+self.s_s_y_offset*5+3)
        self.save_img_folder_label.setText(config.get("USERCONFIG", "saveimgpath"))
        self.save_img_folder_label.adjustSize()
        self.save_img_folder_label.setStyleSheet("color: #0032bd;")

        #Creates all checkboxes in applications and assigns their saved values
        self.create_checkboxes()
        #Sets keyboard shortcuts
        self.set_shortcuts()

        #The textbox where the read text gets outputted
        self.textbox = QPlainTextEdit(self)
        self.textbox.setFont(self.textbox_font)
        self.textbox.setGeometry(320, 200, 500, 200)
        self.textbox.setReadOnly(True)

    def create_buttons(self):
        #Button which lets user take a screenshot snippet of any part of the screens to extract text from
        self.snippet_button = QPushButton("Take Snippet", self)
        self.snippet_button.setFont(self.big_button_font)
        self.snippet_button.setGeometry(7, 53, 178, 32)
        self.snippet_button.setCursor(QCursor(Qt.PointingHandCursor))
        self.snippet_button.clicked.connect(self.new_snippet)
        
        #Button which lets user extract text from a locally saved image file
        self.read_image_file_button = QPushButton("Read File", self)
        self.read_image_file_button.setFont(self.big_button_font)
        self.read_image_file_button.setGeometry(7, 127, 178, 32)
        self.read_image_file_button.setCursor(QCursor(Qt.PointingHandCursor))
        self.read_image_file_button.clicked.connect(self.read_image_file)

        #Button which lets user set the selected language as the default language to be selected when application starts up (without any additional language parameters)
        self.set_default_lang_button = QPushButton("Set Default", self)
        self.set_default_lang_button.setFont(self.small_bold_font)
        self.set_default_lang_button.setGeometry(190, 145, 130, 60)
        self.set_default_lang_button.adjustSize()
        self.set_default_lang_button.setCursor(QCursor(Qt.PointingHandCursor))
        self.set_default_lang_button.clicked.connect(self.set_default_lang_main)

        #Button which lets user add a different language as a parameter
        self.add_lang_button = QPushButton("Add Language", self)
        self.add_lang_button.setFont(self.small_bold_font)
        self.add_lang_button.setGeometry(476, 145, 130, 60)
        self.add_lang_button.adjustSize()
        self.add_lang_button.setCursor(QCursor(Qt.PointingHandCursor))
        self.add_lang_button.clicked.connect(self.add_lang_param)

        #Button which lets user remove a previously added language parameter
        self.remove_add_lang_button = QPushButton("Remove Language", self)
        self.remove_add_lang_button.setFont(self.small_bold_font)
        self.remove_add_lang_button.setGeometry(333, 145, 130, 60)
        self.remove_add_lang_button.adjustSize()
        self.remove_add_lang_button.setCursor(QCursor(Qt.PointingHandCursor))
        self.remove_add_lang_button.clicked.connect(self.remove_lang_param)

        #Button which lets user save a combination of language parameters in config.ini
        self.save_lang_combo_button = QPushButton("Save Language Combo", self)
        self.save_lang_combo_button.setFont(self.small_bold_font)
        self.save_lang_combo_button.setGeometry(625, 31, 190, self.small_button_height)
        self.save_lang_combo_button.setCursor(QCursor(Qt.PointingHandCursor))
        self.save_lang_combo_button.clicked.connect(self.save_lang_combo)

        #Button which lets user set a saved language combination as default selection when application is launched
        self.save_lang_combo_default_button = QPushButton("Set Combo As Default", self)
        self.save_lang_combo_default_button.setFont(self.small_bold_font)
        self.save_lang_combo_default_button.setGeometry(625, 145, 190, self.small_button_height)
        self.save_lang_combo_default_button.setCursor(QCursor(Qt.PointingHandCursor))
        self.save_lang_combo_default_button.clicked.connect(self.set_lang_combo_default)

        #Button which deletes a saved language combination from config.ini
        self.remove_lang_combo_button = QPushButton("Delete Language Combo", self)
        self.remove_lang_combo_button.setFont(self.small_bold_font)
        self.remove_lang_combo_button.setGeometry(625, 118, 190, self.small_button_height)
        self.remove_lang_combo_button.setCursor(QCursor(Qt.PointingHandCursor))
        self.remove_lang_combo_button.clicked.connect(self.remove_lang_combo)

        #Button which copies the contents of textbox to user's clipboard
        self.copy_button = QPushButton("Copy", self)
        self.copy_button.setFont(self.big_button_font)
        self.copy_button.setGeometry(320, 422, 130, 60)
        self.copy_button.adjustSize()
        self.copy_button.setCursor(QCursor(Qt.PointingHandCursor))
        self.copy_button.clicked.connect(self.copy_textbox_contents)

        #Button turns read-only on or off for textbox
        self.edit_textbox_button = QPushButton("Edit", self)
        self.edit_textbox_button.setFont(self.big_button_font)
        self.edit_textbox_button.setGeometry(400, 422, 130, 60)
        self.edit_textbox_button.adjustSize()
        self.edit_textbox_button.setCursor(QCursor(Qt.PointingHandCursor))
        self.edit_textbox_button.clicked.connect(self.set_textbox_readonly)

        #Button that clears the textbox and read_langs label
        self.clear_button = QPushButton("Clear", self)
        self.clear_button.setFont(self.big_button_font)
        self.clear_button.setGeometry(480, 422, 130, 60)
        self.clear_button.adjustSize()
        self.clear_button.setCursor(QCursor(Qt.PointingHandCursor))
        self.clear_button.clicked.connect(self.clear_textbox)
        
        #Button that  prints out the output of the textbox to a txt-file
        self.save_txt_button = QPushButton("Save output to txt", self)
        self.save_txt_button.setFont(self.big_button_font)
        self.save_txt_button.setGeometry(632, 422, 130, 60)
        self.save_txt_button.adjustSize()
        self.save_txt_button.setCursor(QCursor(Qt.PointingHandCursor))
        self.save_txt_button.clicked.connect(lambda:self.save_txt_file(self.textbox.toPlainText()))
        
        #Button that restores all user settings to their default values
        self.restore_default_cfg_button = QPushButton("Restore Default Configuration", self)
        self.restore_default_cfg_button.setFont(self.small_bold_font)
        self.restore_default_cfg_button.setGeometry(8, self.s_s_y_pos+self.s_s_y_offset*8, 210, 22)
        self.restore_default_cfg_button.adjustSize()
        self.restore_default_cfg_button.setCursor(QCursor(Qt.PointingHandCursor))
        self.restore_default_cfg_button.clicked.connect(self.restore_default_config)

        #Button which lets user specify the folder that all text files created by the application are saved to
        self.set_path_txt_button = QPushButton("Save text files to specific folder", self)
        self.set_path_txt_button.setFont(self.small_bold_font)
        self.set_path_txt_button.setGeometry(8, self.s_s_y_pos+self.s_s_y_offset*1-2, 210, self.small_button_height)
        self.set_path_txt_button.setCursor(QCursor(Qt.PointingHandCursor))
        self.set_path_txt_button.clicked.connect(lambda:self.set_save_folder("savetxtpath"))

        #Button which lets user specify the folder that all images created by the application are saved to
        self.set_path_img_button = QPushButton("Save images to specific folder", self)
        self.set_path_img_button.setFont(self.small_bold_font)
        self.set_path_img_button.setGeometry(8, self.s_s_y_pos+self.s_s_y_offset*4-2, 210, self.small_button_height)
        self.set_path_img_button.setCursor(QCursor(Qt.PointingHandCursor))
        self.set_path_img_button.clicked.connect(lambda:self.set_save_folder("saveimgpath"))

        #Button that resets specified folder to save text files in to default
        self.reset_path_txt_button = QPushButton("Reset", self)
        self.reset_path_txt_button.setFont(self.small_bold_font)
        self.reset_path_txt_button.setGeometry(265, self.s_s_y_pos+self.s_s_y_offset*1-2, 50, self.small_button_height)
        self.reset_path_txt_button.setCursor(QCursor(Qt.PointingHandCursor))
        self.reset_path_txt_button.clicked.connect(lambda:self.reset_save_folder("savetxtpath"))

        #Button that resets specified folder to save images in to default
        self.reset_path_img_button = QPushButton("Reset", self)
        self.reset_path_img_button.setFont(self.small_bold_font)
        self.reset_path_img_button.setGeometry(265, self.s_s_y_pos+self.s_s_y_offset*4-2, 50, self.small_button_height)
        self.reset_path_img_button.setCursor(QCursor(Qt.PointingHandCursor))
        self.reset_path_img_button.clicked.connect(lambda:self.reset_save_folder("saveimgpath"))

        #Button that shows a help-message
        self.help_button = QPushButton("Help", self)
        self.help_button.setFont(QFont("arial", 13, QFont.Bold))
        self.help_button.setGeometry(7, 210, 66, 27)
        self.help_button.setCursor(QCursor(Qt.WhatsThisCursor))
        self.help_button.clicked.connect(self.show_help)

    def create_checkboxes(self):
        #Checkbox that will automatically create a txt file of the read output when checked
        self.save_txt_checkbox = QCheckBox("Automatically save output as .txt", self)
        self.save_txt_checkbox.move(10, self.s_s_y_pos)
        self.save_txt_checkbox.adjustSize()
        self.save_txt_checkbox.setChecked(self.auto_save_txt)
        self.save_txt_checkbox.setCursor(QCursor(Qt.PointingHandCursor))
        self.save_txt_checkbox.stateChanged.connect(self.save_txt_clicked)

        #Checkbox that will automatically create a png file of the selected screenshot snippet when checked
        self.save_img_checkbox = QCheckBox("Automatically save snippet as .png", self)
        self.save_img_checkbox.move(10, self.s_s_y_pos+self.s_s_y_offset*3)
        self.save_img_checkbox.adjustSize()
        self.save_img_checkbox.setChecked(self.auto_save_img)
        self.save_img_checkbox.setCursor(QCursor(Qt.PointingHandCursor))
        self.save_img_checkbox.stateChanged.connect(self.save_img_clicked)

        #Checkbox that will automatically copy the text of a read image to the user's clipboard when checked
        self.auto_copy_checkbox = QCheckBox("Automatically copy output to clipboard", self)
        self.auto_copy_checkbox.move(10, self.s_s_y_pos+self.s_s_y_offset*6)
        self.auto_copy_checkbox.adjustSize()
        self.auto_copy_checkbox.setChecked(self.auto_copy_output)
        self.auto_copy_checkbox.setCursor(QCursor(Qt.PointingHandCursor))
        self.auto_copy_checkbox.stateChanged.connect(self.auto_copy_clicked)

        #Checkbox that will turn off all keyboard shortcuts when checked
        self.disable_shortcuts_checkbox = QCheckBox("Disable keyboard shortcuts", self)
        self.disable_shortcuts_checkbox.move(10, self.s_s_y_pos+self.s_s_y_offset*7)
        self.disable_shortcuts_checkbox.adjustSize()
        self.disable_shortcuts_checkbox.setChecked(self.disable_shortcuts)
        self.disable_shortcuts_checkbox.setCursor(QCursor(Qt.PointingHandCursor))
        self.disable_shortcuts_checkbox.stateChanged.connect(self.disable_shortcuts_clicked)

    def set_shortcuts(self):
        """Enable or disable keyboard shortcut depending on user setting."""
        if self.disable_shortcuts:
            #If user has checked the checkbox to disable shortcuts
            self.snippet_button.setShortcut("")
            self.read_image_file_button.setShortcut("")
        else:
            #If user has not checked the checkbox to disable shortcuts
            self.snippet_button.setShortcut("S")
            self.read_image_file_button.setShortcut("F")

    def save_txt_clicked(self):
        """Change value of auto_save_txt and save value to config.ini."""
        state = self.save_txt_checkbox.isChecked()
        self.auto_save_txt = state
        config.set("USERCONFIG", "autosavetxt", str(state))
        write_config()

    def save_img_clicked(self):
        """Change value of auto_save_img and save value to config.ini."""
        state = self.save_img_checkbox.isChecked()
        self.auto_save_img = state
        config.set("USERCONFIG", "autosaveimg", str(state))
        write_config()
    
    def auto_copy_clicked(self):
        """Change value of auto_copy_output and save value to config.ini."""
        state = self.auto_copy_checkbox.isChecked()
        self.auto_copy_output = state
        config.set("USERCONFIG", "autocopy", str(state))
        write_config()

    def disable_shortcuts_clicked(self):
        """Change value of disable shortcuts and save value to config.ini."""
        state = self.disable_shortcuts_checkbox.isChecked()
        self.disable_shortcuts = state
        config.set("USERCONFIG", "disable_shortcuts", str(state))
        write_config()
        self.set_shortcuts()

    def load_lang_combos(self):
        """Add all items from 'SAVED_LANG_COMBOS' section in config.ini to saved_lang_combos_menu dropdown list."""
        for item in config['SAVED_LANG_COMBOS']:
            self.saved_lang_combos_menu.addItem(item)

    def load_langs(self):
        """Add all available languages in Tesseract installation in indexed list, dictionaries and listboxes."""
        languages = ocr.get_languages()
        for lang in languages:
            #Adds the full language name from value in lang_codes_dict if key exists, otherwise adds the langcode's key as value in new dictionary
            self.avail_langs[lang] = lang_codes_dict.setdefault(lang, lang)
            #Adds the full language name to an indexed list
            self.avail_langs_index.append(self.avail_langs[lang])
        #Sorts the language names alphabetically
        self.avail_langs_index.sort(key=str.casefold)
        #Swaps the 'self.avail_langs' values with its keys
        self.avail_langs_swapped = dict([(value, key) for key, value in self.avail_langs.items()])
        
        #Adds all available languages to lang_listbox and add_lang_listbox
        self.lang_listbox.insertItems(0, self.avail_langs_index)
        self.add_lang_listbox.insertItems(0, self.avail_langs_index)
        #Updates the GUI based on user config
        self.update_all_lang_selection()

    def update_all_lang_selection(self):
        """Set language selections from saved user config."""
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

    def get_main_lang(self) -> str:
        """Return the text of currently selected index in lang_listbox."""
        return self.lang_listbox.currentItem().text()
    
    def get_lang_index(self) -> int:
        """Return the index of currently selected item in lang_listbox."""
        return self.lang_listbox.currentRow()

    def lang_listbox_click(self):
        """Update selected_lang label when new item is selected in lang_listbox."""
        self.selected_lang = self.get_main_lang()
        self.update_lang()

    def get_additional_lang_index(self) -> int:
        """Return the index of currently selected item in add_lang_listbox."""
        return self.add_lang_listbox.currentRow()

    def set_default_lang_main(self):
        """Save default language (single) to config.ini."""
        config.set("USERCONFIG", "default_lang_main", self.selected_lang)
        config.set("USERCONFIG", "default_is_combo", str(False))
        config.set("USERCONFIG", "default_lang_combo", "")
        write_config()

    def update_lang(self):
        """Update text of main_lang_label."""
        self.main_lang_label.setText(f"Selected Language: {self.selected_lang}")
        self.main_lang_label.adjustSize()

    def add_lang_param(self):
        """Add selected language from add_lang_listbox to additional_lang_set and lang_param_listbox."""
        new_lang = self.avail_langs_index[self.get_additional_lang_index()]
        if new_lang != self.get_main_lang():
            #Doesn't add language to parameters if it is already the selected main language
            self.additional_lang_set.add(new_lang)
            self.update_lang_param_listbox()
            #Selects the newly added item in the lang_param_listbox
            for index, langs in enumerate(self.additional_lang_set):
                if langs == new_lang:
                    self.lang_param_listbox.setCurrentRow(index)
                    break

    def remove_lang_param(self):
        """Remove selected language from lang_param_listbox."""
        row = self.lang_param_listbox.currentRow()
        if row >= 0:
            #Does nothing if no item in listbox is currently selected
            lang = self.lang_param_listbox.currentItem().text()
            self.additional_lang_set.remove(lang)
            self.update_lang_param_listbox()

    def update_lang_param_listbox(self):
        """Update the items of lang_param_listbox from additional_lang_set."""
        self.lang_param_listbox.clear()
        self.lang_param_listbox.addItems(self.additional_lang_set)

    def get_lang_combo(self) -> str:
        """Return a formatted language parameter string from selected_lang and additional_lang_set."""
        #Gets the language parameter from the language name
        lang_param = self.avail_langs_swapped[self.selected_lang]
        #Checks if there are any added languages
        for lang in self.additional_lang_set:
            #Adds the language(s) to the lang parameter
            lang_param += f"+{self.avail_langs_swapped[lang]}"
        return lang_param
    
    def set_lang_combo(self):
        """Set saved language combination as the selected language with its additional language parameters added."""
        if len(self.saved_lang_combos_menu) > 0:
            #Do nothing if menu is empty
            langs = self.saved_lang_combos_menu.currentText().split("+")
            #Set langs[0] as the main language
            self.selected_lang = self.avail_langs[langs[0]]
            self.additional_lang_set.clear()
            for lang in langs[1::]:
                #Set every item after index 0 as an additional language
                self.additional_lang_set.add(self.avail_langs[lang])
            self.update_lang()
            self.update_lang_param_listbox()

    def save_lang_combo(self):
        """Save current language combination to config.ini."""
        if len(self.additional_lang_set) > 0:
            #Do nothing if no additional languages has been added
            lang_combo = self.get_lang_combo()
            config.set("SAVED_LANG_COMBOS", lang_combo)
            write_config()
            #Adds the new index to the dropdown menu of saved language combination
            self.saved_lang_combos_menu.clear()
            self.load_lang_combos()
            #Automatically selects the newly added language combo (Last index in list)
            self.saved_lang_combos_menu.setCurrentIndex(self.saved_lang_combos_menu.count()-1)

    def remove_lang_combo(self):
        """Delete saved language combination from config.ini."""
        option = self.saved_lang_combos_menu.currentText()
        config.remove_option("SAVED_LANG_COMBOS", option)
        write_config()
        #Update the dropdown menu
        self.saved_lang_combos_menu.clear()
        self.load_lang_combos()
        if len(self.saved_lang_combos_menu) == 0 and config.getboolean("USERCONFIG", "default_is_combo") is True:
            #If there is no items left in dropdown menu, set the saved default language as default without any additional languages
            self.set_default_lang_main()
            self.additional_lang_set.clear()
        self.reset_gui()

    def set_lang_combo_default(self):
        """Set selected language combination as default selection in config.ini."""
        if len(self.saved_lang_combos_menu) > 0:
            lang_combo = self.get_lang_combo()
            #Change boolean to load additional languages to true and save the language combination
            config.set("USERCONFIG", "default_is_combo", str(True))
            config.set("USERCONFIG", "default_lang_combo", lang_combo)
            write_config()

    def reset_gui(self):
        """Update all language related components in GUI to the saved default values in config.ini."""
        self.additional_lang_set.clear()
        self.update_lang_param_listbox()
        self.update_all_lang_selection()
        self.selected_lang = self.get_main_lang()
        self.update_lang()

    def clear_textbox(self):
        """Empty textbox and read_langs_label."""
        self.textbox.clear()
        self.read_langs_label.clear()

    def copy_textbox_contents(self):
        """Copy contents of textbox to user clipboard."""
        if self.textbox.toPlainText() != "":
            #Do nothing if textbox is empty
            clipboard = QApplication.clipboard()
            clipboard.setText(self.textbox.toPlainText())
        
    def set_textbox_readonly(self):
        """Enable or disable ReadOnly for textbox."""
        if self.textbox.isReadOnly() is True:
            self.textbox.setReadOnly(False)
        else:
            self.textbox.setReadOnly(True)

    def save_txt_file(self, output):
        """Save contents of textbox to txt file."""
        #Name txt file after current datetime
        date_string = get_time_string()
        #Set savepath based on user specified save folder
        save_path = self.get_save_folder("savetxtpath")
        full_path = f"{save_path}{date_string}.txt"
        if output != "":
            #Don't save if textbox is empty
            with open(full_path, "w", encoding="utf-8") as file:
                file.write(output)

    def get_save_folder(self, cfg_var) -> str:
        """Return formatted savepath for specified savefolder variable in config.ini."""
        save_path = config.get("USERCONFIG", cfg_var)
        if save_path != "":
            if pathlib.Path(save_path).exists() is False:
                #Create directory if it doesn't exist
                pathlib.Path(save_path).mkdir(parents=True)
            #Append forward-slash if user has specified custom save folder
            save_path = save_path+"/"
        return save_path

    def set_save_folder(self, cfg_var):
        """Save user selected folder to specified savefolder variable in config.ini."""
        folder = QFileDialog.getExistingDirectory(None, "Select Folder")
        if folder != "":
            #Do nothing if user cancels filedialog
            config.set("USERCONFIG", cfg_var, folder)
            write_config()
            self.update_save_folder(cfg_var, folder)
    
    def reset_save_folder(self, cfg_var):
        """Delete value for specified savefolder variable in config.ini if user selects Yes."""
        if config.get("USERCONFIG", cfg_var) != "":
            #Do nothing if custom save folder has not been set
            if cfg_var == "savetxtpath":
                filetype = "text files"
            elif cfg_var == "saveimgpath":
                filetype = "images"
            confirmbox = QMessageBox().question(self, "Reset Save Folder", f"Are you sure you want reset save folder for {filetype}?", QMessageBox().Yes | QMessageBox().No)
            if confirmbox == QMessageBox.Yes:
                config.set("USERCONFIG", cfg_var, "")
                write_config()
                self.update_save_folder(cfg_var, "")

    def update_save_folder(self, cfg_var, value):
        """Update GUI label associated with specified savefolder variable."""
        if cfg_var == "savetxtpath":
            self.save_txt_folder_label.setText(value)
            self.save_txt_folder_label.adjustSize()
        elif cfg_var == "saveimgpath":
            self.save_img_folder_label.setText(value)
            self.save_img_folder_label.adjustSize()

    def read_image_buffer(self, pixmap):
        """Convert QPixmap image to PIL Image and send converted image to OCR function."""
        #Convert QPixmap to QImage
        screenshot = QImage()
        screenshot = pixmap.toImage()
        buffer = QBuffer()
        buffer.open(QBuffer.ReadWrite)
        #Convert QImage to PIL Image
        screenshot.save(buffer, "PNG")
        newimg = Image.open(io.BytesIO(buffer.data()))
        buffer.close()
        #Send image to OCR function
        self.ocr_image(newimg)

    def read_image_file(self):
        """Send user selected image file to OCR function."""
        #Sets the default directory to directory of last selected file (stored in config.ini)
        lastdir = config.get("USERCONFIG", "lastdir")
        file, check = QFileDialog.getOpenFileName(None, "Select File",
                                                  lastdir, "All Files (*)")
        if check:
            #If file was selected
            get_dir = file.rsplit("/",1)[0]
            #Save file's directory in config.ini
            config.set("USERCONFIG", "lastdir", get_dir)
            write_config()
            try:
                #Send image to OCR function if file is a valid image
                img = Image.open(file)
                self.ocr_image(img)
            except:
                #Show error message if file is not valid
                error_msg = QMessageBox()
                error_msg.setIcon(QMessageBox.Critical)
                error_msg.setText("Error reading file!")
                error_msg.setInformativeText("The selected file is not a valid image file.")
                error_msg.setWindowTitle("Error")
                error_msg.exec_()

    def ocr_image(self, image):
        """Use TesseractOCR to extract text from image."""
        #Set chosen language parameters
        lang_param = self.get_lang_combo()
        img_text = ocr.image_to_string(image, lang=lang_param).strip()
        #Paste output string to textbox without trailing whitespaces
        self.textbox.setPlainText(img_text)
        if self.auto_copy_output:
            #Copy output to user clipboard if auto_copy_checkbox is checked
            self.copy_textbox_contents()
        if self.auto_save_txt:
            #Save output as txt file if save_txt_checkbox is checked
            self.save_txt_file(img_text)
        self.print_read_langs()

    def print_read_langs(self):
        """Show language parameters used in OCR function in GUI."""
        langs = self.get_lang_combo()
        self.read_langs_label.setText(f"Language Parameters: {langs}")
        self.read_langs_label.adjustSize()

    def restore_default_config(self):
        """Overwrite [USERCONFIG] with [DEFAULT] in config.ini if user selects "Yes"."""
        confirmbox = QMessageBox().question(self, "Restore Default Configuration", "Are you sure you want to restore default configuration?\nThis can not be undone.", QMessageBox().Yes | QMessageBox().No)
        if confirmbox == QMessageBox.Yes:
            default_config = config.items("DEFAULT")
            for k, v in default_config:
                config.set("USERCONFIG", k, v)
            write_config()
            self.reset_gui()
            self.save_txt_folder_label.clear()
            self.save_img_folder_label.clear()

    def show_help(self):
        """Show help messagebox."""
        help_msg = QMessageBox()
        help_msg.setIcon(QMessageBox.Information)
        help_msg.setText("Extract text from an image using TesseractOCR by either taking a screenshot snippet from your screens with the application or by selecting a locally saved image file. The snippet tool may not cover all screens if monitor resolutions and positions differ wildly from each other.\n\nTo change which language to read, select the language from the list of languages with the blue text. If the language you are looking for is not in the list, it is either not supported by TesseractOCR or you have not installed the language in Tesseract.\n\nIf you want to read multiple languages you can add them from the list of available languages under 'Additional Languages' (rightmost listbox). If you want to use the language combination another time, you can save the current language combination. Language combinations are saved to the 'config.ini' file.")
        help_msg.setWindowTitle("Help")
        help_msg.exec_()

    def new_snippet(self):
        """
        Create dim Splashscreen object and show dim Splashscreen.

        Also responsible for tracking mouse and capturing screenshot.
        """
        self.snippet = CreateSnippet(self)
        self.snippet.show()


class CreateSnippet(QSplashScreen):
    """QSplashScreen, that track mouse event for capturing screenshot."""
    def __init__(self, mainwindow):
        super().__init__()
        #Reference to MainWindow object
        self.mainwindow = mainwindow

        #Start and end variables for snippet function
        self.origin = QPoint(0,0)
        self.end = QPoint(0,0)

        #The box that shows when holding mouse down
        self.rubberband = QRubberBand(QRubberBand.Rectangle, self)
        
        #The leftmost x-coordinate of all monitors geometry, might be negative
        self.x_min = 0
        #The topmost y-coordinate of all monitors geometry, might be negative
        self.y_min = 0

        #Function to capture snippet
        self.dim_screen()

    def dim_screen(self):
        """
        Fill splashScreen with black color and reduce the widget opacity to create dim screen effect on all screens.

        This will not work for very weird multiple-monitor positions or when difference in resolutions between monitors are too varied.
        """
        #Get the combined geometry of all monitors
        screen_geometry = QGuiApplication.primaryScreen().virtualGeometry()     
        all_screens = QGuiApplication.screens()

        #Change cursor to cross when inside snippet functionality
        self.setCursor(QCursor(Qt.CrossCursor))
        
        x_values = []
        y_values = []
        #Loop through all screens to set coordinates that matches monitor positions
        for screen in all_screens:
            #Updates the leftmost and topmost coordinates
            if self.x_min > screen.geometry().left():
                self.x_min = screen.geometry().left()
            if self.y_min > screen.geometry().top():
                self.y_min = screen.geometry().top()

            #Create a list based on maximum x and y coordinates for every monitor
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

        #Fill all screens with black color
        screen_pixelmap = QPixmap(width, height)
        screen_pixelmap.fill(QColor(0,0,0))

        #Always place dim/pixmap in center regardless of monitor position
        avg_x = int(sum(x_values)/len(x_values))
        avg_y = int(sum(y_values)/len(y_values))
        self.move(avg_x, avg_y)

        self.setPixmap(screen_pixelmap)
        #Minimize MainWindow so user can snippet what's behind it
        self.mainwindow.hide()
        #Set opacity of black color to 40%
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
            #Get start coordinates
            self.origin = event.pos()
            self.rubberband.setGeometry(QRect(self.origin, QSize()))
            self.rubberband.show()

    def mouseMoveEvent(self, event):
        """Resize rectangle as we move mouse, after left-clicked."""
        self.rubberband.setGeometry(QRect(self.origin, event.pos()).normalized())

    def mouseReleaseEvent(self, event):
        """Upon mouse released, ask the main desktop's QScreen to capture screen on defined area."""
        if event.button() == Qt.LeftButton:
            #Get end coordinates
            self.end = event.pos()
            #Hide QSplashScreen
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
            #Convert QPixmap to PIL Image and OCR image
            self.mainwindow.read_image_buffer(selected_pixel_map)
            
            if self.mainwindow.auto_save_img:
                #Save screenshot snippet as png file if save_img_textbox is checked
                date_string = get_time_string()
                save_path = self.mainwindow.get_save_folder("saveimgpath")
                full_path = f"{save_path}{date_string}.png"
                selected_pixel_map.save(full_path, "png")

            #Return to MainWindow
            self.mainwindow.show()

#Dictionary to convert TesseractOCR language codes to their full names
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
    """
    Window to show error if path to TesseractOCR.exe is not valid.
    
    Lets user specify path to TesseractOCR.exe via QFileDialog.
    """
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
        """Make user set path to TesseractOCR.exe."""
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
            except ocr.TesseractNotFoundError:
                #Display file_error_msg and then close application if file selected is not valid
                sys.exit(self.file_error_msg.exec_())
            except Exception as e:
                #Display error in messagebox and then close application if unexpected error has occured
                unexpected_error(str(e))
        else:
            #Close application if user cancels filedialog
            sys.exit()
        
def unexpected_error(exception):
    """Show messagebox displaying error message."""
    unexpected_error_msg = QMessageBox()
    unexpected_error_msg.setIcon(QMessageBox.Critical)
    unexpected_error_msg.setText("Unexpected Error!")
    #Print the error message(exception parameter) to messagebox
    unexpected_error_msg.setInformativeText(f"Error Message:\n'{exception}'\n\nTry deleting 'config.ini' file.")
    unexpected_error_msg.setWindowTitle("Error")
    #Close application after messagebox is closed
    sys.exit(unexpected_error_msg.exec_())

def main():
    """Main function."""
    app = QApplication([])
    try:
        mw = MainWindow()
        mw.show()
    except ocr.TesseractNotFoundError:
        ErrorWindow()
    except Exception as e:
        unexpected_error(str(e))
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()