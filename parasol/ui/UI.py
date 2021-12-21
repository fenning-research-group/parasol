import PyQt5

from PyQt5.QtWidgets import QMainWindow, QApplication, QCheckBox, QComboBox
from PyQt5.QtWidgets import QPushButton, QLineEdit
from PyQt5 import QtCore

from PyQt5 import uic
import sys
import os

from parasol.controller import Controller

# get directry of this file
MODULE_DIR = os.path.dirname(__file__)

# Ensure resolution/dpi is correct
if hasattr(QtCore.Qt, "AA_EnableHighDpiScaling"):
    PyQt5.QtWidgets.QApplication.setAttribute(QtCore.Qt.AA_EnableHighDpiScaling, True)

if hasattr(QtCore.Qt, "AA_UseHighDpiPixmaps"):
    PyQt5.QtWidgets.QApplication.setAttribute(QtCore.Qt.AA_UseHighDpiPixmaps, True)


class PARASOL_UI(QMainWindow):
    """
    Launches PARASOL_UI.ui & passes variables to controller
    """

    def __init__(self):
        super(PARASOL_UI, self).__init__()

        # Initialize Controller
        self.controller = Controller()

        # Load the ui file
        ui_path = os.path.join(MODULE_DIR, "PARASOL_UI.ui")
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

        # get JV frequency and MPP frequency
        self.jvfrequency1 = self.findChild(QLineEdit, "JVFrequencyInput_1")
        self.jvfrequency2 = self.findChild(QLineEdit, "JVFrequencyInput_2")
        self.jvfrequency3 = self.findChild(QLineEdit, "JVFrequencyInput_3")
        self.jvfrequency4 = self.findChild(QLineEdit, "JVFrequencyInput_4")
        self.jvfrequency5 = self.findChild(QLineEdit, "JVFrequencyInput_5")
        self.jvfrequency6 = self.findChild(QLineEdit, "JVFrequencyInput_6")

        self.mppfrequency1 = self.findChild(QLineEdit, "MPPFrequencyInput_1")
        self.mppfrequency2 = self.findChild(QLineEdit, "MPPFrequencyInput_2")
        self.mppfrequency3 = self.findChild(QLineEdit, "MPPFrequencyInput_3")
        self.mppfrequency4 = self.findChild(QLineEdit, "MPPFrequencyInput_4")
        self.mppfrequency5 = self.findChild(QLineEdit, "MPPFrequencyInput_5")
        self.mppfrequency6 = self.findChild(QLineEdit, "MPPFrequencyInput_6")

        # Get JV min voltage, max voltage, and voltage step size
        self.vmin1 = self.findChild(QLineEdit, "VminInput_1")
        self.vmin2 = self.findChild(QLineEdit, "VminInput_2")
        self.vmin3 = self.findChild(QLineEdit, "VminInput_3")
        self.vmin4 = self.findChild(QLineEdit, "VminInput_4")
        self.vmin5 = self.findChild(QLineEdit, "VminInput_5")
        self.vmin6 = self.findChild(QLineEdit, "VminInput_6")

        self.vmax1 = self.findChild(QLineEdit, "VmaxInput_1")
        self.vmax2 = self.findChild(QLineEdit, "VmaxInput_2")
        self.vmax3 = self.findChild(QLineEdit, "VmaxInput_3")
        self.vmax4 = self.findChild(QLineEdit, "VmaxInput_4")
        self.vmax5 = self.findChild(QLineEdit, "VmaxInput_5")
        self.vmax6 = self.findChild(QLineEdit, "VmaxInput_6")

        self.vstep1 = self.findChild(QLineEdit, "VstepsInput_1")
        self.vstep2 = self.findChild(QLineEdit, "VstepsInput_2")
        self.vstep3 = self.findChild(QLineEdit, "VstepsInput_3")
        self.vstep4 = self.findChild(QLineEdit, "VstepsInput_4")
        self.vstep5 = self.findChild(QLineEdit, "VstepsInput_5")
        self.vstep6 = self.findChild(QLineEdit, "VstepsInput_6")

        # Get MPP mode
        self.mppmode1 = self.findChild(QComboBox, "MPPModeBox_1")
        self.mppmode2 = self.findChild(QComboBox, "MPPModeBox_2")
        self.mppmode3 = self.findChild(QComboBox, "MPPModeBox_3")
        self.mppmode4 = self.findChild(QComboBox, "MPPModeBox_4")
        self.mppmode5 = self.findChild(QComboBox, "MPPModeBox_5")
        self.mppmode6 = self.findChild(QComboBox, "MPPModeBox_6")

        # Get JV mode button
        self.jvmode1 = self.findChild(QComboBox, "JVModeBox_1")
        self.jvmode2 = self.findChild(QComboBox, "JVModeBox_2")
        self.jvmode3 = self.findChild(QComboBox, "JVModeBox_3")
        self.jvmode4 = self.findChild(QComboBox, "JVModeBox_4")
        self.jvmode5 = self.findChild(QComboBox, "JVModeBox_5")
        self.jvmode6 = self.findChild(QComboBox, "JVModeBox_6")

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

        # Create GUI
        self.Launch_GUI()

    def update_loaded_modules(self):
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

    def update_dictionaries(self):
        """Updates dictionaries[string id num] with data from the UI"""
        self.strings = {}
        # Make Dictionary for each channel
        self.strings[1] = {
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

    def lock_values(self, stringid):
        """Locks values for the string subsection of the UI"""
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

    def unlock_values(self, stringid):
        """Unlocks values for the string subsection of the UI"""
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

    def load(self, stringid):
        """Loads the module using the command in controller.py and data from the dictionaries/UI"""
        # Notify User
        print("Loading string: " + str(stringid))

        # Update Values
        self.update_loaded_modules()
        self.update_dictionaries()

        # Grab id, dictionary
        id = int(stringid)
        d = self.strings[id]

        # Lock Values
        self.lock_values(id)

        # Grab values from dictionary
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

        # Call Load String from controller
        self.controller.load_string(
            id,
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

    def unload(self, stringid):
        """Unloads the module using the command in controller.py and the stringid"""

        # Notify User
        print("Unloading string: " + str(stringid))

        # Get ID
        id = int(stringid)

        # Unlock values
        self.unlock_values(id)

        # Call Unload String from controller
        self.controller.unload_string(id)

    def checktest(self, stringid):
        """Checks the test using the command in _______ and the stringid"""

        print("Checking string: " + str(stringid))

    ################################################################################
    # Buttons / Duplicated Functions
    ################################################################################

    # Lock Values for Editing

    def lock_value1(self):
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

    def lock_value2(self):
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

    def lock_value3(self):
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

    def lock_value4(self):
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

    def lock_value5(self):
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

    def lock_value6(self):
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

    # Unlock Values For Editing

    def unlock_value1(self):
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

    def unlock_value2(self):
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

    def unlock_value3(self):
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

    def unlock_value4(self):
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

    def unlock_value5(self):
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

    def unlock_value6(self):
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

    # Load Buttons

    def load1(self):
        self.load(1)

    def load2(self):
        self.load(2)

    def load3(self):
        self.load(3)

    def load4(self):
        self.load(4)

    def load5(self):
        self.load(5)

    def load6(self):
        self.load(6)

    # Unload Buttons

    def unload1(self):
        self.unload(1)

    def unload2(self):
        self.unload(2)

    def unload3(self):
        self.unload(3)

    def unload4(self):
        self.unload(4)

    def unload5(self):
        self.unload(5)

    def unload6(self):
        self.unload(6)

    # Checktest Buttons

    def checktest1(self):
        self.checktest(1)

    def checktest2(self):
        self.checktest(2)

    def checktest3(self):
        self.checktest(3)

    def checktest4(self):
        self.checktest(4)

    def checktest5(self):
        self.checktest(5)

    def checktest6(self):
        self.checktest(6)

    def Launch_GUI(self):
        app = QApplication(sys.argv)
        # UIWindow = PARASOL_UI()
        app.exec_()
