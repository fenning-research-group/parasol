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

        # Set matplotlib params:
        # mplfont = {
        #     'weight' : 'light',
        #     'size' : 10
        # }
        # matplotlib.rc('font', **mplfont)
        mpl.rcParams['font.size'] = 8

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

        # Load all Test Folders, clear list, add events on click and doubleclick
        self.alltestfolders = self.findChild(QListWidget, "AllTestFolders")
        self.alltestfolders.clear()
        self.alltestfolders.itemClicked.connect(self.testfolder_clicked)
        self.alltestfolders.itemDoubleClicked.connect(self.testfolder_doubleclicked)
        
        # Update list of tests, create dict[Foldername] = True/False for plotting and dict[Foldername] = Folderpath
        self.testname_to_testpath, self.test_selection_dict = self.update_test_folders(rootdir)

        # Loads all the graphics
        nrows = 3
        ncols = 4
        dpival = 50
        xloc = 270
        yloc = 0

        # Get main loadout for appending the Canvas to
        self.layout = self.findChild(PyQt5.QtWidgets.QFrame, "frame")
        
        # Create a figure with several subplots, devide up axes
        self.figure, self.axes = plt.subplots(ncols, nrows, dpi = dpival, tight_layout = True)
        
        self.plot_axes_dict = {
            1 : self.axes[0][0],
            2 : self.axes[1][0],
            3 : self.axes[2][0],
            4 : self.axes[3][0],
            5 : self.axes[0][1],
            6 : self.axes[1][1],
            7 : self.axes[2][1],
            8 : self.axes[3][1],
            9 : self.axes[0][2],
            10 : self.axes[1][2],
            11 : self.axes[2][2],
            12 : self.axes[3][2],
        }

        self.plot_y_dict = {
            1 : self.grapher.variable_dict["FWD Jsc"],
            2 : self.grapher.variable_dict["FWD Voc"],
            3 : self.grapher.variable_dict["FWD FF"],
            4: self.grapher.variable_dict["FWD PCE"],
            5: self.grapher.variable_dict["REV Jsc"],
            6 : self.grapher.variable_dict["REV Voc"],
            7: self.grapher.variable_dict["REV FF"],
            8: self.grapher.variable_dict["REV PCE"],
            9: [self.grapher.variable_dict["FWD Rs"], self.grapher.variable_dict["REV Rs"]],
            10: [self.grapher.variable_dict["FWD Rsh"], self.grapher.variable_dict["REV Rsh"]],
            11: [self.grapher.variable_dict["FWD Rch"], self.grapher.variable_dict["REV Rch"]],
            12: [self.grapher.variable_dict["FWD Rch"], self.grapher.variable_dict["REV Rch"]],
            #12: "MPPT",
        }

        self.plot_x_dict = {
            1 : self.grapher.variable_dict["Time Elapsed"],
            2 : self.grapher.variable_dict["Time Elapsed"],
            3 : self.grapher.variable_dict["Time Elapsed"],
            4 : self.grapher.variable_dict["Time Elapsed"],
            5 : self.grapher.variable_dict["Time Elapsed"],
            6 : self.grapher.variable_dict["Time Elapsed"],
            7 : self.grapher.variable_dict["Time Elapsed"],
            8 : self.grapher.variable_dict["Time Elapsed"],
            9 : self.grapher.variable_dict["Time Elapsed"],
            10 : self.grapher.variable_dict["Time Elapsed"],
            11 : self.grapher.variable_dict["Time Elapsed"],
            12 : self.grapher.variable_dict["Time Elapsed"],
        }
        
        # Place figure in canvas, control resize policy, resize, place on UI, and set location
        self.canvas = FigureCanvas(self.figure)
        self.canvas.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)        
        self.canvas.updateGeometry()
        self.canvas.resize(850,770)
        self.canvas.setParent(self.layout)
        self.canvas.move(xloc,yloc)

        # customize axes
        for key in self.plot_axes_dict:
            self.plot_axes_dict[key].tick_params(direction = 'in', labelsize = 'small')


        # show UI
        self.show()

        # Create GUI
        self.launch_gui()

    # List of all test folders --> autoupdates when the program launches
    def update_test_folders(self, rootdir: str)->list:
        """Updates the list of test folders"""

        # Clear current displaylist
        self.alltestfolders.clear()

        # Get test folders and test foldernames
        test_folderpath_list = self.filestructure.get_tests(rootdir)
        test_foldername_list = [os.path.basename(os.path.normpath(testfolderpath)) for testfolderpath in test_folderpath_list]
        
        # Create dict[foldername] = folderpath -> map names to paths
        # Create dict[foldername] = True/False -> map names to if they have been selected
        # Add test foldernames to GUI
        testname_to_testpath= {}
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
        #print(item.text())

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
        
        # Update Plots
        self.update_plots(analyzed_files)

    def colorize_list(self):

        # Colorize the list
        for i, key in enumerate(self.test_selection_dict):
            if self.test_selection_dict[key] == True:
                self.alltestfolders.item(i).setBackground(QtCore.Qt.green)
            elif self.test_selection_dict[key] == False:
                self.alltestfolders.item(i).setBackground(QtCore.Qt.white)


    def update_plots(self, analyzed_file_lists : list):

        # Flatten file array        
        allfiles = []
        for analyzed_file_list_for_given_test in analyzed_file_lists:
            for analyzed_file in analyzed_file_list_for_given_test:
                allfiles.append(analyzed_file)

        # Cycle through dictionaries for each plot (set in __init__) to get desired parameters
        for key in self.plot_axes_dict:
            self.plot_axes_dict[key].cla()

            yparam = self.plot_y_dict[key]
            xparam = self.plot_x_dict[key]
            axes = self.plot_axes_dict[key]

            # Pass to appropriate plotter to plot on given axes
            if type(yparam) != list:
                self.grapher.plot_xy_scalars(allfiles,xparam,yparam, axes)
            else:
               self.grapher.plot_xy2_scalars(allfiles,xparam,yparam,axes)

        # Update canvas
        self.canvas.draw()

              
        

    def launch_gui(self) -> None:
        """Launches GUI"""
        # exexcutes the GUI
        app = QApplication(sys.argv)
        app.exec_()
