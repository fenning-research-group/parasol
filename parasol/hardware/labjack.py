class LabJack:
    """Scanner package for PARASOL"""

    def __init__(self) -> None:
        """Initliazes the Scanner class for Yokogawa GS610"""

        # Load constants, connect, and lock
        self.connect()

    def connect(self) -> None:
        """Connects to the yokogawa"""

        # get address
        # yoko_address = constants["address"]
        print("labjack connected")
        # # connect to the yokogawa using pyvisa (GPIB)
        # rm = pyvisa.ResourceManager()
        # self.yoko = rm.open_resource(yoko_address)
        # self.yoko.timeout = constants["timeout"]

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
