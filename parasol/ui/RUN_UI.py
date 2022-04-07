import PyQt5
from PyQt5.QtWidgets import QMainWindow, QApplication, QCheckBox, QComboBox
from PyQt5.QtWidgets import QPushButton, QLineEdit
from PyQt5 import QtCore
from PyQt5 import uic
import sys
import os
from datetime import datetime
import yaml

# Import Controller (call load, unload), characterization (know test types), and analysis (check on tests)
from parasol.controller import Controller
from parasol.characterization import Characterization
from parasol.analysis.analysis import Analysis
from parasol.analysis.grapher import Grapher
from parasol.filestructure import FileStructure

from multiprocessing import Process
from threading import Thread

# Set module directory, load yaml preferences
MODULE_DIR = os.path.dirname(__file__)
with open(os.path.join(MODULE_DIR, "..", "hardwareconstants.yaml"), "r") as f:
    defaults = yaml.safe_load(f)["RUN_UI"]  # , Loader=yaml.FullLoader)["relay"]

# Ensure resolution/dpi is correct for UI
if hasattr(QtCore.Qt, "AA_EnableHighDpiScaling"):
    PyQt5.QtWidgets.QApplication.setAttribute(QtCore.Qt.AA_EnableHighDpiScaling, True)

if hasattr(QtCore.Qt, "AA_UseHighDpiPixmaps"):
    PyQt5.QtWidgets.QApplication.setAttribute(QtCore.Qt.AA_UseHighDpiPixmaps, True)

# Multithreading wrapper
def run_async_thread(func):
    """
    Function decorator, intended to make "func" run in a separate thread (asynchronously).

    Arg:
        func (function): function to run in seperate thread
    Returns:
        function: created thread object
    """

    # import modules needed
    from threading import Thread
    from functools import wraps

    # wrapper function
    @wraps(func)
    def async_func(*args, **kwargs):
        func_hl = Thread(target=func, args=args, kwargs=kwargs)
        func_hl.start()
        return func_hl

    return async_func


# _check_test function outside of the class so that we can use multiprocessing on it
def _check_test(jv_paths: list, mpp_paths: list) -> None:
    """
    Process to check test and plot

    Args:
        jv_paths(list[str]): list of paths to JV folders
        mpp_paths(list[str]): list of paths to MPP folders
    """
    # Get analysis and grapher classes
    analysis = Analysis()
    grapher = Grapher()

    # Calculate "Time Elapsed (s)", "FWD Pmp (mW/cm2)", "REV Pmp (mW/cm2)"
    plot_df = analysis.check_test(jv_paths, mpp_paths)

    # Plot "Time Elapsed (s)" vsersus "FWD Pmp (mW/cm2)" and "REV Pmp (mW/cm2)"
    grapher.plot_x_v_ys(
        plot_df, "Time Elapsed (s)", ["FWD Pmp (mW/cm2)", "REV Pmp (mW/cm2)"]
    )


