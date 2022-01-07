import PyQt5
from PyQt5.QtWidgets import QMainWindow, QApplication, QCheckBox, QComboBox
from PyQt5.QtWidgets import (
    QPushButton,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QOpenGLWidget,
)
from PyQt5 import QtCore
from PyQt5 import uic
import sys
import os
from datetime import datetime
import yaml


# Import Controller (call load, unload), characterization (know test types), and analysis (check on tests)

# Set module directory
MODULE_DIR = os.path.dirname(__file__)

# Ensure resolution/dpi is correct for UI
if hasattr(QtCore.Qt, "AA_EnableHighDpiScaling"):
    PyQt5.QtWidgets.QApplication.setAttribute(QtCore.Qt.AA_EnableHighDpiScaling, True)

if hasattr(QtCore.Qt, "AA_UseHighDpiPixmaps"):
    PyQt5.QtWidgets.QApplication.setAttribute(QtCore.Qt.AA_UseHighDpiPixmaps, True)


class GRAPH_UI(QMainWindow):
    """Run UI package for PARASOL"""

    def __init__(self) -> None:
        """Initliazes the RUN_UI class"""

        super(GRAPH_UI, self).__init__()

        # start with genearic root dir from fileprogram but allow change
        rootdir = "C:\\Users\\seand\\Documents\\Data"

        # Load the ui file
        ui_path = os.path.join(MODULE_DIR, "GRAPH_UI.ui")
        uic.loadUi(ui_path, self)
        self.show()

        # Load all Test Folders, clear, add events on click and doubleclick, and populate list
        self.alltestfolders = self.findChild(QListWidget, "AllTestFolders")
        self.alltestfolders.clear()
        self.alltestfolders.itemClicked.connect(self.testfolder_clicked)
        self.alltestfolders.itemDoubleClicked.connect(self.testfolder_doubleclicked)
        self.update_test_folders(rootdir)

        # Loads all the graphics
        self.fwd_jsc_graphics = self.findChild(PyQt5.QtWidgets.QOpenGLWidget, "FWD_Jsc")
        self.fwd_voc_graphics = self.findChild(PyQt5.QtWidgets.QOpenGLWidget, "FWD_Voc")
        self.fwd_ff_graphics = self.findChild(PyQt5.QtWidgets.QOpenGLWidget, "FWD_FF")
        self.fwd_pce_graphics = self.findChild(PyQt5.QtWidgets.QOpenGLWidget, "FWD_PCE")

        self.rev_jsc_graphics = self.findChild(PyQt5.QtWidgets.QOpenGLWidget, "REV_Jsc")
        self.rev_voc_graphics = self.findChild(PyQt5.QtWidgets.QOpenGLWidget, "REV_Voc")
        self.rev_ff_graphics = self.findChild(PyQt5.QtWidgets.QOpenGLWidget, "REV_FF")
        self.rev_pce_graphics = self.findChild(PyQt5.QtWidgets.QOpenGLWidget, "REV_PCE")

        self.fwd_jsc_plot = self.fwd_jsc_graphics.addPlot(title="Fwd Jsc v Time")

        # self.fwd_jsc_graphics.addPlot(title="FWD Jsc")
        self.fwd_jsc_plot.plot([1, 2, 3])

        # Create GUI
        self.launch_gui()

    def update_test_folders(self, rootdir: str) -> None:
        """Updates the list of test folders"""

        # Clear current list
        self.alltestfolders.clear()

        # Get Test Folder List, add items
        self.testfolderlist = ["test1", "test2", "test3"]
        for testfolder in self.testfolderlist:
            self.alltestfolders.addItem(testfolder)

        # Create Dictionary to keep track of selected test folders
        self.test_selection_dict = {}
        for testfolder in self.testfolderlist:
            self.test_selection_dict[testfolder] = False

    def testfolder_clicked(self, item: QListWidgetItem) -> None:
        """Temporarily displays the test folder when clicked"""
        print(item.text())

    def testfolder_doubleclicked(self, item: QListWidgetItem) -> None:
        """Permanantley displays the test folder when double clicked"""

        # Change status of selected test folder
        if self.test_selection_dict[str(item.text())] == False:
            self.test_selection_dict[str(item.text())] = True
        elif self.test_selection_dict[str(item.text())] == True:
            self.test_selection_dict[str(item.text())] = False

        self.colorize_list()

    def colorize_list(self):

        # Colorize the list
        for i, key in enumerate(self.test_selection_dict):
            if self.test_selection_dict[key] == True:
                self.alltestfolders.item(i).setBackground(QtCore.Qt.green)
            elif self.test_selection_dict[key] == False:
                self.alltestfolders.item(i).setBackground(QtCore.Qt.red)

    def launch_gui(self) -> None:
        """Launches GUI"""
        # exexcutes the GUI
        app = QApplication(sys.argv)
        app.exec_()
