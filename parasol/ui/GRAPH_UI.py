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
with open(os.path.join(MODULE_DIR, "..", "hardwareconstants.yaml"), "r") as f:
    defaults = yaml.safe_load(f)["GRAPH_UI"]

# Ensure resolution/dpi is correct for UI
if hasattr(QtCore.Qt, "AA_EnableHighDpiScaling"):
    PyQt5.QtWidgets.QApplication.setAttribute(QtCore.Qt.AA_EnableHighDpiScaling, True)

if hasattr(QtCore.Qt, "AA_UseHighDpiPixmaps"):
    PyQt5.QtWidgets.QApplication.setAttribute(QtCore.Qt.AA_UseHighDpiPixmaps, True)


def GRAPHER():
    """Create GRAPH UI window"""

    class GRAPH_UI(QMainWindow):
        """Graph UI package for PARASOL"""

        def __init__(self) -> None:
            """Initliazes the GRAPH_UI class"""

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

            # Load the UI file
            ui_path = os.path.join(MODULE_DIR, "GRAPH_UI.ui")
            uic.loadUi(ui_path, self)

            # Make dictionary to hold y parameter names
            self.plot_y_dict = {
                1: defaults["y1"],
                2: defaults["y2"],
                3: defaults["y3"],
                4: defaults["y4"],
                5: defaults["y5"],
                6: defaults["y6"],
                7: defaults["y7"],
                8: defaults["y8"],
                9: defaults["y9"],
                10: defaults["y10"],
                11: defaults["y11"],
                12: defaults["y12"],
            }

            # Make dictionary to hold x parameter names
            self.plot_x_dict = {
                1: defaults["x1"],
                2: defaults["x2"],
                3: defaults["x3"],
                4: defaults["x4"],
                5: defaults["x5"],
                6: defaults["x6"],
                7: defaults["x7"],
                8: defaults["x8"],
                9: defaults["x9"],
                10: defaults["x10"],
                11: defaults["x11"],
                12: defaults["x12"],
            }

            # Get file paths
            self.characterization_dir_loc = (
                self.filestructure.get_characterization_dir()
            )
            self.rootdir = self.findChild(QLineEdit, "rootdir")
            self.rootdir.setText(self.characterization_dir_loc)
            if os.path.exists(self.rootdir.text()) == False:
                self.rootdir.setText("")
            self.analysis_dir_loc = self.filestructure.get_analysis_dir()
            self.savedir = self.analysis_dir_loc
            if os.path.exists(self.savedir) == False:
                self.savedir = ""

            # Manage rootdir button
            self.setrootdir = self.findChild(QPushButton, "setrootdir")
            self.setrootdir.clicked.connect(self.setrootdir_clicked)

            # Manage savefigure button
            self.savefigure = self.findChild(QPushButton, "savefigure")
            self.savefigure.clicked.connect(self.savefigure_clicked)

            # Load testfolderdisplay list widget, clear list, add events on click and doubleclick
            self.alltestfolders = self.findChild(QListWidget, "AllTestFolders")
            self.alltestfolders.clear()
            self.alltestfolders.itemClicked.connect(self.testfolder_clicked)
            self.alltestfolders.itemDoubleClicked.connect(self.testfolder_doubleclicked)

            # Update list of tests, create dictionary[Foldername] = True/False for plotting and dict[Foldername] = Folderpath if rootdir exsists, else let user change
            if os.path.exists(self.rootdir.text()):
                (
                    self.testname_to_testpath,
                    self.test_selection_dict,
                ) = self.update_test_folders(self.rootdir.text())
            else:
                self.test_name_to_testpath = {}
                self.test_selection_dict = {}

            # Get layout to append graphs
            self.layout = self.findChild(PyQt5.QtWidgets.QFrame, "graphframe")

            # Create figure with several subplots, devide up axes
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

            # Place figure in canvas, control resize policy, resize, place on UI, and set location
            self.canvas = FigureCanvas(self.figure)
            self.canvas.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
            self.canvas.updateGeometry()
            self.canvas.setParent(self.layout)

            # Make plots work!
            self.canvas.resize(1600, 900)
            mpl.rcParams["font.size"] = fontsize
            mpl.rcParams["lines.markersize"] = markersize
            for key in self.plot_axes_dict:
                self.plot_axes_dict[key].tick_params(direction="in", labelsize="small")
                self.plot_axes_dict[key].xaxis.label.set_size(fontsize)
                self.plot_axes_dict[key].yaxis.label.set_size(fontsize)

            # Show UI
            self.show()

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

            # Create dictionary [foldername] = folderpath -> map names to paths
            # Create dictionary [foldername] = True/False -> map names to if they have been selected
            testname_to_testpath = {}
            test_selection_dict = {}
            for idx in range(len(test_foldername_list)):
                testname_to_testpath[test_foldername_list[idx]] = test_folderpath_list[
                    idx
                ]
                test_selection_dict[test_foldername_list[idx]] = False
                self.alltestfolders.addItem(test_foldername_list[idx])

            return testname_to_testpath, test_selection_dict

        def get_selected_folders(self) -> list:
            """
            Gets list of selected folder paths

            Returns:
                list[str] : paths to test folders selected

            """

            # cycle through testfoldername, if selected, change list index to True
            selected_test_folders = []
            for foldername in self.test_selection_dict:
                if self.test_selection_dict[foldername] == True:
                    selected_test_folders.append(self.testname_to_testpath[foldername])

            return selected_test_folders

        def testfolder_clicked(self, item: QListWidgetItem) -> None:
            """Does Nothing"""
            # Do nothing on single click

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
            analyzed_files = self.filestructure.get_files(test_folders, "Analyzed") #TODO: this can throw error
            mpp_files = self.filestructure.get_files(test_folders, "MPP")

            self.update_plots(analyzed_files, mpp_files, test_folders)

        def setrootdir_clicked(self) -> None:
            """Manages setting root directory on button click"""

            # Prompts dialoge to let user select root directory
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

            # Create new figure
            fig2 = self.figure

            # Ask for save directory, save if given, else ignore
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

            # Create list of selected tests
            selected_tests = []
            for i, key in enumerate(self.test_selection_dict):
                if self.test_selection_dict[key] == True:
                    selected_tests.append(key)

            # Create color map dict to hold color for each test
            colors = plt.cm.viridis(np.linspace(0, 1, len(selected_tests)))
            test_color_dict = {}
            for idx, selected_test in enumerate(selected_tests):
                test_color_dict[self.testname_to_testpath[selected_test]] = str(
                    mpl.colors.to_hex(colors[idx])
                )

            # Colorize the list in the file browser. This will behave as a key
            for i, key in enumerate(self.test_selection_dict):

                # If dev is selected, get colors and set item to same color as graph
                if self.test_selection_dict[key] == True:
                    rgbh = test_color_dict[self.testname_to_testpath[key]]
                    self.alltestfolders.item(i).setBackground(PyQt5.QtGui.QColor(rgbh))

                # Otherwise set it to white
                elif self.test_selection_dict[key] == False:
                    self.alltestfolders.item(i).setBackground(QtCore.Qt.white)

            return test_color_dict

        def update_plots(
            self,
            analyzed_file_lists: list,
            mpp_file_lists: list,
            test_folder_list: list,
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

                # Cycle through each test and plot
                for index, test_folder in enumerate(test_folder_list):

                    # Get colors
                    rgbh = self.test_colors[test_folder]

                    # Pass to appropriate plotter to plot on given axes
                    if "MPPT MPP (mW/cm2)" in yparam:
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

    # Create application (required for widget)
    app = QApplication(sys.argv)

    # Create UI, which is a widget
    window = GRAPH_UI()

    # Start the application
    app.exec_()
