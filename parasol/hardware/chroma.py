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
        self.connect()

        # Set both channels to source voltage and measure current when initialized (1st is dummy index)
        self._sourcing_current = [False, False, False, False, False, False, False, False, False]
        self.srcV_measI(1)
        self.srcV_measI(2)
        self.srcV_measI(3)
        self.srcV_measI(4)
        self.srcV_measI(7)
        self.srcV_measI(8)
        
        # indicator of channel so we dont keep spamming
        self.channel = None
        

    def connect(self) -> None:
        """Connects to the chroma"""
        
        rm = pyvisa.ResourceManager()
        self.ca = rm.open_resource(self.ca_address)
        self.ca.timeout = constants["time_out"]
        self.ca.write('*RST')


    def disconnect(self):
        """Disconnects from the chroma"""
        self.inst.close()
        self.rm.close()


    def srcI_measV(self, channel: int) -> None:
        """Setup source current and measure voltage
        
        Args:
            channel (int or string): chroma channel to alter
        """
        
        if channel != self.channel:
            self.ca.write("CHAN " + str(channel)) # set channel
            self.channel = channel
        self.ca.write("MODE " + self.ca_cc_mode) # set mode to CC
        # self.ca.write("CONF:MEAS:AVE " + str(self.ca_avg_num))
        # self.ca.write("CONF:VOLT:RANG L")# + str(self.ca_v_max)+"V") 
        self.ca.write("CHAN:ACT OFF") # turn off measurement
        self.set_current(channel,0.0) # set power to 0


    def srcV_measI(self, channel: int) -> None:
        """Setup source voltage and measure current

        Args:
            channel (int or string): chroma channel to alter
        """
        
        if channel != self.channel:
            self.ca.write("CHAN " + str(channel)) # set channel
            self.channel = channel
        self.ca.write("MODE " + self.ca_cv_mode) # set mode to CV
        # self.ca.write("CONF:MEAS:AVE " + str(self.ca_avg_num))
        # self.ca.write("VOLT:CURR L")# set current mode low + str(self.ca_i_max) +"A")
        # self.ca.write("VOLT:MODE FAST") 
        self.ca.write("CHAN:ACT OFF") # turn off measurement
        self.set_voltage(channel,0.0) # set power to 0


    def output_on(self, channel: int) -> None:
        """Turns output on

        Args:
            channel (int or string): chroma channel to alter
        """
        
        if channel != self.channel:
            self.ca.write("CHAN " + str(channel)) # set channel
            self.channel = channel
        self.ca.write("CHAN:ACT ON") # turn on measurement
        self.ca.write("LOAD ON") # turn on load


    def output_off(self, channel: int) -> None:
        """Turns output off

        Args:
            channel (int or string): chroma channel to alter
        """
        
        if channel != self.channel:
            self.ca.write("CHAN " + str(channel)) # set channel
            self.channel = channel
        self.ca.write("CHAN:ACT OFF") # turn off measurement
        self.ca.write("LOAD OFF") # turn off load


    def set_voltage(self, channel: int, voltage: float) -> None:
        """Sets voltage

        Args:
            channel (int or string): chroma channel to alter
            voltage (float): desired voltage (V)
        """
        
        # If we are in wrong mode, switch
        if self._sourcing_current[channel] == True:
            self.srcV_measI(channel)
            self.output_on(channel)
            self._sourcing_current[channel] = False
        
        if channel != self.channel:
            self.ca.write("CHAN " + str(channel)) # set channel
            self.channel = channel
        self.ca.write("VOLT:L1 " + str(voltage)) # set load voltage
        time.sleep(self.source_delay) # delay for system to settle


    def set_current(self, channel: int, current: float) -> None:
        """Sets current

        Args:
            channel (int or string): chroma channel to alter
            current (float): desired current (A)
        """

        # If we are in wrong mode, switch
        if self._sourcing_current[channel] == False:
            self.srcI_measV(channel)
            self.output_on(channel)
            self._sourcing_current[channel] = True

        # set to input channel
        if channel != self.channel:
            self.ca.write("CHAN " + str(channel)) # set channel
            self.channel = channel
        self.ca.write("CURR:STATIC:L1 " + str(current)) # set load current
        time.sleep(self.source_delay) # delay for system to settle


    def measure_current(self, channel: int) -> float:
        """Measures current several times and then averages (number defined in hardwareconstants.yaml)

        Args:
            channel (int or string): chroma channel to alter

        Returns:
            float: current (A) reading
        """

        if channel != self.channel:
            self.ca.write("CHAN " + str(channel)) # set channel
            self.channel = channel
        curr = float(self.ca.query("MEAS:CURR?")) # measure current

        return curr


    def measure_voltage(self, channel: int) -> float:
        """Measures voltage several times and then averages (number defined in hardwareconstants.yaml)

        Args:
            channel (int or string): chroma channel to alter

        Returns:
            float: voltage (V) reading
        """

        # sets to input channel
        if channel != self.channel:
            self.ca.write("CHAN " + str(channel)) # set channel
            self.channel = channel
        volt = float(self.ca.query("MEAS:VOLT?")) # measure voltage

        return volt


    def voc(self, channel: int) -> float:
        """Gets open circut voltage: V where I = 0

        Args:
            channel (int or string): chroma channel to alter

        Returns:
            float: open circut voltage (V)
        """

        # Set current to 0, measure voltage
        self.set_current(channel, 0)
        voc = self.measure_voltage(channel)

        return voc


    def isc(self, channel: int) -> float:
        """Gets short circut current: I where V = 0

        Args:
            channel (int or string): chroma channel to alter

        Returns:
            float: short circut current (A)
        """

        # Set voltage to 0, measure current
        self.set_voltage(channel, 0)
        isc = self.measure_current(channel)

        return isc


    def set_V_measure_I(self, channel: int, voltage: float) -> float:
        """Sets voltage and measures current

        Args:
            channel (int or string): chroma channel to alter
            voltage (float): voltage (V)

        Returns:
            float: current (A) reading
        """

        # Ensure we are in correct quadrant
        if(voltage < 0):
            print("VOLTAGE ERROR!!!!")
            voltage = abs(voltage + 0.05)

        # set voltage, measure current and voltage
        self.set_voltage(channel, voltage)
        curr = self.measure_current(channel)
        volt = self.measure_voltage(channel)
        print(voltage,volt,curr)
        return curr


    def set_I_measure_V(self, channel: int, current: float) -> float:
        """Sets current and measures voltage

        Args:
            channel (int or string): chroma channel to alter
            voltage (float): current (A)

        Returns:
            float: voltage (V) reading
        """
        
        # Ensure we are in correct quadrant
        if(current < 0):
            print("CURRENT ERROR!!!!")
            voltage = abs(voltage + 0.05)
        
        # set current, measure current and voltage
        self.set_current(channel, current)
        volt = self.measure_voltage(channel)
        curr = self.measure_current(channel)
        print(current,curr,volt)
        return volt
