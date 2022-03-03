import PyQt5
from PyQt5.QtWidgets import (
    QMainWindow,
    QApplication,
    QPushButton,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QSizePolicy,
    QFileDialog,
)
import PyQt5.QtGui
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
import matplotlib.pyplot as plt
import matplotlib as mpl
import yaml

from PyQt5 import QtCore
from PyQt5 import uic
import sys
import os
import numpy as np


from parasol.filestructure import FileStructure
from parasol.analysis.grapher import Grapher


# Set module directory
MODULE_DIR = os.path.dirname(__file__)
with open(os.path.join(MODULE_DIR, "UI_defaults.yaml"), "r") as f:
    defaults = yaml.safe_load(f)["GRAPH_UI"]  # , Loader=yaml.FullLoader)["GRAPH_UI"]

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
        fontsize = 8
        markersize = 1.0
        dpival = 50

        # Load the ui file
        ui_path = os.path.join(MODULE_DIR, "GRAPH_UI.ui")
        uic.loadUi(ui_path, self)

        # Load default root dir, set in UI
        self.rootdir = self.findChild(QLineEdit, "rootdir")
        # self.rootdir.setText(self.filestructure.get_root_dir())
        self.rootdir.setText(defaults["root_dir"])
        if os.path.exists(self.rootdir.text()) == False:
            self.rootdir.setText("")

        # Manage rootdir button
        self.setrootdir = self.findChild(QPushButton, "setrootdir")
        self.setrootdir.clicked.connect(self.setrootdir_clicked)

        # Manage savefigure button
        self.savefigure = self.findChild(QPushButton, "savefigure")
        self.savefigure.clicked.connect(self.savefigure_clicked)
        self.savedir = defaults["save_dir"]
        if os.path.exists(self.savedir) == False:
            self.savedir = ""

        # Load testfolderdisplay list widget, clear list, add events on click and doubleclick
        self.alltestfolders = self.findChild(QListWidget, "AllTestFolders")
        self.alltestfolders.clear()
        self.alltestfolders.itemClicked.connect(self.testfolder_clicked)
        self.alltestfolders.itemDoubleClicked.connect(self.testfolder_doubleclicked)

        # Update list of tests, create dict[Foldername] = True/False for plotting and dict[Foldername] = Folderpath if rootdir exsists, else let user change
        if os.path.exists(self.rootdir.text()):
            (
                self.testname_to_testpath,
                self.test_selection_dict,
            ) = self.update_test_folders(self.rootdir.text())
        else:
            self.test_name_to_testpath = {}
            self.test_selection_dict = {}

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
        self.canvas.resize(1600, 900)
        mpl.rcParams["font.size"] = fontsize
        mpl.rcParams["lines.markersize"] = markersize
        for key in self.plot_axes_dict:
            self.plot_axes_dict[key].tick_params(direction="in", labelsize="small")
            self.plot_axes_dict[key].xaxis.label.set_size(fontsize)
            self.plot_axes_dict[key].yaxis.label.set_size(fontsize)

        # show UI
        self.show()

        # Create GUI
        self.launch_gui()

    def update_test_folders(self, rootdir: str) -> list:
        """Updates the list of test folders

        Args:
            rootdir[str]: root directory

        Returns
            dict : dictionary[testfoldername] : testpath
            dict : dictionary[testfoldername] : True/False for plotting
        """

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
        # Create diuct[foldername] = color -> map names to colors
        # Add test foldernames to GUI
        testname_to_testpath = {}
        test_selection_dict = {}

        for idx in range(len(test_foldername_list)):
            testname_to_testpath[test_foldername_list[idx]] = test_folderpath_list[idx]
            test_selection_dict[test_foldername_list[idx]] = False
            self.alltestfolders.addItem(test_foldername_list[idx])

        return testname_to_testpath, test_selection_dict

    def get_selected_folders(self) -> list:
        """
        Gets list of selected folder paths

        Returns:
            list[str] : paths to test folders selected

        """

        selected_test_folders = []

        # cycle through testfoldername
        for foldername in self.test_selection_dict:
            if self.test_selection_dict[foldername] == True:
                selected_test_folders.append(self.testname_to_testpath[foldername])

        return selected_test_folders

    # Command on single click
    def testfolder_clicked(self, item: QListWidgetItem) -> None:
        """Temporarily displays the test folder when clicked"""
        # for now --> do nothing.

    def testfolder_doubleclicked(self, item: QListWidgetItem) -> None:
        """Permanantley displays the test folder when double clicked

        Args:
        item[QListWidgetItem] : item selected
        """

        # Change status of selected test folder
        if self.test_selection_dict[str(item.text())] == False:
            self.test_selection_dict[str(item.text())] = True
        elif self.test_selection_dict[str(item.text())] == True:
            self.test_selection_dict[str(item.text())] = False

        # Color input values using dictionary[testfolder] = color
        self.test_colors = self.colorize_list()

        # Get selected test folders
        test_folders = self.get_selected_folders()

        # Get selected test files seperated by test (list of lists)
        analyzed_files = self.filestructure.get_files(test_folders, "Analyzed")
        mpp_files = self.filestructure.get_files(test_folders, "MPP")

        # Update Plots
        self.update_plots(analyzed_files, mpp_files, test_folders)

    def setrootdir_clicked(self) -> None:
        """Manages setting root directory on button click"""
        file = QFileDialog.getExistingDirectory(
            self, "Select Directory", self.rootdir.text()
        )
        self.rootdir.setText(file)

        # Update list of tests, create dict[Foldername] = True/False for plotting and dict[Foldername] = Folderpath
        (
            self.testname_to_testpath,
            self.test_selection_dict,
        ) = self.update_test_folders(file)

    def savefigure_clicked(self) -> None:
        """Manages saving figure on button click"""

        fig2 = self.figure
        # ax = fig2.axes[10]
        # ax.legend("test")

        file = QFileDialog.getSaveFileName(
            self, "Save File", self.savedir, "PNG (*.png)"
        )
        if file is not None:
            fig2.savefig(file[0])
            self.savedir = os.path.dirname(file[0])

    def colorize_list(self) -> None:
        """
        Sets the colors for items clicked and creates dictionary for plots to be set to same color

        Returns:
            dict: dictionary[testfolderpath] : hexcolor

        """
        # Cylcle through tests, count # selected, append to list
        numtests = 0
        selected_tests = []
        for i, key in enumerate(self.test_selection_dict):
            if self.test_selection_dict[key] == True:
                numtests += 1
                selected_tests.append(key)
            elif self.test_selection_dict[key] == False:
                numtests += 0

        # Create color map dict to hold color for each test
        colors = plt.cm.viridis(np.linspace(0, 1, numtests))
        test_color_dict = {}
        for idx, selected_test in enumerate(selected_tests):
            test_color_dict[self.testname_to_testpath[selected_test]] = str(
                mpl.colors.to_hex(colors[idx])
            )  # colors[idx]

        # Colorize the list
        for i, key in enumerate(self.test_selection_dict):
            if self.test_selection_dict[key] == True:
                # Get colors and set item to same color as graph
                rgbh = test_color_dict[self.testname_to_testpath[key]]
                self.alltestfolders.item(i).setBackground(PyQt5.QtGui.QColor(rgbh))
            elif self.test_selection_dict[key] == False:
                # Set white
                self.alltestfolders.item(i).setBackground(QtCore.Qt.white)

        return test_color_dict

    def update_plots(
        self, analyzed_file_lists: list, mpp_file_lists: list, test_folder_list: list
    ):
        """
        Updates plots

        Args:
            analyzed_files_lists (list[list[str]]): list of analyzed file paths seperated by test
            mpp_files_lists (list[list[str]]): list of mpp file paths seperated by test
            test_folder_list (list[str]): list of test folder paths
        """
        # Cycle through dictionaries for each plot (set in __init__) to get desired parameters
        for key in self.plot_axes_dict:

            # Clear plot
            self.plot_axes_dict[key].cla()

            # Get parameters
            yparam = self.plot_y_dict[key]
            xparam = self.plot_x_dict[key]
            axes = self.plot_axes_dict[key]

            # Cycle through each Test, plot
            for index, test_folder in enumerate(test_folder_list):

                # Get colors
                rgbh = self.test_colors[test_folder]

                # Pass to appropriate plotter to plot on given axes
                if "MPP" in yparam:
                    self.grapher.plot_mpps(
                        mppfiles=mpp_file_lists[index], ax=axes, c=rgbh
                    )
                elif type(yparam) != list:
                    self.grapher.plot_xy_scalars(
                        paramfiles=analyzed_file_lists[index],
                        x=xparam,
                        y=yparam,
                        ax=axes,
                        c=rgbh,
                    )
                else:
                    self.grapher.plot_xy2_scalars(
                        paramfiles=analyzed_file_lists[index],
                        x=xparam,
                        ys=yparam,
                        ax=axes,
                        c=rgbh,
                    )

        # Update canvas
        self.canvas.draw()

    def launch_gui(self) -> None:
        """Launches GUI"""
        # exexcutes the GUI
        app = QApplication(sys.argv)
        app.exec_()