# Main function
class RUN_UI(QMainWindow):
    """Run UI package for PARASOL"""

    def __init__(self) -> None:
        """Initliazes the RUN_UI class"""

        super(RUN_UI, self).__init__()

        # Initialize packages
        self.controller = Controller()
        self.characterization = Characterization()
        self.analysis = Analysis()
        self.grapher = Grapher()
        self.filestructure = FileStructure()

        # Make blank variables for the start date
        self.startdate1 = None
        self.startdate2 = None
        self.startdate3 = None
        self.startdate4 = None
        self.startdate5 = None
        self.startdate6 = None

        # Make blank variables for saveloc
        self.savedir1 = None
        self.savedir2 = None
        self.savedir3 = None
        self.savedir4 = None
        self.savedir5 = None
        self.savedir6 = None

        # Load the ui file
        ui_path = os.path.join(MODULE_DIR, "RUN_UI2.ui")
        uic.loadUi(ui_path, self)
        self.show()

        # Get checkBoxes / modules ran
        self.checkbox1 = self.findChild(QCheckBox, "checkBox_1")
        self.checkbox2 = self.findChild(QCheckBox, "checkBox_2")
        self.checkbox3 = self.findChild(QCheckBox, "checkBox_3")
        self.checkbox4 = self.findChild(QCheckBox, "checkBox_4")
        self.checkbox5 = self.findChild(QCheckBox, "checkBox_5")
        self.checkbox6 = self.findChild(QCheckBox, "checkBox_6")
        self.checkbox7 = self.findChild(QCheckBox, "checkBox_7")
        self.checkbox8 = self.findChild(QCheckBox, "checkBox_8")
        self.checkbox9 = self.findChild(QCheckBox, "checkBox_9")
        self.checkbox10 = self.findChild(QCheckBox, "checkBox_10")
        self.checkbox11 = self.findChild(QCheckBox, "checkBox_11")
        self.checkbox12 = self.findChild(QCheckBox, "checkBox_12")
        self.checkbox13 = self.findChild(QCheckBox, "checkBox_13")
        self.checkbox14 = self.findChild(QCheckBox, "checkBox_14")
        self.checkbox15 = self.findChild(QCheckBox, "checkBox_15")
        self.checkbox16 = self.findChild(QCheckBox, "checkBox_16")
        self.checkbox17 = self.findChild(QCheckBox, "checkBox_17")
        self.checkbox18 = self.findChild(QCheckBox, "checkBox_18")
        self.checkbox19 = self.findChild(QCheckBox, "checkBox_19")
        self.checkbox20 = self.findChild(QCheckBox, "checkBox_20")
        self.checkbox21 = self.findChild(QCheckBox, "checkBox_21")
        self.checkbox22 = self.findChild(QCheckBox, "checkBox_22")
        self.checkbox23 = self.findChild(QCheckBox, "checkBox_23")
        self.checkbox24 = self.findChild(QCheckBox, "checkBox_24")

        # Get Names
        self.name1 = self.findChild(QLineEdit, "NameInput_1")
        self.name2 = self.findChild(QLineEdit, "NameInput_2")
        self.name3 = self.findChild(QLineEdit, "NameInput_3")
        self.name4 = self.findChild(QLineEdit, "NameInput_4")
        self.name5 = self.findChild(QLineEdit, "NameInput_5")
        self.name6 = self.findChild(QLineEdit, "NameInput_6")

        # Get Areas
        self.area1 = self.findChild(QLineEdit, "AreaInput_1")
        self.area2 = self.findChild(QLineEdit, "AreaInput_2")
        self.area3 = self.findChild(QLineEdit, "AreaInput_3")
        self.area4 = self.findChild(QLineEdit, "AreaInput_4")
        self.area5 = self.findChild(QLineEdit, "AreaInput_5")
        self.area6 = self.findChild(QLineEdit, "AreaInput_6")

        self.area1.setText(str(defaults["area"]))
        self.area2.setText(str(defaults["area"]))
        self.area3.setText(str(defaults["area"]))
        self.area4.setText(str(defaults["area"]))
        self.area5.setText(str(defaults["area"]))
        self.area6.setText(str(defaults["area"]))

        # get JV frequency and MPP frequency
        self.jvfrequency1 = self.findChild(QLineEdit, "JVFrequencyInput_1")
        self.jvfrequency2 = self.findChild(QLineEdit, "JVFrequencyInput_2")
        self.jvfrequency3 = self.findChild(QLineEdit, "JVFrequencyInput_3")
        self.jvfrequency4 = self.findChild(QLineEdit, "JVFrequencyInput_4")
        self.jvfrequency5 = self.findChild(QLineEdit, "JVFrequencyInput_5")
        self.jvfrequency6 = self.findChild(QLineEdit, "JVFrequencyInput_6")

        self.jvfrequency1.setText(str(defaults["jv_frequency"]))
        self.jvfrequency2.setText(str(defaults["jv_frequency"]))
        self.jvfrequency3.setText(str(defaults["jv_frequency"]))
        self.jvfrequency4.setText(str(defaults["jv_frequency"]))
        self.jvfrequency5.setText(str(defaults["jv_frequency"]))
        self.jvfrequency6.setText(str(defaults["jv_frequency"]))

        self.mppfrequency1 = self.findChild(QLineEdit, "MPPFrequencyInput_1")
        self.mppfrequency2 = self.findChild(QLineEdit, "MPPFrequencyInput_2")
        self.mppfrequency3 = self.findChild(QLineEdit, "MPPFrequencyInput_3")
        self.mppfrequency4 = self.findChild(QLineEdit, "MPPFrequencyInput_4")
        self.mppfrequency5 = self.findChild(QLineEdit, "MPPFrequencyInput_5")
        self.mppfrequency6 = self.findChild(QLineEdit, "MPPFrequencyInput_6")

        self.mppfrequency1.setText(str(defaults["mpp_frequency"]))
        self.mppfrequency2.setText(str(defaults["mpp_frequency"]))
        self.mppfrequency3.setText(str(defaults["mpp_frequency"]))
        self.mppfrequency4.setText(str(defaults["mpp_frequency"]))
        self.mppfrequency5.setText(str(defaults["mpp_frequency"]))
        self.mppfrequency6.setText(str(defaults["mpp_frequency"]))

        # Get JV min voltage, max voltage, and voltage step size
        self.vmin1 = self.findChild(QLineEdit, "VminInput_1")
        self.vmin2 = self.findChild(QLineEdit, "VminInput_2")
        self.vmin3 = self.findChild(QLineEdit, "VminInput_3")
        self.vmin4 = self.findChild(QLineEdit, "VminInput_4")
        self.vmin5 = self.findChild(QLineEdit, "VminInput_5")
        self.vmin6 = self.findChild(QLineEdit, "VminInput_6")

        self.vmin1.setText(str(defaults["v_min"]))
        self.vmin2.setText(str(defaults["v_min"]))
        self.vmin3.setText(str(defaults["v_min"]))
        self.vmin4.setText(str(defaults["v_min"]))
        self.vmin5.setText(str(defaults["v_min"]))
        self.vmin6.setText(str(defaults["v_min"]))

        self.vmax1 = self.findChild(QLineEdit, "VmaxInput_1")
        self.vmax2 = self.findChild(QLineEdit, "VmaxInput_2")
        self.vmax3 = self.findChild(QLineEdit, "VmaxInput_3")
        self.vmax4 = self.findChild(QLineEdit, "VmaxInput_4")
        self.vmax5 = self.findChild(QLineEdit, "VmaxInput_5")
        self.vmax6 = self.findChild(QLineEdit, "VmaxInput_6")

        self.vmax1.setText(str(defaults["v_max"]))
        self.vmax2.setText(str(defaults["v_max"]))
        self.vmax3.setText(str(defaults["v_max"]))
        self.vmax4.setText(str(defaults["v_max"]))
        self.vmax5.setText(str(defaults["v_max"]))
        self.vmax6.setText(str(defaults["v_max"]))

        self.vstep1 = self.findChild(QLineEdit, "VstepsInput_1")
        self.vstep2 = self.findChild(QLineEdit, "VstepsInput_2")
        self.vstep3 = self.findChild(QLineEdit, "VstepsInput_3")
        self.vstep4 = self.findChild(QLineEdit, "VstepsInput_4")
        self.vstep5 = self.findChild(QLineEdit, "VstepsInput_5")
        self.vstep6 = self.findChild(QLineEdit, "VstepsInput_6")

        self.vstep1.setText(str(defaults["v_steps"]))
        self.vstep2.setText(str(defaults["v_steps"]))
        self.vstep3.setText(str(defaults["v_steps"]))
        self.vstep4.setText(str(defaults["v_steps"]))
        self.vstep5.setText(str(defaults["v_steps"]))
        self.vstep6.setText(str(defaults["v_steps"]))

        # Get MPP mode, clear, feed in options from characteriations
        self.mppmode1 = self.findChild(QComboBox, "MPPModeBox_1")
        self.mppmode2 = self.findChild(QComboBox, "MPPModeBox_2")
        self.mppmode3 = self.findChild(QComboBox, "MPPModeBox_3")
        self.mppmode4 = self.findChild(QComboBox, "MPPModeBox_4")
        self.mppmode5 = self.findChild(QComboBox, "MPPModeBox_5")
        self.mppmode6 = self.findChild(QComboBox, "MPPModeBox_6")

        self.mppmode1.clear()
        self.mppmode2.clear()
        self.mppmode3.clear()
        self.mppmode4.clear()
        self.mppmode5.clear()
        self.mppmode6.clear()

        for item in self.characterization.mpp_options:
            self.mppmode1.addItem(self.characterization.mpp_options[item])
            self.mppmode2.addItem(self.characterization.mpp_options[item])
            self.mppmode3.addItem(self.characterization.mpp_options[item])
            self.mppmode4.addItem(self.characterization.mpp_options[item])
            self.mppmode5.addItem(self.characterization.mpp_options[item])
            self.mppmode6.addItem(self.characterization.mpp_options[item])

        self.mppmode1.setCurrentIndex(int(defaults["mpp_mode"]))
        self.mppmode2.setCurrentIndex(int(defaults["mpp_mode"]))
        self.mppmode3.setCurrentIndex(int(defaults["mpp_mode"]))
        self.mppmode4.setCurrentIndex(int(defaults["mpp_mode"]))
        self.mppmode5.setCurrentIndex(int(defaults["mpp_mode"]))
        self.mppmode6.setCurrentIndex(int(defaults["mpp_mode"]))

        # Get JV mode, clear, feed in options from characteriations
        self.jvmode1 = self.findChild(QComboBox, "JVModeBox_1")
        self.jvmode2 = self.findChild(QComboBox, "JVModeBox_2")
        self.jvmode3 = self.findChild(QComboBox, "JVModeBox_3")
        self.jvmode4 = self.findChild(QComboBox, "JVModeBox_4")
        self.jvmode5 = self.findChild(QComboBox, "JVModeBox_5")
        self.jvmode6 = self.findChild(QComboBox, "JVModeBox_6")

        self.jvmode1.clear()
        self.jvmode2.clear()
        self.jvmode3.clear()
        self.jvmode4.clear()
        self.jvmode5.clear()
        self.jvmode6.clear()

        for item in self.characterization.jv_options:
            self.jvmode1.addItem(self.characterization.jv_options[item])
            self.jvmode2.addItem(self.characterization.jv_options[item])
            self.jvmode3.addItem(self.characterization.jv_options[item])
            self.jvmode4.addItem(self.characterization.jv_options[item])
            self.jvmode5.addItem(self.characterization.jv_options[item])
            self.jvmode6.addItem(self.characterization.jv_options[item])

        self.jvmode1.setCurrentIndex(int(defaults["jv_mode"]))
        self.jvmode2.setCurrentIndex(int(defaults["jv_mode"]))
        self.jvmode3.setCurrentIndex(int(defaults["jv_mode"]))
        self.jvmode4.setCurrentIndex(int(defaults["jv_mode"]))
        self.jvmode5.setCurrentIndex(int(defaults["jv_mode"]))
        self.jvmode6.setCurrentIndex(int(defaults["jv_mode"]))

        # Get load button & connect to function
        self.loadbutton1 = self.findChild(QPushButton, "LoadButton_1")
        self.loadbutton2 = self.findChild(QPushButton, "LoadButton_2")
        self.loadbutton3 = self.findChild(QPushButton, "LoadButton_3")
        self.loadbutton4 = self.findChild(QPushButton, "LoadButton_4")
        self.loadbutton5 = self.findChild(QPushButton, "LoadButton_5")
        self.loadbutton6 = self.findChild(QPushButton, "LoadButton_6")

        self.loadbutton1.clicked.connect(self.load1)
        self.loadbutton2.clicked.connect(self.load2)
        self.loadbutton3.clicked.connect(self.load3)
        self.loadbutton4.clicked.connect(self.load4)
        self.loadbutton5.clicked.connect(self.load5)
        self.loadbutton6.clicked.connect(self.load6)

        self.loadbutton1.setEnabled(True)
        self.loadbutton2.setEnabled(True)
        self.loadbutton3.setEnabled(True)
        self.loadbutton4.setEnabled(True)
        self.loadbutton5.setEnabled(True)
        self.loadbutton6.setEnabled(True)

        # Get unload button & connect to function
        self.unloadbutton1 = self.findChild(QPushButton, "UnLoadButton_1")
        self.unloadbutton2 = self.findChild(QPushButton, "UnLoadButton_2")
        self.unloadbutton3 = self.findChild(QPushButton, "UnLoadButton_3")
        self.unloadbutton4 = self.findChild(QPushButton, "UnLoadButton_4")
        self.unloadbutton5 = self.findChild(QPushButton, "UnLoadButton_5")
        self.unloadbutton6 = self.findChild(QPushButton, "UnLoadButton_6")

        self.unloadbutton1.clicked.connect(self.unload1)
        self.unloadbutton2.clicked.connect(self.unload2)
        self.unloadbutton3.clicked.connect(self.unload3)
        self.unloadbutton4.clicked.connect(self.unload4)
        self.unloadbutton5.clicked.connect(self.unload5)
        self.unloadbutton6.clicked.connect(self.unload6)

        self.unloadbutton1.setEnabled(False)
        self.unloadbutton2.setEnabled(False)
        self.unloadbutton3.setEnabled(False)
        self.unloadbutton4.setEnabled(False)
        self.unloadbutton5.setEnabled(False)
        self.unloadbutton6.setEnabled(False)

        # Get check test button & connect to function
        self.checktestbutton1 = self.findChild(QPushButton, "CheckTestButton_1")
        self.checktestbutton2 = self.findChild(QPushButton, "CheckTestButton_2")
        self.checktestbutton3 = self.findChild(QPushButton, "CheckTestButton_3")
        self.checktestbutton4 = self.findChild(QPushButton, "CheckTestButton_4")
        self.checktestbutton5 = self.findChild(QPushButton, "CheckTestButton_5")
        self.checktestbutton6 = self.findChild(QPushButton, "CheckTestButton_6")

        self.checktestbutton1.clicked.connect(self.checktest1)
        self.checktestbutton2.clicked.connect(self.checktest2)
        self.checktestbutton3.clicked.connect(self.checktest3)
        self.checktestbutton4.clicked.connect(self.checktest4)
        self.checktestbutton5.clicked.connect(self.checktest5)
        self.checktestbutton6.clicked.connect(self.checktest6)

        self.checktestbutton1.setEnabled(False)
        self.checktestbutton2.setEnabled(False)
        self.checktestbutton3.setEnabled(False)
        self.checktestbutton4.setEnabled(False)
        self.checktestbutton5.setEnabled(False)
        self.checktestbutton6.setEnabled(False)

        # Get the check module orientation button & connect to function
        self.checkorientationbutton1 = self.findChild(
            QPushButton, "CheckOrientationButton_1"
        )
        self.checkorientationbutton2 = self.findChild(
            QPushButton, "CheckOrientationButton_2"
        )
        self.checkorientationbutton3 = self.findChild(
            QPushButton, "CheckOrientationButton_3"
        )
        self.checkorientationbutton4 = self.findChild(
            QPushButton, "CheckOrientationButton_4"
        )
        self.checkorientationbutton5 = self.findChild(
            QPushButton, "CheckOrientationButton_5"
        )
        self.checkorientationbutton6 = self.findChild(
            QPushButton, "CheckOrientationButton_6"
        )

        self.checkorientationbutton1.clicked.connect(self.checkorientation1)
        self.checkorientationbutton2.clicked.connect(self.checkorientation2)
        self.checkorientationbutton3.clicked.connect(self.checkorientation3)
        self.checkorientationbutton4.clicked.connect(self.checkorientation4)
        self.checkorientationbutton5.clicked.connect(self.checkorientation5)
        self.checkorientationbutton6.clicked.connect(self.checkorientation6)

        self.checkorientationbutton1.setEnabled(True)
        self.checkorientationbutton2.setEnabled(True)
        self.checkorientationbutton3.setEnabled(True)
        self.checkorientationbutton4.setEnabled(True)
        self.checkorientationbutton5.setEnabled(True)
        self.checkorientationbutton6.setEnabled(True)

        # Create GUI
        self.launch_gui()

    def update_loaded_modules(self) -> None:
        """Uses checkboxes in UI to get list of active modules"""

        # Set all variables to None
        modules1 = [None] * 4
        modules2 = [None] * 4
        modules3 = [None] * 4
        modules4 = [None] * 4
        modules5 = [None] * 4
        modules6 = [None] * 4

        # Cycle through and check if we have module, if so add number to module#
        if self.checkbox1.isChecked():
            modules1[0] = 1
        if self.checkbox2.isChecked():
            modules1[1] = 2
        if self.checkbox3.isChecked():
            modules1[2] = 3
        if self.checkbox4.isChecked():
            modules1[3] = 4

        if self.checkbox5.isChecked():
            modules2[0] = 5
        if self.checkbox6.isChecked():
            modules2[1] = 6
        if self.checkbox7.isChecked():
            modules2[2] = 7
        if self.checkbox8.isChecked():
            modules2[3] = 8

        if self.checkbox9.isChecked():
            modules3[0] = 9
        if self.checkbox10.isChecked():
            modules3[1] = 10
        if self.checkbox11.isChecked():
            modules3[2] = 11
        if self.checkbox12.isChecked():
            modules3[3] = 12

        if self.checkbox13.isChecked():
            modules4[0] = 13
        if self.checkbox14.isChecked():
            modules4[1] = 14
        if self.checkbox15.isChecked():
            modules4[2] = 15
        if self.checkbox16.isChecked():
            modules4[3] = 16

        if self.checkbox17.isChecked():
            modules5[0] = 17
        if self.checkbox18.isChecked():
            modules5[1] = 18
        if self.checkbox19.isChecked():
            modules5[2] = 19
        if self.checkbox20.isChecked():
            modules5[3] = 20

        if self.checkbox21.isChecked():
            modules6[0] = 21
        if self.checkbox22.isChecked():
            modules6[1] = 22
        if self.checkbox23.isChecked():
            modules6[2] = 23
        if self.checkbox24.isChecked():
            modules6[3] = 24

        # Throw out None values so that list is just loaded modules
        self.module1 = [i for i in modules1 if i is not None]
        self.module2 = [i for i in modules2 if i is not None]
        self.module3 = [i for i in modules3 if i is not None]
        self.module4 = [i for i in modules4 if i is not None]
        self.module5 = [i for i in modules5 if i is not None]
        self.module6 = [i for i in modules6 if i is not None]

    def update_dictionaries(self) -> None:
        """Updates dictionaries[stringid] with data from the UI"""

        # Make Dictionary for each channel
        self.strings = {}
        self.strings[1] = {
            "start_date": self.startdate1,
            "_savedir": self.savedir1,
            "name": self.name1.text(),
            "area": self.area1.text(),
            "module_channels": self.module1,
            "jv": {
                "mode": self.jvmode1.currentIndex(),
                "interval": self.jvfrequency1.text(),
                "vmin": self.vmin1.text(),
                "vmax": self.vmax1.text(),
                "steps": self.vstep1.text(),
            },
            "mpp": {
                "mode": self.mppmode1.currentIndex(),
                "interval": self.mppfrequency1.text(),
            },
        }

        self.strings[2] = {
            "start_date": self.startdate2,
            "_savedir": self.savedir2,
            "name": self.name2.text(),
            "area": self.area2.text(),
            "module_channels": self.module2,
            "jv": {
                "mode": self.jvmode2.currentIndex(),
                "interval": self.jvfrequency2.text(),
                "vmin": self.vmin2.text(),
                "vmax": self.vmax2.text(),
                "steps": self.vstep2.text(),
            },
            "mpp": {
                "mode": self.mppmode2.currentIndex(),
                "interval": self.mppfrequency2.text(),
            },
        }

        self.strings[3] = {
            "start_date": self.startdate3,
            "_savedir": self.savedir3,
            "name": self.name3.text(),
            "area": self.area3.text(),
            "module_channels": self.module3,
            "jv": {
                "mode": self.jvmode3.currentIndex(),
                "interval": self.jvfrequency3.text(),
                "vmin": self.vmin3.text(),
                "vmax": self.vmax3.text(),
                "steps": self.vstep3.text(),
            },
            "mpp": {
                "mode": self.mppmode3.currentIndex(),
                "interval": self.mppfrequency3.text(),
            },
        }

        self.strings[4] = {
            "start_date": self.startdate4,
            "_savedir": self.savedir4,
            "name": self.name4.text(),
            "area": self.area4.text(),
            "module_channels": self.module4,
            "jv": {
                "mode": self.jvmode4.currentIndex(),
                "interval": self.jvfrequency4.text(),
                "vmin": self.vmin4.text(),
                "vmax": self.vmax4.text(),
                "steps": self.vstep4.text(),
            },
            "mpp": {
                "mode": self.mppmode4.currentIndex(),
                "interval": self.mppfrequency4.text(),
            },
        }

        self.strings[5] = {
            "start_date": self.startdate5,
            "_savedir": self.savedir5,
            "name": self.name5.text(),
            "area": self.area5.text(),
            "module_channels": self.module5,
            "jv": {
                "mode": self.jvmode5.currentIndex(),
                "interval": self.jvfrequency5.text(),
                "vmin": self.vmin5.text(),
                "vmax": self.vmax5.text(),
                "steps": self.vstep5.text(),
            },
            "mpp": {
                "mode": self.mppmode5.currentIndex(),
                "interval": self.mppfrequency5.text(),
            },
        }

        self.strings[6] = {
            "start_date": self.startdate6,
            "_savedir": self.savedir6,
            "name": self.name6.text(),
            "area": self.area6.text(),
            "module_channels": self.module6,
            "jv": {
                "mode": self.jvmode6.currentIndex(),
                "interval": self.jvfrequency6.text(),
                "vmin": self.vmin6.text(),
                "vmax": self.vmax6.text(),
                "steps": self.vstep6.text(),
            },
            "mpp": {
                "mode": self.mppmode6.currentIndex(),
                "interval": self.mppfrequency6.text(),
            },
        }

    def lock_values(self, stringid: int) -> None:
        """Locks values for the string subsection of the UI

        Args:
            stringid(int): string id
        """

        # Call subfunctions to lock all changeable values in string subsection of the UI as well as unlock 'unload' and 'check test' buttons
        if stringid == 1:
            self.lock_value1()
        elif stringid == 2:
            self.lock_value2()
        elif stringid == 3:
            self.lock_value3()
        elif stringid == 4:
            self.lock_value4()
        elif stringid == 5:
            self.lock_value5()
        elif stringid == 6:
            self.lock_value6()

    def unlock_values(self, stringid: int) -> None:
        """Unlocks values for the string subsection of the UI

        Args:
            stringid (int): string id
        """

        # Call subfunctions to unlock all changeable values in string subsection of the UI as well as lock 'unload' and 'check test' buttons
        if stringid == 1:
            self.unlock_value1()
        elif stringid == 2:
            self.unlock_value2()
        elif stringid == 3:
            self.unlock_value3()
        elif stringid == 4:
            self.unlock_value4()
        elif stringid == 5:
            self.unlock_value5()
        elif stringid == 6:
            self.unlock_value6()

    def load(self, stringid: int) -> None:
        """Loads the module using the command in controller.py and data from the dictionaries/UI

        Args:
            stringid (int): string id
        """

        # Notify User
        print("Loading string: " + str(stringid))

        # Update Values
        self.update_loaded_modules()
        self.update_dictionaries()

        # Grab id, dictionary
        id = int(stringid)
        d = self.strings[id]

        # Grab values from dictionary
        start_date = d["start_date"]
        name = d["name"]
        area = float(d["area"])
        jv_mode = int(d["jv"]["mode"])
        module_channels = d["module_channels"]
        jv_interval = float(d["jv"]["interval"])
        jv_vmin = float(d["jv"]["vmin"])
        jv_vmax = float(d["jv"]["vmax"])
        jv_steps = int(d["jv"]["steps"])
        mpp_mode = int(d["mpp"]["mode"])
        mpp_interval = float(d["mpp"]["interval"])

        if 1 <= id <= 6:

            # Call Load String from controller
            updated_name = self.controller.load_string(
                id,
                start_date,
                name,
                area,
                jv_mode,
                mpp_mode,
                module_channels,
                jv_interval,
                mpp_interval,
                jv_vmin,
                jv_vmax,
                jv_steps,
            )

            # reconstruct savedir from name and date
            updated_savedir = self.filestructure.get_test_folder(
                start_date, updated_name
            )

            # Update saveloc, name
            if id == 1:
                self.name1.setText(updated_name)
                self.savedir1 = updated_savedir
            elif id == 2:
                self.name2.setText(updated_name)
                self.savedir2 = updated_savedir
            elif id == 3:
                self.name3.setText(updated_name)
                self.savedir3 = updated_savedir
            elif id == 4:
                self.name4.setText(updated_name)
                self.savedir4 = updated_savedir
            elif id == 5:
                self.name5.setText(updated_name)
                self.savedir5 = updated_savedir
            elif id == 6:
                self.name6.setText(updated_name)
                self.savedir6 = updated_savedir

            # alter dictionary
            d["_savedir"] = updated_savedir
            d["name"] = updated_name

            # lock values
            self.lock_values(id)

        else:
            print("Please check the boxes for the devices you would like to load.")

    # Run unload in a new thread to not interfere with other measurments active
    @run_async_thread
    def unload(self, stringid: int) -> None:
        """Unloads the module using the command in controller.py and the stringid

        Args:
            stringid (int): string id
        """

        # Notify User
        print("Unloading string: " + str(stringid))

        # Get ID
        id = int(stringid)

        # Unlock user inputs
        self.unlock_values(id)

        # Call Unload String from controller
        self.controller.unload_string(id)

        # get dictionary
        d = self.strings[id]

        # Manage save dir
        saveloc = None
        if id == 1:
            self.savedir1 = saveloc
            d["_savedir"] = saveloc
        elif id == 2:
            self.savedir2 = saveloc
            d["_savedir"] = saveloc
        elif id == 3:
            self.savedir3 = saveloc
            d["_savedir"] = saveloc
        elif id == 4:
            self.savedir4 = saveloc
            d["_savedir"] = saveloc
        elif id == 5:
            self.savedir5 = saveloc
            d["_savedir"] = saveloc
        elif id == 6:
            self.savedir6 = saveloc
            d["_savedir"] = saveloc

        # Let user know its complete
        print("String " + str(stringid) + " unload successful")

    def checktest(self, stringid: int) -> None:
        """Checks the test using the string id with the commands in analysis.py & grapher.py

        Args:
            stringid (int): string id
        """

        print("Checking string: " + str(stringid))

        # Get useful info from wave
        id = int(stringid)
        module_channels = self.strings[id]["module_channels"]

        # Create folderpaths to folders that contain data
        jv_paths = []
        for module in module_channels:
            jvfolder = self.filestructure.get_jv_folder(
                self.strings[id]["start_date"], self.strings[id]["name"], module
            )
            jv_paths.append(jvfolder)
        mpp_paths = [
            self.filestructure.get_mpp_folder(
                self.strings[id]["start_date"], self.strings[id]["name"]
            )
        ]

        # Start process to anlayze and plot data in new process --> requires multiple cores
        Process(target=_check_test, args=(jv_paths, mpp_paths)).start()

    def checkorientation(self, stringid: int) -> None:
        """Checks Orientaion of wiring to see if its is correct for the string

        Args:
            stringid (int): string number
        """

        # Update Values
        self.update_loaded_modules()
        self.update_dictionaries()

        # Grab modules from dictionary
        d = self.strings[stringid]
        module_channels = d["module_channels"]

        self.controller.load_check_orientation(module_channels)

    ################################################################################
    # Buttons / Duplicated Functions
    ################################################################################

    def checktest1(self) -> None:
        """Checks test 1"""
        self.checktest(1)

    def checktest2(self) -> None:
        """Checks test 2"""
        self.checktest(2)

    def checktest3(self) -> None:
        """Checks test 3"""
        self.checktest(3)

    def checktest4(self) -> None:
        """Checks test 4"""
        self.checktest(4)

    def checktest5(self) -> None:
        """Checs test 5"""
        self.checktest(5)

    def checktest6(self) -> None:
        """Checks test 6"""
        self.checktest(6)

    # Lock Values for Editing

    def lock_value1(self) -> None:
        """Locks all changeable objects for test 1"""

        self.name1.setEnabled(False)
        self.area1.setEnabled(False)
        self.jvmode1.setEnabled(False)
        self.jvfrequency1.setEnabled(False)
        self.vmin1.setEnabled(False)
        self.vmax1.setEnabled(False)
        self.vstep1.setEnabled(False)
        self.mppmode1.setEnabled(False)
        self.mppfrequency1.setEnabled(False)
        self.checkbox1.setEnabled(False)
        self.checkbox2.setEnabled(False)
        self.checkbox3.setEnabled(False)
        self.checkbox4.setEnabled(False)

        self.loadbutton1.setEnabled(False)
        self.unloadbutton1.setEnabled(True)
        self.checktestbutton1.setEnabled(True)
        self.checkorientationbutton1.setEnabled(False)

    def lock_value2(self) -> None:
        """Locks all changeable objects for test 2"""

        self.name2.setEnabled(False)
        self.area2.setEnabled(False)
        self.jvmode2.setEnabled(False)
        self.jvfrequency2.setEnabled(False)
        self.vmin2.setEnabled(False)
        self.vmax2.setEnabled(False)
        self.vstep2.setEnabled(False)
        self.mppmode2.setEnabled(False)
        self.mppfrequency2.setEnabled(False)
        self.checkbox5.setEnabled(False)
        self.checkbox6.setEnabled(False)
        self.checkbox7.setEnabled(False)
        self.checkbox8.setEnabled(False)

        self.loadbutton2.setEnabled(False)
        self.unloadbutton2.setEnabled(True)
        self.checktestbutton2.setEnabled(True)
        self.checkorientationbutton2.setEnabled(False)

    def lock_value3(self) -> None:
        """Locks all changeable objects for test 3"""

        self.name3.setEnabled(False)
        self.area3.setEnabled(False)
        self.jvmode3.setEnabled(False)
        self.jvfrequency3.setEnabled(False)
        self.vmin3.setEnabled(False)
        self.vmax3.setEnabled(False)
        self.vstep3.setEnabled(False)
        self.mppmode3.setEnabled(False)
        self.mppfrequency3.setEnabled(False)
        self.checkbox9.setEnabled(False)
        self.checkbox10.setEnabled(False)
        self.checkbox11.setEnabled(False)
        self.checkbox12.setEnabled(False)

        self.loadbutton3.setEnabled(False)
        self.unloadbutton3.setEnabled(True)
        self.checktestbutton3.setEnabled(True)
        self.checkorientationbutton3.setEnabled(False)

    def lock_value4(self) -> None:
        """Locks all changeable objects for test 4"""

        self.name4.setEnabled(False)
        self.area4.setEnabled(False)
        self.jvmode4.setEnabled(False)
        self.jvfrequency4.setEnabled(False)
        self.vmin4.setEnabled(False)
        self.vmax4.setEnabled(False)
        self.vstep4.setEnabled(False)
        self.mppmode4.setEnabled(False)
        self.mppfrequency4.setEnabled(False)
        self.checkbox13.setEnabled(False)
        self.checkbox14.setEnabled(False)
        self.checkbox15.setEnabled(False)
        self.checkbox16.setEnabled(False)

        self.loadbutton4.setEnabled(False)
        self.unloadbutton4.setEnabled(True)
        self.checktestbutton4.setEnabled(True)
        self.checkorientationbutton4.setEnabled(False)

    def lock_value5(self) -> None:
        """Locks all changeable objects for test 5"""

        self.name5.setEnabled(False)
        self.area5.setEnabled(False)
        self.jvmode5.setEnabled(False)
        self.jvfrequency5.setEnabled(False)
        self.vmin5.setEnabled(False)
        self.vmax5.setEnabled(False)
        self.vstep5.setEnabled(False)
        self.mppmode5.setEnabled(False)
        self.mppfrequency5.setEnabled(False)
        self.checkbox17.setEnabled(False)
        self.checkbox18.setEnabled(False)
        self.checkbox19.setEnabled(False)
        self.checkbox20.setEnabled(False)

        self.loadbutton5.setEnabled(False)
        self.unloadbutton5.setEnabled(True)
        self.checktestbutton5.setEnabled(True)
        self.checkorientationbutton5.setEnabled(False)

    def lock_value6(self) -> None:
        """Locks all changeable objects for test 6"""

        self.name6.setEnabled(False)
        self.area6.setEnabled(False)
        self.jvmode6.setEnabled(False)
        self.jvfrequency6.setEnabled(False)
        self.vmin6.setEnabled(False)
        self.vmax6.setEnabled(False)
        self.vstep6.setEnabled(False)
        self.mppmode6.setEnabled(False)
        self.mppfrequency6.setEnabled(False)
        self.checkbox21.setEnabled(False)
        self.checkbox22.setEnabled(False)
        self.checkbox23.setEnabled(False)
        self.checkbox24.setEnabled(False)

        self.loadbutton6.setEnabled(False)
        self.unloadbutton6.setEnabled(True)
        self.checktestbutton6.setEnabled(True)
        self.checkorientationbutton6.setEnabled(False)

    # Unlock Values For Editing

    def unlock_value1(self) -> None:
        """Unlocks all changeable objects for test 1"""

        self.name1.setEnabled(True)
        self.area1.setEnabled(True)
        self.jvmode1.setEnabled(True)
        self.jvfrequency1.setEnabled(True)
        self.vmin1.setEnabled(True)
        self.vmax1.setEnabled(True)
        self.vstep1.setEnabled(True)
        self.mppmode1.setEnabled(True)
        self.mppfrequency1.setEnabled(True)
        self.checkbox1.setEnabled(True)
        self.checkbox2.setEnabled(True)
        self.checkbox3.setEnabled(True)
        self.checkbox4.setEnabled(True)

        self.loadbutton1.setEnabled(True)
        self.unloadbutton1.setEnabled(False)
        self.checktestbutton1.setEnabled(False)
        self.checkorientationbutton1.setEnabled(True)

    def unlock_value2(self) -> None:
        """Unlocks all changeable objects for test 2"""

        self.name2.setEnabled(True)
        self.area2.setEnabled(True)
        self.jvmode2.setEnabled(True)
        self.jvfrequency2.setEnabled(True)
        self.vmin2.setEnabled(True)
        self.vmax2.setEnabled(True)
        self.vstep2.setEnabled(True)
        self.mppmode2.setEnabled(True)
        self.mppfrequency2.setEnabled(True)
        self.checkbox5.setEnabled(True)
        self.checkbox6.setEnabled(True)
        self.checkbox7.setEnabled(True)
        self.checkbox8.setEnabled(True)

        self.loadbutton2.setEnabled(True)
        self.unloadbutton2.setEnabled(False)
        self.checktestbutton2.setEnabled(False)
        self.checkorientationbutton2.setEnabled(True)

    def unlock_value3(self) -> None:
        """Unlocks all changeable objects for test 3"""

        self.name3.setEnabled(True)
        self.area3.setEnabled(True)
        self.jvmode3.setEnabled(True)
        self.jvfrequency3.setEnabled(True)
        self.vmin3.setEnabled(True)
        self.vmax3.setEnabled(True)
        self.vstep3.setEnabled(True)
        self.mppmode3.setEnabled(True)
        self.mppfrequency3.setEnabled(True)
        self.checkbox9.setEnabled(True)
        self.checkbox10.setEnabled(True)
        self.checkbox11.setEnabled(True)
        self.checkbox12.setEnabled(True)

        self.loadbutton3.setEnabled(True)
        self.unloadbutton3.setEnabled(False)
        self.checktestbutton3.setEnabled(False)
        self.checkorientationbutton3.setEnabled(True)

    def unlock_value4(self) -> None:
        """Unlocks all changeable objects for test 4"""

        self.name4.setEnabled(True)
        self.area4.setEnabled(True)
        self.jvmode4.setEnabled(True)
        self.jvfrequency4.setEnabled(True)
        self.vmin4.setEnabled(True)
        self.vmax4.setEnabled(True)
        self.vstep4.setEnabled(True)
        self.mppmode4.setEnabled(True)
        self.mppfrequency4.setEnabled(True)
        self.checkbox13.setEnabled(True)
        self.checkbox14.setEnabled(True)
        self.checkbox15.setEnabled(True)
        self.checkbox16.setEnabled(True)

        self.loadbutton4.setEnabled(True)
        self.unloadbutton4.setEnabled(False)
        self.checktestbutton4.setEnabled(False)
        self.checkorientationbutton4.setEnabled(True)

    def unlock_value5(self) -> None:
        """Unlocks all changeable objects for test 5"""

        self.name5.setEnabled(True)
        self.area5.setEnabled(True)
        self.jvmode5.setEnabled(True)
        self.jvfrequency5.setEnabled(True)
        self.vmin5.setEnabled(True)
        self.vmax5.setEnabled(True)
        self.vstep5.setEnabled(True)
        self.mppmode5.setEnabled(True)
        self.mppfrequency5.setEnabled(True)
        self.checkbox17.setEnabled(True)
        self.checkbox18.setEnabled(True)
        self.checkbox19.setEnabled(True)
        self.checkbox20.setEnabled(True)

        self.loadbutton5.setEnabled(True)
        self.unloadbutton5.setEnabled(False)
        self.checktestbutton5.setEnabled(False)
        self.checkorientationbutton5.setEnabled(True)

    def unlock_value6(self) -> None:
        """Unlocks all changeable objects for test 6"""

        self.name6.setEnabled(True)
        self.area6.setEnabled(True)
        self.jvmode6.setEnabled(True)
        self.jvfrequency6.setEnabled(True)
        self.vmin6.setEnabled(True)
        self.vmax6.setEnabled(True)
        self.vstep6.setEnabled(True)
        self.mppmode6.setEnabled(True)
        self.mppfrequency6.setEnabled(True)
        self.checkbox21.setEnabled(True)
        self.checkbox22.setEnabled(True)
        self.checkbox23.setEnabled(True)
        self.checkbox24.setEnabled(True)

        self.loadbutton6.setEnabled(True)
        self.unloadbutton6.setEnabled(False)
        self.checktestbutton6.setEnabled(False)
        self.checkorientationbutton6.setEnabled(True)

    # Load Buttons

    def load1(self) -> None:
        """Loads test 1"""
        self.startdate1 = datetime.now().strftime("x%Y%m%d")
        self.load(1)

    def load2(self) -> None:
        """Loads test 2"""
        self.startdate2 = datetime.now().strftime("x%Y%m%d")
        self.load(2)

    def load3(self) -> None:
        """Loads test 3"""
        self.startdate3 = datetime.now().strftime("x%Y%m%d")
        self.load(3)

    def load4(self) -> None:
        """Loads test 4"""
        self.startdate4 = datetime.now().strftime("x%Y%m%d")
        self.load(4)

    def load5(self) -> None:
        """Loads test 5"""
        self.startdate5 = datetime.now().strftime("x%Y%m%d")
        self.load(5)

    def load6(self) -> None:
        """Loads test 6"""
        self.startdate6 = datetime.now().strftime("x%Y%m%d")
        self.load(6)

    # Unload Buttons

    def unload1(self) -> None:
        """Unloads test 1"""
        self.unload(1)

    def unload2(self) -> None:
        """Unloads test 2"""
        self.unload(2)

    def unload3(self) -> None:
        """Unloads test 3"""
        self.unload(3)

    def unload4(self) -> None:
        """Unloads test 4"""
        self.unload(4)

    def unload5(self) -> None:
        """Unloads test 5"""
        self.unload(5)

    def unload6(self) -> None:
        """Unloads test 6"""
        self.unload(6)

    # Checktest Buttons

    def checktest1(self) -> None:
        """Checks test 1"""
        self.checktest(1)

    def checktest2(self) -> None:
        """Checks test 2"""
        self.checktest(2)

    def checktest3(self) -> None:
        """Checks test 3"""
        self.checktest(3)

    def checktest4(self) -> None:
        """Checks test 4"""
        self.checktest(4)

    def checktest5(self) -> None:
        """Checks test 5"""
        self.checktest(5)

    def checktest6(self) -> None:
        """Checks test 6"""
        self.checktest(6)

    # Checkorientation Buttons

    def checkorientation1(self) -> None:
        """Checks orientation of test 1"""
        self.checkorientation(1)

    def checkorientation2(self) -> None:
        """Checks orientation of test 2"""
        self.checkorientation(2)

    def checkorientation3(self) -> None:
        """Checks orientation of test 3"""
        self.checkorientation(3)

    def checkorientation4(self) -> None:
        """Checks orientation of test 4"""
        self.checkorientation(4)

    def checkorientation5(self) -> None:
        """Checks orientation of test 5"""
        self.checkorientation(5)

    def checkorientation6(self) -> None:
        """Checks orientation of test 6"""
        self.checkorientation(6)

    # Launches GUI

    def launch_gui(self) -> None:
        """Launches GUI"""

        # exexcutes the GUI
        app = QApplication(sys.argv)
        app.exec_()
