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

from parasol.filestructure import FileStructure
from parasol.analysis.grapher import Grapher


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

        # Define UI
        super(GRAPH_UI, self).__init__()

        # Load other modules
        self.filestructure = FileStructure()
        self.grapher = Grapher()

        # Assume basic root directory --> will add to UI
        rootdir = self.filestructure.get_root_dir()

        # Load the ui file
        ui_path = os.path.join(MODULE_DIR, "GRAPH_UI.ui")
        uic.loadUi(ui_path, self)
        self.show()

        # Load all Test Folders, clear list, add events on click and doubleclick
        self.alltestfolders = self.findChild(QListWidget, "AllTestFolders")
        self.alltestfolders.clear()
        self.alltestfolders.itemClicked.connect(self.testfolder_clicked)
        self.alltestfolders.itemDoubleClicked.connect(self.testfolder_doubleclicked)
        # Update list of tests, create dict[Folderpath] = True/False for plotting
        self.test_selection_dict = self.update_test_folders(rootdir)

        # Loads all the graphics
        self.fwd_jsc_graphics = self.findChild(PyQt5.QtWidgets.QOpenGLWidget, "FWD_Jsc")
        self.fwd_voc_graphics = self.findChild(PyQt5.QtWidgets.QOpenGLWidget, "FWD_Voc")
        self.fwd_ff_graphics = self.findChild(PyQt5.QtWidgets.QOpenGLWidget, "FWD_FF")
        self.fwd_pce_graphics = self.findChild(PyQt5.QtWidgets.QOpenGLWidget, "FWD_PCE")

        self.rev_jsc_graphics = self.findChild(PyQt5.QtWidgets.QOpenGLWidget, "REV_Jsc")
        self.rev_voc_graphics = self.findChild(PyQt5.QtWidgets.QOpenGLWidget, "REV_Voc")
        self.rev_ff_graphics = self.findChild(PyQt5.QtWidgets.QOpenGLWidget, "REV_FF")
        self.rev_pce_graphics = self.findChild(PyQt5.QtWidgets.QOpenGLWidget, "REV_PCE")

        self.rser_graphics = self.findChild(PyQt5.QtWidgets.QOpenGLWidget, "Rser")
        self.rsh_graphics = self.findChild(PyQt5.QtWidgets.QOpenGLWidget, "Rsh")
        self.rch_graphics = self.findChild(PyQt5.QtWidgets.QOpenGLWidget, "Rch")
        self.mpp_graphics = self.findChild(PyQt5.QtWidgets.QOpenGLWidget, "mppt")

        self.plot_params = [
            "FWD_Jsc",
            "FWD_Voc",
            "FWD_FF",
            "FWD_PCE",
            "REV_Jsc",
            "REV_Voc",
            "REV_FF",
            "REV_PCE",
            ["FWD_Rser", "REV_Rser"],
            ["FWD_Rsh", "REV_Rsh"],
            ["FWD_Rch", "REV_Rch"],
            "mppt",
        ]

        # Create GUI
        self.launch_gui()

    # List of all test folders --> autoupdates when the program launches
    def update_test_folders(self, rootdir: str) -> dict:
        """Updates the list of test folders"""

        # Clear current displaylist
        self.alltestfolders.clear()

        # Get test folders, add them to the list (just folder, not path)
        test_folder_list = self.filestructure.get_tests(rootdir)
        for testfolder in test_folder_list:
            self.alltestfolders.addItem(testfolder.split(":")[-1])

        # Create Dictionary to keep track of selected test folders dict[Folderpath] = True/False
        test_selection_dict = {}
        for testfolder in test_folder_list:
            test_selection_dict[testfolder] = False

        # Return the dictionary
        return test_selection_dict

    # List of all selected test folders --> autoupdates when the program launches
    def get_selected_folders(self) -> list:

        # self.test_selection_dict[TestFolderpath] = True/False for selected

        selected_test_folders = []

        for key in self.test_selection_dict:
            if self.test_selection_dict[key] == True:
                selected_test_folders.append(key)

        return selected_test_folders

    # Command on single click
    def testfolder_clicked(self, item: QListWidgetItem) -> None:
        """Temporarily displays the test folder when clicked"""
        print(item.text())

    # Command on double click
    def testfolder_doubleclicked(self, item: QListWidgetItem) -> None:
        """Permanantley displays the test folder when double clicked"""

        # Change status of selected test folder
        if self.test_selection_dict[str(item.text())] == False:
            self.test_selection_dict[str(item.text())] = True
        elif self.test_selection_dict[str(item.text())] == True:
            self.test_selection_dict[str(item.text())] = False

        # Color input values using dictionary
        self.colorize_list()

        # Get selected tests from dictionary, use them to update plots
        self.selected_tests = self.get_selected_folders()
        tests_to_plot = self.selected_tests
        self.update_plots(tests_to_plot)

    def colorize_list(self):

        # Colorize the list
        for i, key in enumerate(self.test_selection_dict):
            if self.test_selection_dict[key] == True:
                self.alltestfolders.item(i).setBackground(QtCore.Qt.green)
            elif self.test_selection_dict[key] == False:
                self.alltestfolders.item(i).setBackground(QtCore.Qt.red)

    def update_plots(tests_to_plot):
        print(tests_to_plot)

    def launch_gui(self) -> None:
        """Launches GUI"""
        # exexcutes the GUI
        app = QApplication(sys.argv)
        app.exec_()
