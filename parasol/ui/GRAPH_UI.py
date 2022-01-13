import PyQt5
from PyQt5.QtWidgets import QMainWindow, QApplication, QCheckBox, QComboBox
from PyQt5.QtWidgets import (
    QPushButton,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QOpenGLWidget,
    QVBoxLayout,
)
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
import matplotlib.pyplot as plt

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
        ui_path = os.path.join(MODULE_DIR, "GRAPH_UI2.ui")
        uic.loadUi(ui_path, self)

        # Load all Test Folders, clear list, add events on click and doubleclick
        self.alltestfolders = self.findChild(QListWidget, "AllTestFolders")
        self.alltestfolders.clear()
        self.alltestfolders.itemClicked.connect(self.testfolder_clicked)
        self.alltestfolders.itemDoubleClicked.connect(self.testfolder_doubleclicked)
        # Update list of tests, create dict[Foldername] = True/False for plotting and dict[Foldername] = Folderpath
        self.testname_to_testpath, self.test_selection_dict = self.update_test_folders(rootdir)

        # Loads all the graphics
        # xstart = 260
        # xspacer = 10
        # ystart = 0
        # yspacer = 10
        width = 270
        height = 180

        # # Get main loadout for appending the graphs to
        self.layout = self.findChild(PyQt5.QtWidgets.QVBoxLayout, "verticalLayout")
        
        self.fwd_jsc_fig = plt.figure(figsize =(width,height))
        self.fwd_jsc_canvas = FigureCanvas(self.fwd_jsc_fig)
        
        self.layout.addWidget(self.fwd_jsc_canvas)

        # self._jsc_ax = self.fwd_jsc_canvas.figure.subplots()
        # self.fwd_jsc_plot = None
        # self._jsc_ax.plot([1],[2])


        #self._fwd_jsc = self.fwd_jsc_canvas.figure.subplots()
        #self._fwd_jsc_trace, = self._fwd_jsc.plot([],[]) 
        
        
        #self.fwd_jsc_canvas.draw()        

        # self.fwd_jsc_graphics = self.findChild(PyQt5.QtWidgets.QOpenGLWidget, "FWD_Jsc")
        # self.fwd_voc_graphics = self.findChild(PyQt5.QtWidgets.QOpenGLWidget, "FWD_Voc")
        # self.fwd_ff_graphics = self.findChild(PyQt5.QtWidgets.QOpenGLWidget, "FWD_FF")
        # self.fwd_pce_graphics = self.findChild(PyQt5.QtWidgets.QOpenGLWidget, "FWD_PCE")

        # self.rev_jsc_graphics = self.findChild(PyQt5.QtWidgets.QOpenGLWidget, "REV_Jsc")
        # self.rev_voc_graphics = self.findChild(PyQt5.QtWidgets.QOpenGLWidget, "REV_Voc")
        # self.rev_ff_graphics = self.findChild(PyQt5.QtWidgets.QOpenGLWidget, "REV_FF")
        # self.rev_pce_graphics = self.findChild(PyQt5.QtWidgets.QOpenGLWidget, "REV_PCE")

        # self.rser_graphics = self.findChild(PyQt5.QtWidgets.QOpenGLWidget, "Rser")
        # self.rsh_graphics = self.findChild(PyQt5.QtWidgets.QOpenGLWidget, "Rsh")
        # self.rch_graphics = self.findChild(PyQt5.QtWidgets.QOpenGLWidget, "Rch")
        # self.mpp_graphics = self.findChild(PyQt5.QtWidgets.QOpenGLWidget, "mppt")

        # show
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
                
        allfiles = []
        for analyzed_file_list_for_given_test in analyzed_file_lists:
            for analyzed_file in analyzed_file_list_for_given_test:
                allfiles.append(analyzed_file)

        #fig, ax = plt.subplots(1, figsize=(3, 2))
        # if self.fwd_jsc_plot:
        #     self.fwd_jsc_plot.remove()
        self.fwd_jsc_fig.clear()
        self.fwd_jsc_ax = self.fwd_jsc_fig.add_subplot(111)

        self.fwd_jsc_plot = self.grapher.plot_xy_scalars(
            allfiles,
            self.grapher.variable_dict["Time Elapsed"],
            self.grapher.variable_dict["FWD Jsc"],
            self.fwd_jsc_ax 
            )

        self.fwd_jsc_canvas.draw()

        # Cycle through paramfiles
        # fwd_jsc_fig = self.grapher.plot_xy_scalars(
        #     allfiles,
        #     self.grapher.variable_dict["Time Elapsed"],
        #     self.grapher.variable_dict["FWD Jsc"] )
        # fwd_voc_fig = self.grapher.plot_xy_scalars(
        #     allfiles,
        #     self.grapher.variable_dict["Time Elapsed"],
        #     self.grapher.variable_dict["FWD Voc"] )
        # fwd_ff_fig = self.grapher.plot_xy_scalars(
        #     allfiles,
        #     self.grapher.variable_dict["Time Elapsed"],
        #     self.grapher.variable_dict["FWD FF"] )
        # fwd_pce_fig = self.grapher.plot_xy_scalars(
        #     allfiles,
        #     self.grapher.variable_dict["Time Elapsed"],
        #     self.grapher.variable_dict["FWD PCE"] )
        
        # rev_jsc_fig = self.grapher.plot_xy_scalars(
        #     allfiles,
        #     self.grapher.variable_dict["Time Elapsed"],
        #     self.grapher.variable_dict["REV Jsc"] )
        # rev_voc_fig = self.grapher.plot_xy_scalars(
        #     allfiles,
        #     self.grapher.variable_dict["Time Elapsed"],
        #     self.grapher.variable_dict["REV Voc"] )
        # rev_ff_fig = self.grapher.plot_xy_scalars(
        #     allfiles,
        #     self.grapher.variable_dict["Time Elapsed"],
        #     self.grapher.variable_dict["REV FF"] )
        # rev_pce_fig = self.grapher.plot_xy_scalars(
        #     allfiles,
        #     self.grapher.variable_dict["Time Elapsed"],
        #     self.grapher.variable_dict["REV PCE"] )

        # rser_fig = self.grapher.plot_xy2_scalars(
        #     allfiles,
        #     self.grapher.variable_dict["Time Elapsed"],
        #     [self.grapher.variable_dict["FWD Rs"], self.grapher.variable_dict["REV Rs"]]
        #     )
        # rsh_fig = self.grapher.plot_xy2_scalars(
        #     allfiles,
        #     self.grapher.variable_dict["Time Elapsed"],
        #     [self.grapher.variable_dict["FWD Rsh"], self.grapher.variable_dict["REV Rsh"]]
        #     )
        # rch_fig = self.grapher.plot_xy2_scalars(
        #     allfiles,
        #     self.grapher.variable_dict["Time Elapsed"],
        #     [self.grapher.variable_dict["FWD Rch"], self.grapher.variable_dict["REV Rch"]]
        #     )

        # mppt_fig = self.grapher.plot_xy_scalars(
        #     allfiles,
        #     self.grapher.variable_dict["Time Elapsed"],
        #     self.grapher.variable_dict["REV PCE"] )
        

        #self.fwd_jsc_fig = fwd_pce_fig
        #self.fwd_jsc_canvas = FigureCanvas(self.fwd_jsc_fig)

        #self.fwd_jsc_fig.canvas.draw()
        # self.fwd_jsc_fig.show()
        #self.fwd_jsc_canvas.draw()
        
        

    def launch_gui(self) -> None:
        """Launches GUI"""
        # exexcutes the GUI
        app = QApplication(sys.argv)
        app.exec_()
