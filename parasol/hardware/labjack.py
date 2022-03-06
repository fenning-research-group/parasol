import yaml
import os

# Set module directory, import constants from yaml file
MODULE_DIR = os.path.dirname(__file__)
with open(os.path.join(MODULE_DIR, "..", "hardwareconstants.yaml"), "r") as f:
    constants = yaml.safe_load(f)["labjack"]  # , Loader=yaml.FullLoader)["relay"]


class LabJack:
    """Scanner package for PARASOL"""

    def __init__(self) -> None:
        """Initliazes the Scanner class for Yokogawa GS610"""

        # Get constants
        # self.timeout = constants["timeout"]
        # self.delay = constants["delay"]

        # Load constants, connect, and lock
        self.connect()

    def connect(self) -> None:
        """Connects to the yokogawa"""

        print("connected")

        # get address
        # port = get_port(constants["device_identifiers"])

        # Connect to relay using serial
        # self.labjack = serial.Serial(port, timeout=self.timeout)

    def get_temp(self) -> float:
        """Gets the temperature"""

        temp = 27

        return temp

    def get_rh(self) -> float:
        """Gets the humidity"""

        rh = 50

        return rh

    def get_intensity(self) -> float:
        """Gets the intensity"""

        intensity = 1

        return intensity
