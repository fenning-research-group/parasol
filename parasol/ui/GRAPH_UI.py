import PyQt5
from PyQt5.QtWidgets import QMainWindow, QApplication, QCheckBox, QComboBox
from PyQt5.QtWidgets import (
    QPushButton,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QOpenGLWidget,
    QVBoxLayout,
    QFrame,
    QSizePolicy,
)
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
import matplotlib.pyplot as plt
import matplotlib as mpl

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

        # Create user variables
        nrows = 4
        ncols = 3
        dpival = 50
        rootdir = self.filestructure.get_root_dir()

        # Load the ui file
        ui_path = os.path.join(MODULE_DIR, "GRAPH_UI.ui")
        uic.loadUi(ui_path, self)

        # Load testfolderdisplay list widget, clear list, add events on click and doubleclick
        self.alltestfolders = self.findChild(QListWidget, "AllTestFolders")
        self.alltestfolders.clear()
        self.alltestfolders.itemClicked.connect(self.testfolder_clicked)
        self.alltestfolders.itemDoubleClicked.connect(self.testfolder_doubleclicked)
        # Update list of tests, create dict[Foldername] = True/False for plotting and dict[Foldername] = Folderpath
        self.testname_to_testpath, self.test_selection_dict = self.update_test_folders(
            rootdir
        )

        # Get layout where we are appending graphs
        self.layout = self.findChild(PyQt5.QtWidgets.QFrame, "graphframe")

        # Create a figure with several subplots, devide up axes
        self.figure, self.axes = plt.subplots(
            ncols, nrows, dpi=dpival, tight_layout=True
        )

        # Make axes dict for plots, numbering left -> right & top -> down
        idnum = 1
        self.plot_axes_dict = {}
        for colnum in range(ncols):
            for rownum in range(nrows):
                self.plot_axes_dict[idnum] = self.axes[colnum][rownum]
                idnum += 1

        # Make dict to hold y parameter names
        self.plot_y_dict = {
            1: self.grapher.variable_dict["FWD Jsc"],
            2: self.grapher.variable_dict["FWD Voc"],
            3: self.grapher.variable_dict["FWD FF"],
            4: self.grapher.variable_dict["FWD PCE"],
            5: self.grapher.variable_dict["REV Jsc"],
            6: self.grapher.variable_dict["REV Voc"],
            7: self.grapher.variable_dict["REV FF"],
            8: self.grapher.variable_dict["REV PCE"],
            9: [
                self.grapher.variable_dict["FWD Rs"],
                self.grapher.variable_dict["REV Rs"],
            ],
            10: [
                self.grapher.variable_dict["FWD Rsh"],
                self.grapher.variable_dict["REV Rsh"],
            ],
            11: [
                self.grapher.variable_dict["FWD Rch"],
                self.grapher.variable_dict["REV Rch"],
            ],
            12: "MPP",
        }

        # Make dict to hold x parameter names
        self.plot_x_dict = {
            1: self.grapher.variable_dict["Time Elapsed"],
            2: self.grapher.variable_dict["Time Elapsed"],
            3: self.grapher.variable_dict["Time Elapsed"],
            4: self.grapher.variable_dict["Time Elapsed"],
            5: self.grapher.variable_dict["Time Elapsed"],
            6: self.grapher.variable_dict["Time Elapsed"],
            7: self.grapher.variable_dict["Time Elapsed"],
            8: self.grapher.variable_dict["Time Elapsed"],
            9: self.grapher.variable_dict["Time Elapsed"],
            10: self.grapher.variable_dict["Time Elapsed"],
            11: self.grapher.variable_dict["Time Elapsed"],
            12: self.grapher.variable_dict["Time Elapsed"],
        }

        # Place figure in canvas, control resize policy, resize, place on UI, and set location
        self.canvas = FigureCanvas(self.figure)
        self.canvas.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.canvas.updateGeometry()
        self.canvas.setParent(self.layout)

        # Make Plots work!
        self.canvas.resize(1072,804)
        mpl.rcParams["font.size"] = 8
        for key in self.plot_axes_dict:
            self.plot_axes_dict[key].tick_params(direction="in", labelsize="small")

        # show UI
        self.show()

        # Create GUI
        self.launch_gui()

    # List of all test folders --> autoupdates when the program launches
    def update_test_folders(self, rootdir: str) -> list:
        """Updates the list of test folders"""

        # Clear current displaylist
        self.alltestfolders.clear()

        # Get test folders and test foldernames
        test_folderpath_list = self.filestructure.get_tests(rootdir)
        test_foldername_list = [
            os.path.basename(os.path.normpath(testfolderpath))
            for testfolderpath in test_folderpath_list
        ]

        # Create dict[foldername] = folderpath -> map names to paths
        # Create dict[foldername] = True/False -> map names to if they have been selected
        # Add test foldernames to GUI
        testname_to_testpath = {}
        test_selection_dict = {}
        for idx in range(len(test_foldername_list)):
            testname_to_testpath[test_foldername_list[idx]] = test_folderpath_list[idx]
            test_selection_dict[test_foldername_list[idx]] = False
            self.alltestfolders.addItem(test_foldername_list[idx])

        return testname_to_testpath, test_selection_dict

    # List of all selected test folders --> autoupdates when the program launches
    def get_selected_folders(self) -> list:

        selected_test_folders = []

        # cycle through testfoldername
        for foldername in self.test_selection_dict:
            if self.test_selection_dict[foldername] == True:
                selected_test_folders.append(self.testname_to_testpath[foldername])

        return selected_test_folders

    # Command on single click
    def testfolder_clicked(self, item: QListWidgetItem) -> None:
        """Temporarily displays the test folder when clicked"""
        # print(item.text())

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

        # Get selected test folders
        test_folders = self.get_selected_folders()

        # Get selected test files seperated by test (list of lists)
        analyzed_files = self.filestructure.get_files(test_folders, "Analyzed")
        mpp_files = self.filestructure.get_files(test_folders,"MPP")

        # Update Plots
        self.update_plots(analyzed_files,mpp_files)

    def colorize_list(self):

        # Colorize the list
        for i, key in enumerate(self.test_selection_dict):
            if self.test_selection_dict[key] == True:
                self.alltestfolders.item(i).setBackground(QtCore.Qt.green)
            elif self.test_selection_dict[key] == False:
                self.alltestfolders.item(i).setBackground(QtCore.Qt.white)

    def update_plots(self, analyzed_file_lists: list, mpp_file_lists: list):

        # Flatten file array
        allfiles = []
        for analyzed_file_list_for_given_test in analyzed_file_lists:
            for analyzed_file in analyzed_file_list_for_given_test:
                allfiles.append(analyzed_file)
        
        mppfiles = []
        for mpp_file_list_for_given_test in mpp_file_lists:
            for mpp_file in mpp_file_list_for_given_test:
                mppfiles.append(mpp_file)

        # Cycle through dictionaries for each plot (set in __init__) to get desired parameters
        for key in self.plot_axes_dict:
            self.plot_axes_dict[key].cla()

            yparam = self.plot_y_dict[key]
            xparam = self.plot_x_dict[key]
            axes = self.plot_axes_dict[key]

            # Pass to appropriate plotter to plot on given axes
            if "MPP" in yparam:
                self.grapher.plot_mpps(mppfiles, axes)
            elif type(yparam) != list:
                self.grapher.plot_xy_scalars(allfiles, xparam, yparam, axes)
            else:
                self.grapher.plot_xy2_scalars(allfiles, xparam, yparam, axes)

        # Update canvas
        self.canvas.draw()

    def launch_gui(self) -> None:
        """Launches GUI"""
        # exexcutes the GUI
        app = QApplication(sys.argv)
        app.exec_()
