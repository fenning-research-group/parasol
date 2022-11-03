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

    def __init__(self, ca_num: int) -> None:
        """Initliazes the Chroma class for Chroma 63102A

        Args:
            ca_num (int): chroma number
        """

        # Get constants from hardwareconstants
        self.time_out = constants["time_out"]
        self.baud_rate = constants["baud_rate"]
        self.source_delay = constants["source_delay"]
        self.sense_delay = constants["sense_delay"]
        self.ca_delay = constants["command_delay"]
        self.ca_avg_num = constants["avg_num"]
        self.ca_v_max = constants["max_voltage"]
        self.ca_i_max = constants["max_current"]
        self.ca_v_min = constants["v_min"]
        self.ca_address = constants["address"]
        self.ca_cc_mode = constants["current_mode"]
        self.ca_cv_mode = "CV" # 
        # self.voltage_range = constants["voltage_range"]
        # self.current_range = constants["current_range"]
        
        # Connect and setup lock
        self.lock = Lock()
        self.connect(ca_num=ca_num)

        # Set both channels to source voltage and measure current when initialized (1st is dummy index)
        # Added some time.sleep because sometimes Ch2 of ET5420 was not ready to receive commands. This should be done with internal commands.
        # TODO: Check if this is still necessary
        self._sourcing_current = [False, False, False]
        self.srcV_measI(1)
        time.sleep(1)
        self.srcV_measI(2)
        time.sleep(1)

    def connect(self, ca_num: int) -> None:
        """Connects to the chroma at the given port

        Args:
            ca_num (int): Chroma number
        """
        
        rm = pyvisa.ResourceManager()
        self.ca = rm.open_resource(self.ca_address)
        self.ca.timeout = constants["time_out"]
        # Get port information
        # if ca_num == 1:
        #     port = get_port(constants["device_identifiers"]["ET_1"])
        # elif ca_num == 2:
        #     port = get_port(constants["device_identifiers"]["ET_2"])
        # elif ca_num == 3:
        #     port = get_port(constants["device_identifiers"]["ET_3"])

        # Connect using serial, use highest transferrate and shortest timeout
        # self.ca = serial.Serial(port, baudrate=self.baud_rate, timeout=self.time_out)

    # untested
    def srcI_measV(self, channel: int) -> None:
        """Setup source current and measure voltage

        Args:
            channel (int or string): chroma channel to alter
        """
        
        # Set to input channel
        self.ca.write(":CHAN " + str(channel))
        time.sleep(self.ca_delay)

        # Set to constant current
        self.ca.write(":MODE " + self.ca_cc_mode)
        time.sleep(self.ca_delay)

        # Set ranges for voltage, as well as max and min
        # "NAME" : RANGE (MAX/SHUTOFF)
        # "LOW": 0.4 -> 16.000 (20.000)
        # "HIGH": 0.8 -> 80.000 (80.000)
        self.ca.write(":CONF:VOLT:RANG " + str(self.ca_v_max))
        time.sleep(self.ca_delay)

        # Set range for current, as well as max current (no min feature)
        # "NAME" : RANGE (MAX/SHUTOFF)
        # "LOW": 0 -> 2.000 (2.0)
        # "HIGH": 0 -> 20.000 (20.0)
        
        # no command for setting current range in CC?

        # Set max power output
        # "NAME" : RANGE (MAX/SHUTOFF)
        # ALL: 0 --> 100 (100?)

        # no command for setting max power output in CC?

        # Close channel
        self.ca.write(":CHAN:ACT OFF")
        time.sleep(self.ca_delay)

    def srcV_measI(self, channel: int) -> None:
        """Setup source voltage and measure current

        Args:
            channel (int or string): chroma channel to alter
        """
        
        # sets to input channel
        self.ca.write(":CHAN " + str(channel))
        time.sleep(self.ca_delay)
        
        # Set to constant voltage
        self.ca.write(":MODE " + self.ca_cv_mode)
        time.sleep(self.ca_delay)

        # Set ranges for voltage, as well as max and min
        # "NAME" : RANGE (MAX/SHUTOFF)
        # "LOW": 0.4 -> 16.000 (20.000)
        # "HIGH": 0.8 -> 80.000 (155.000)
        
        # no command for setting voltage range in CV

        # Set range for current, as well as max current (no min feature)
        # "NAME" : RANGE (MAX/SHUTOFF)
        # "LOW": 0 -> 3.000 (3.3)
        # "HIGH": 0 -> 20.000 (22.0)
        self.ca.write(":VOLT:CURR " + str(self.ca_i_max))
        time.sleep(self.ca_delay)

        # Set max power output
        # "NAME" : RANGE (MAX/SHUTOFF)
        # ALL: 0 --> 200 (220)
        
        # no command for setting max power limit in CV

        # Close channel
        self.ca.write(":CHAN:ACT OFF")
        time.sleep(self.ca_delay)

    @ca_lock
    def output_on(self, channel: int) -> None:
        """Turns output on

        Args:
            channel (int or string): chroma channel to alter
        """
        
        # sets to input channel
        self.ca.write(":CHAN " + str(channel))
        time.sleep(self.ca_delay)

        # enables the selected load module (panel displays measurements)
        self.ca.write(":CHAN:ACT ON")
        time.sleep(self.source_delay)

    @ca_lock
    def output_off(self, channel: int) -> None:
        """Turns output off

        Args:
            channel (int or string): chroma channel to alter
        """
        
        # sets to input channel
        self.ca.write(":CHAN " + str(channel))
        time.sleep(self.ca_delay)

        # disables the selected load module (LCD turns off?)
        self.ca.write(":CHAN:ACT OFF")
        time.sleep(self.source_delay)

    @ca_lock
    def set_voltage(self, channel: int, voltage: float) -> None:
        """Sets voltage

        Args:
            channel (int or string): chroma channel to alter
            voltage (float): desired voltage (V)
        """
        
        # sets to input channel
        self.ca.write(":CHAN " + str(channel))
        time.sleep(self.ca_delay)

        # If we are in wrong mode, switch
        if self._sourcing_current[channel] == True:
            self.srcV_measI(channel)
            self._sourcing_current[channel] = False

        # Set voltage (V) and wait
        self.ca.write(":VOLT:L1 " + str(voltage))
        time.sleep(self.ca_delay)
        
        # starts sinking current to match voltage
        self.ca.write(":LOAD ON")
        time.sleep(self.source_delay)

    def _set_voltage(self, channel: int, voltage: float) -> None:
        """Sets voltage without locking

        Args:
            channel (int or string): chroma channel to alter
            voltage (float): desired voltage (V)
        """
         
        # sets to input channel
        self.ca.write(":CHAN " + str(channel))
        time.sleep(self.ca_delay)

        # If we are in wrong mode, switch
        if self._sourcing_current[channel] == True:
            self.srcV_measI(channel)
            self._sourcing_current[channel] = False

        # Set voltage (V) and wait
        self.ca.write(":VOLT:L1 " + str(voltage))
        time.sleep(self.ca_delay)
        
        # starts sinking current to match voltage
        self.ca.write(":LOAD ON")
        time.sleep(self.source_delay)

    @ca_lock
    def set_current(self, channel: int, current: float) -> None:
        """Sets current

        Args:
            channel (int or string): chroma channel to alter
            current (float): desired current (A)
        """
        
        # set to input channel
        self.ca.write(":CHAN " + str(channel))
        time.sleep(self.ca_delay)

        # If we are in wrong mode, switch
        if self._sourcing_current[channel] == False:
            self.srcI_measV(channel)
            self._sourcing_current[channel] = True

        # set current (A) and wait
        self.ca.write(":CURR:STATIC:L1 " + str(current))
        time.sleep(self.ca_delay)
        
        # starts sinking current
        self.ca.write(":LOAD ON")
        time.sleep(self.source_delay)

    def _set_current(self, channel: int, current: float) -> None:
        """Sets current without locking

        Args:
            channel (int or string): chroma channel to alter
            current (float): desired current (A)
        """
        
        # set to input channel
        self.ca.write(":CHAN " + str(channel))
        time.sleep(self.ca_delay)

        # If we are in wrong mode, switch
        if self._sourcing_current[channel] == False:
            self.srcI_measV(channel)
            self._sourcing_current[channel] = True

        # set current (A) and wait
        self.ca.write(":CURR:STATIC:L1 " + str(current))
        time.sleep(self.ca_delay)
        
        # starts sinking current
        self.ca.write(":LOAD ON")
        time.sleep(self.source_delay)

    def measure_current(self, channel: int) -> float:
        """Measures current several times and then averages (number defined in hardwareconstants.yaml)

        Args:
            channel (int or string): chroma channel to alter

        Returns:
            float: current (A) reading
        """

        # sets to input channel
        self.ca.write(":CHAN " + str(channel))
        time.sleep(self.ca_delay)

        # sets avg num of measurements taken
        self.ca.write(":CONF:MEAS:AVE " + str(self.ca_avg_num))
        time.sleep(self.ca_delay)

        # measure current
        self.ca.write(":MEAS:CURR?")
        time.sleep(self.sense_delay)
        curr = self.ca.readlines()
        time.sleep(self.sense_delay)

        return curr

    def measure_voltage(self, channel: int) -> float:
        """Measures voltage several times and then averages (number defined in hardwareconstants.yaml)

        Args:
            channel (int or string): chroma channel to alter

        Returns:
            float: voltage (V) reading
        """

        # sets to input channel
        self.ca.write(":CHAN " + str(channel))
        time.sleep(self.ca_delay)

        # sets avg num of measurements taken
        self.ca.write(":CONF:MEAS:AVE " + str(self.ca_avg_num))
        time.sleep(self.ca_delay)

        # measure voltage
        self.ca.write(":MEAS:VOLT?")
        time.sleep(self.sense_delay)
        volt = self.ca.readlines()
        time.sleep(self.sense_delay)

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
