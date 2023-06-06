# Screenshot OCR

**Screenshot OCR** is a desktop GUI frontend for Tesseract OCR Engine made for Windows. The application allows the user to select a snippet of their screen, automatically execute Tesseract and extract the text from the snippet.

## Features

- **Select a snippet of your screen to perform OCR on, without needing to save or load an image**
- Automatically copy OCR output to clipboard
- Perform OCR on a local file 
- Keyboard shortcuts *(Can be disabled)*
- Select language to perform OCR on from a list of installed languages in Tesseract
- Add additional languages as parameters to OCR
- Save default language between uses
- Save combinations of base language + additional language parameters between uses
- Edit output text in application
- Option to save OCR output as .txt file
- Option to save screen snippet as .png file
- Save 

## Requirements

Screenshot OCR requires Python to run *(Version 3.10 or newer is recommended)* and the following packages:
- [PyQt5](https://pypi.org/project/PyQt5/)
- [pytesseract](https://pypi.org/project/pytesseract/)
  
Everything can be installed from either *requirements.txt* or the *Pipfile*.

For the program to work you also need **[Tesseract OCR Engine for Windows](https://tesseract-ocr.github.io/tessdoc/Downloads.html)** installed on your system.

## How To Use

The application will look for a Tesseract executable in *'C:\Program Files\Tesseract-OCR\tesseract.exe'*. If your installation of Tesseract is located elsewhere, you can manually select it when first running the program.

Before performing OCR, select the language you want to read from the left-most list-box. If you want to add additional languages, you can select them from the third list-box and then click the 'Add Language' button below the list-box. All additional languages now appear in the second list-box. To remove an additional language, select the language and click the 'Remove Language' button below the second list-box.

### **Perform OCR On Screen Snippet**

Click on the **'Take Snippet'** button (or just press **'S'** on your keyboard) to bring up the snippet functionality. Hold down the left mouse-button and draw a rectangle around the text your want to read, and when you let go, the application will automatically perform OCR on the selected area. The output will then be pasted into the text-field in the application.

You can press **'Esc'** to exit the snippet functionality without performing OCR on anything.

The snippet functionality works on multiple monitors, but may not completely cover everything if the monitor's resolutions and positions differ wildly from each other. Move the text you want to OCR onto your main monitor if this is an issue.


## Saved Configuration
