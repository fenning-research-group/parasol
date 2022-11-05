import yaml
import os
import re
import pyvisa
import time
from threading import Lock

from parasol.hardware.port_finder import get_port


# Set module directory, import constants from yaml file
MODULE_DIR = os.path.dirname(__file__)
with open(os.path.join(MODULE_DIR, "..", "hardwareconstants.yaml"), "r") as f:
    constants = yaml.safe_load(f)["chroma"]


def ca_lock(f):
    """Locks chroma

    Args:
        f (function): any function that needs to be locked
    """

    def inner(self, *args, **kwargs):
        with self.lock:
            return f(self, *args, **kwargs)

    return inner


class Chroma:
    """Chroma package for PARASOL"""

    def __init__(self) -> None:
        """Initliazes the Chroma class for Chroma 63102A

        Args:
            ca_num (int): chroma number
        """

        # Get constants from hardwareconstants
        self.time_out = constants["time_out"]
        self.source_delay = constants["source_delay"]
        self.sense_delay = constants["sense_delay"]
        self.ca_delay = constants["command_delay"]
        self.ca_avg_num = constants["avg_num"]
        self.ca_v_max = constants["max_voltage"]
        self.ca_i_max = constants["max_current"]
        self.ca_v_min = constants["v_min"]
        self.ca_address = constants["address"]
        self.ca_cc_mode = constants["current_mode"]
        self.ca_cv_mode = "CV"
        
        # Connect and setup lock
        self.lock = Lock()
        self.connect()

        # Set both channels to source voltage and measure current when initialized (1st is dummy index)
        # Added some time.sleep because sometimes Ch2 of ET5420 was not ready to receive commands. This should be done with internal commands.
        # TODO: Check if this is still necessary
        self._sourcing_current = [False, False, False, False, False, False, False, False, False]
        self.srcV_measI(1)
        self.srcV_measI(2)
        self.srcV_measI(3)
        self.srcV_measI(4)
        self.srcV_measI(7)
        self.srcV_measI(8)
        

    def connect(self) -> None:
        """Connects to the chroma at the given port

        Args:
            ca_num (int): Chroma number
        """
        
        rm = pyvisa.ResourceManager()
        self.ca = rm.open_resource(self.ca_address)
        self.ca.timeout = constants["time_out"]
        

    # untested
    def srcI_measV(self, channel: int) -> None:
        """Setup source current and measure voltage

        Args:
            channel (int or string): chroma channel to alter
        """
        
        self.ca.write("CHAN " + str(channel))
        self.ca.write("MODE " + self.ca_cc_mode)
        self.ca.write("CONF:VOLT:RANG " + str(self.ca_v_max)+"V") # note this could be H or L for high or low
        self.ca.write("CHAN:ACT OFF")

    def srcV_measI(self, channel: int) -> None:
        """Setup source voltage and measure current

        Args:
            channel (int or string): chroma channel to alter
        """
        
        self.ca.write("CHAN " + str(channel))
        self.ca.write("MODE " + self.ca_cv_mode)
        self.ca.write("VOLT:CURR " + str(self.ca_i_max) +"A")
        self.ca.write("CHAN:ACT OFF")

    @ca_lock
    def output_on(self, channel: int) -> None:
        """Turns output on

        Args:
            channel (int or string): chroma channel to alter
        """
        
        self.ca.write("CHAN " + str(channel))
        self.ca.write("CHAN:ACT ON")

    @ca_lock
    def output_off(self, channel: int) -> None:
        """Turns output off

        Args:
            channel (int or string): chroma channel to alter
        """
        
        self.ca.write("CHAN " + str(channel))
        self.ca.write("CHAN:ACT OFF")

    @ca_lock
    def set_voltage(self, channel: int, voltage: float) -> None:
        """Sets voltage

        Args:
            channel (int or string): chroma channel to alter
            voltage (float): desired voltage (V)
        """
        
        # If we are in wrong mode, switch
        if self._sourcing_current[channel] == True:
            self.srcV_measI(channel)
            self._sourcing_current[channel] = False
        
        self.ca.write("CHAN " + str(channel))
        # self.ca.write("VOLT:L1 " + str(voltage) + "V")
        self.ca.write("VOLT:L1 " + str(0) + "V")
        # self.ca.write("CONF:VOLT:ON 1V")
        self.ca.write("LOAD ON")
        time.sleep(self.source_delay)


    def _set_voltage(self, channel: int, voltage: float) -> None:
        """Sets voltage without locking

        Args:
            channel (int or string): chroma channel to alter
            voltage (float): desired voltage (V)
        """
         
        # If we are in wrong mode, switch
        if self._sourcing_current[channel] == True:
            self.srcV_measI(channel)
            self._sourcing_current[channel] = False
        
        self.ca.write("CHAN " + str(channel))
        self.ca.write("VOLT:L1 " + str(0) + "V")
        # self.ca.write("VOLT:L1 " + str(voltage) + "V")
        self.ca.write("LOAD ON")
        time.sleep(self.source_delay)

    @ca_lock
    def set_current(self, channel: int, current: float) -> None:
        """Sets current

        Args:
            channel (int or string): chroma channel to alter
            current (float): desired current (A)
        """

        # If we are in wrong mode, switch
        if self._sourcing_current[channel] == False:
            self.srcI_measV(channel)
            self._sourcing_current[channel] = True

        # set to input channel
        self.ca.write("CHAN " + str(channel))
        self.ca.write("CURR:STATIC:L1 " + str(current) + "A")
        self.ca.write("LOAD ON")
        time.sleep(self.source_delay)

    def _set_current(self, channel: int, current: float) -> None:
        """Sets current without locking

        Args:
            channel (int or string): chroma channel to alter
            current (float): desired current (A)
        """
        

        # If we are in wrong mode, switch
        if self._sourcing_current[channel] == False:
            self.srcI_measV(channel)
            self._sourcing_current[channel] = True

        self.ca.write("CHAN " + str(channel))
        self.ca.write("CURR:STATIC:L1 " + str(current) + "A")
        self.ca.write("LOAD ON")
        time.sleep(self.source_delay)

    def measure_current(self, channel: int) -> float:
        """Measures current several times and then averages (number defined in hardwareconstants.yaml)

        Args:
            channel (int or string): chroma channel to alter

        Returns:
            float: current (A) reading
        """
        # mIGHT NEED
        # self.ca.wite(":MEAS:INP")
        # sets to input channel
        self.ca.write("CHAN " + str(channel))
        self.ca.write("CONF:MEAS:AVE " + str(self.ca_avg_num))
        time.sleep(self.sense_delay)
        curr = float(self.ca.query("MEAS:CURR?"))

        return curr

    def measure_voltage(self, channel: int) -> float:
        """Measures voltage several times and then averages (number defined in hardwareconstants.yaml)

        Args:
            channel (int or string): chroma channel to alter

        Returns:
            float: voltage (V) reading
        """

        # sets to input channel
        self.ca.write("CHAN " + str(channel))
        self.ca.write("CONF:MEAS:AVE " + str(self.ca_avg_num))
        time.sleep(self.sense_delay)
        volt = float(self.ca.query("MEAS:VOLT?"))

        return volt

    # untested
    @ca_lock
    def voc(self, channel: int) -> float:
        """Gets open circut voltage: V where I = 0

        Args:
            channel (int or string): chroma channel to alter

        Returns:
            float: open circut voltage (V)
        """

        # Set current to 0, measure voltage
        self._set_current(channel, 0)
        voc = self.measure_voltage(channel)

        return voc

    # untested
    @ca_lock
    def isc(self, channel: int) -> float:
        """Gets short circut current: I where V = 0

        Args:
            channel (int or string): chroma channel to alter

        Returns:
            float: short circut current (A)
        """

        # Set voltage to 0, measure current
        self._set_voltage(channel, 0)
        isc = self.measure_current(channel)

        return isc

    @ca_lock
    def set_V_measure_I(self, channel: int, voltage: float) -> float:
        """Sets voltage and measures current

        Args:
            channel (int or string): chroma channel to alter
            voltage (float): voltage (V)

        Returns:
            float: current (A) reading
        """

        # Set voltage, wait, measure current
        # NEW NEW
        if(voltage <= 0):
            print("VOLTAGE ERROR!!!!")
            voltage = abs(voltage + 0.05)

        self._set_voltage(channel, voltage)
        curr = self.measure_current(channel)
        return curr

    # untested
    @ca_lock
    def set_I_measure_V(self, channel: int, voltage: float) -> float:
        """Sets current and measures voltage

        Args:
            channel (int or string): chroma channel to alter
            voltage (float): current (A)

        Returns:
            float: voltage (V) reading
        """

        # Set current, wait, measure voltage
        self._set_current(channel, voltage)
        volt = self.measure_voltage(channel)
        return volt
