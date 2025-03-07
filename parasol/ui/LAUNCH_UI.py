import PyQt5
from PyQt5.QtWidgets import (
    QMainWindow,
    QApplication,
    QPushButton,
    # QLineEdit,
    # QListWidget,
    # QListWidgetItem,
    # QSizePolicy,
    # QFileDialog,
    QComboBox
)
import PyQt5.QtGui
from PyQt5 import QtCore
from PyQt5 import uic
import os
import sys

from parasol.configuration.configuration import Configuration
config = Configuration()
constants = config.get_config()['LAUNCH_UI']

MODULE_DIR = os.path.dirname(__file__)
# Ensure resolution/dpi is correct for UI
if hasattr(QtCore.Qt, "AA_EnableHighDpiScaling"):
    PyQt5.QtWidgets.QApplication.setAttribute(QtCore.Qt.AA_EnableHighDpiScaling, True)

if hasattr(QtCore.Qt, "AA_UseHighDpiPixmaps"):
    PyQt5.QtWidgets.QApplication.setAttribute(QtCore.Qt.AA_UseHighDpiPixmaps, True)


def LAUNCHER():
    """Create LAUNCH UI window"""
    
    class LAUNCH_UI(QMainWindow):
        """LAUNCH UI package for PARASOL"""

        def __init__(self) -> None:
            """Initliazes the LAUNCH_UI class"""

            # Define UI
            super(LAUNCH_UI, self).__init__()

            # Load the UI file
            ui_path = os.path.join(MODULE_DIR, "LAUNCH_UI.ui")
            uic.loadUi(ui_path, self)
            self.show()
            
            # Dropdown for function
            self.function = self.findChild(QComboBox, "Function")
            self.function.clear()
            self.function.addItem('Runner')
            self.function.addItem('Grapher')
            self.function.setCurrentIndex(int(constants["function"]))

            # Dropdown for mode
            self.mode = self.findChild(QComboBox, "Mode")
            self.mode.clear()
            self.mode.addItem('Indoor')
            self.mode.addItem('Outdoor')
            self.mode.setCurrentIndex(int(constants["mode"]))
            
            # Manage rootdir button
            self.startbutton = self.findChild(QPushButton, "StartButton")
            self.startbutton.clicked.connect(self.startbutton_clicked)
            self.startbutton.setEnabled(True)
            
            # option to automatically boot desired function & mode
            if constants['bypass']:
                self.startbutton_clicked()

        
        
        def startbutton_clicked(self) -> None:
            """Launches appropriate imports and macros for situation"""
            try:
                # different programs for run_ui
                if self.function.currentIndex() == 0: # Runner
                    
                    from parasol.ui.RUN_UI import RUN_UI
                    self.window = QMainWindow()
                    self.ui = RUN_UI()
                    
                    if self.mode.currentIndex() == 0: # Indoor
                        self.ui.customize('indoor')       
                    else: # Outdoor
                        self.ui.customize('outdoor')
                        
                else: # Grapher (indoor or outdoor)
                    from parasol.ui.GRAPH_UI import GRAPH_UI
                    self.window = QMainWindow()
                    self.ui = GRAPH_UI()


                # option to hide the LAUNCH UI after launch
                if constants['hide_after_launch']:
                    self.hide()
            except Exception as e:
                print(f"Error launching UI: {e}")
            
    
    # Create application (required for widget)
    app = QApplication(sys.argv)

    # Create UI, which is a widget
    window = LAUNCH_UI()

    # Start the application
    app.exec_()
