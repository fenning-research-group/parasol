import yaml
import os
import pyvisa
import time
import numpy as np
from threading import Lock

# set module directory, import constants from yaml file
MODULE_DIR = os.path.dirname(__file__)
with open(os.path.join(MODULE_DIR, "..", "hardwareconstants.yaml"), "r") as f:
    constants = yaml.safe_load(f)["chroma"]

class Chroma:
    """Chroma package for PARASOL"""

    def __init__(self) -> None:
        """Initliazes the Chroma class for Chroma 63102A
        
        Note:Chroma default status is on
        """

        # get constants from hardwareconstants
        self.time_out = constants["time_out"]
        self.source_delay = constants["source_delay"]
        self.sense_delay = constants["sense_delay"]
        #TODO:Check these/clean up
        self.ca_avg_num = constants["avg_num"] # number of measurments to average

        self.ca_v_max = constants["max_voltage"] # unused (use H below)
        self.ca_i_max = constants["max_current"] # unused (need max current for CV, can be # max or min)
        self.ca_address = constants["address"]
        self.ca_cc_mode = "CCH"
        self.ca_cv_mode = "CV"
        self.v_mode = 'H'

        # create lock        
        self.lock = Lock()

        # connect 
        self.connect()

        # create indicator of channel so we dont keep spamming to switch
        self.channel = None

        # set all channels to source voltage and measure current when initialized (1st is dummy index)
        self._sourcing_current = [False, False, False, False, False, False, False, False, False]
        self.srcV_measI(1)
        self.srcV_measI(2)
        self.srcV_measI(3)
        self.srcV_measI(4)
        self.srcV_measI(7)
        self.srcV_measI(8)
        

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

        
    def channel_check(self, channel: int) -> None:
        """Checks and switches to new channel ID

        Args:
            channel (int or string): chroma channel to alter
        """
        if channel != self.channel:
            self.ca.write("CHAN " + str(channel)) # sets new channel
            self.channel = channel


    def srcV_measI(self, channel: int) -> None:
        """Setup for sourcing voltage and measuring current

        Args:
            channel (int or string): chroma channel to alter
        """
        
        self.channel_check(channel) # set channel
        self.ca.write("MODE " + self.ca_cv_mode) # set mode to CV
        self.ca.write("CONF:MEAS:AVE " + str(self.ca_avg_num)) # set averge number
        # self.ca.write("VOLT:CURR " + str(self.ca_i_max))
        self.ca.write("VOLT:MODE "+ str(self.sense_delay)) # set CV response to slow
        self.ca.write("VOLT:L1 0") # set voltage of load to 0 V
        self.ca.write("CHAN:ACT OFF") # turn off measurement
        self.ca.write("LOAD OFF") # turn off load


    def srcI_measV(self, channel: int) -> None:
        """Setup for sourcing current and measuring voltage
        
        Args:
            channel (int or string): chroma channel to alter
        """
        
        self.channel_check(channel) # set channel
        self.ca.write("MODE " + self.ca_cc_mode) # set mode to CC
        self.ca.write("CURR:STATIC:L1 0") # set current of load to 0
        self.ca.write("CONF:MEAS:AVE " + str(self.ca_avg_num)) # set averge number
        self.ca.write("CONF:VOLT:RANG " + str(self.v_mode)) # set the volt range to high/low for CC mode 
        self.ca.write("CHAN:ACT OFF") # turn off measurement
        self.ca.write("LOAD OFF") # turn off load


    def output_on(self, channel: int) -> None:
        """Turns output on

        Args:
            channel (int or string): chroma channel to alter
        """
        
        self.channel_check(channel) # set channel
        self.ca.write("CHAN:ACT ON") # turn on measurement
        self.ca.write("LOAD ON") # turn on load


    def load_on(self, channel: int, voltage: float) -> None:
        """Turns output on and applies voltage with lock

        Args:
            channel (int or string): chroma channel to alter
            voltage (float)
        """
        with self.lock:
            self.set_voltage(channel, voltage)
            self.output_on(channel)
            
    
    def load_off(self, channel: int) -> None:
        """Turns output off with lock

        Args:
            channel (int or string): chroma channel to alter
        """

        with self.lock:
            self.output_off(channel)
    

    def output_off(self, channel: int) -> None:
        """Turns output off

        Args:
            channel (int or string): chroma channel to alter
        """
        
        self.channel_check(channel) # sets channel
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
        
        self.channel_check(channel) # set channel
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

        self.channel_check(channel) # set channel
        self.ca.write("CURR:STATIC:L1 " + str(current)) # set load current
        time.sleep(self.source_delay) # delay for system to settle


    def measure_voltage(self, channel: int) -> float:
        """Measures the voltage reading at the given channel

        Args:
            channel (int or string): chroma channel to alter

        Returns:
            float: voltage (V) reading
        """

        
        self.channel_check(channel) # set channel
        volt = float(self.ca.query("MEAS:VOLT?")) # measure voltage

        return volt


    def measure_current(self, channel: int) -> float:
        """Measures the current reading at the given channel

        Args:
            channel (int or string): chroma channel to alter

        Returns:
            float: current (A) reading
        """

        self.channel_check(channel) # sets channel
        curr = float(self.ca.query("MEAS:CURR?")) # measure current

        return curr


    def set_V_measure_I(self, channel: int, voltage: float, lock = True) -> float:
        """Sets voltage and measures current

        Args:
            channel (int or string): chroma channel to alter
            voltage (float): voltage (V)
            lock (boolean = True): option to lock instrument while command is running

        Returns:
            float: voltage (V) reading
            float: current (A) reading 
        """

        if lock:
            with self.lock:
                # set voltage, measure current and voltage
                self.set_voltage(channel, voltage)
                curr = self.measure_current(channel)
                volt = self.measure_voltage(channel)
        else:
            # set voltage, measure current and voltage
            self.set_voltage(channel, voltage)
            curr = self.measure_current(channel)
            volt = self.measure_voltage(channel)        
        return volt, curr
    

    def set_I_measure_V(self, channel: int, current: float, lock = True) -> float:
        """Sets current and measures voltage

        Args:
            channel (int or string): chroma channel to alter
            voltage (float): current (A)
            lock (boolean = True): option to lock instrument while command is running

        Returns:
            float: current (A) reading
            float: voltage (V) reading
        """
        
        if lock:
            with self.lock:
                # set current, measure current and voltage
                self.set_current(channel, current)
                volt = self.measure_voltage(channel)
                curr = self.measure_current(channel)
        else:
            # set current, measure current and voltage
            self.set_current(channel, current)
            volt = self.measure_voltage(channel)
            curr = self.measure_current(channel)

        return curr, volt


    def voc(self, channel: int) -> float:
        """Gets open circut voltage (V) where I = 0

        Args:
            channel (int or string): chroma channel to alter

        Returns:
            float: open circut voltage (V)
        """

        self.channel_check(channel) # set channel
        i,v = self.set_I_measure_V(0) # set current to 0, measure voltage

        return v


    def isc(self, channel: int) -> float:
        """Gets short circut current (A) where V = 0

        Args:
            channel (int or string): chroma channel to alter

        Returns:
            float: short circut current (A)
        """
        self.channel_check(channel) # set channel
        v,i = self.set_V_measure_I(0) # set voltage to 0, measure current

        return i


    def iv_sweep(self, channel: int, vstart: float, vend: float, steps: int) -> np.ndarray:
        """Runs a single IV sweep and returns the data

        Args:
            channel (int): channel
            vstart (float): FWD sweep start voltage (V)
            vend (float): FWD sweep end voltage (V)
            steps (float): number of voltage steps in the sweep

        Returns:
            np.ndarray: voltage (V) array
            np.ndarray: current (A) array
        """

        with self.lock:

            # make empty numpy arrays for data
            v = np.linspace(vstart, vend, steps)
            vm = np.zeros(v.shape)
            i = np.zeros(v.shape)

            # turn on output, set voltage, measure current, turn off output
            self.output_on(channel)
            for idx, v_point in enumerate(v):
                vm[idx],i[idx] = self.set_V_measure_I(channel,v_point, lock = False)
            self.output_off(channel)

            # flip reverse scan order so that it aligns with voltage
            if abs(vstart) > abs(vend):
                i = i[::-1]
                vm = vm[::-1]

        return v, vm, i
    

    def iv_sweep_quadrant_fwd_rev(self, channel: int, vstart: float, vend: float, steps: int) -> np.ndarray:
        """Runs FWD and then REV IV sweep in the power producing quadrant and returns the data

        Args:
            chanel(int): chroma channel number
            vstart (float): FWD sweep start voltage (V)
            vend (float): FWD sweep end voltage (V)
            steps (float): number of voltage steps in the sweep

        Returns:
            np.ndarray: voltage applied (V) array
            np.ndarray: FWD voltage measured (V) array
            np.ndarray: FWD current measured (A) array
            np.ndarray: REV voltage measured (V) array
            np.ndarray: REV current measured (A) array
        """

        with self.lock:

            # make empty numpy arrays for data
            v = np.linspace(vstart, vend, steps)
            vm_fwd = np.zeros(v.shape)
            i_fwd = np.zeros(v.shape)
            vm_rev = np.zeros(v.shape)
            i_rev = np.zeros(v.shape)
            i_fwd[:] = np.nan
            i_rev[:] = np.nan

            # turn on output
            self.output_on(channel)

            # find point before 1st point in quadrant
            index = 0
            for v_point in v:
                if v_point >= 0:
                    break
                index += 1
            index -= 1
            start_index = index

            # cycle from there until we get out of the quadrant
            while index <= len(v):
                vm_fwd[index], i_fwd[index] = self.set_V_measure_I(channel,v[index], lock = False)
                if i_fwd[index] > 0:
                    break
                index += 1

            # scan backwards until we get back to starting point
            while index >= start_index:
                vm_rev[index], i_rev[index] = self.set_V_measure_I(channel,v[index], lock = False)
                index -= 1

            # turn output off
            self.output_off(channel)

        return v, vm_fwd, i_fwd, vm_rev, i_rev


    def iv_sweep_quadrant_rev_fwd(self, channel: int, vstart: float, vend: float, steps: int) -> np.ndarray:
        """Runs REV and then FWD IV sweep in the power producing quadrant and returns the data

        Args:
            channel (int): chroma channel number
            vstart (float): FWD sweep start voltage (V)
            vend (float): FWD sweep end voltage (V)
            steps (float): number of voltage steps in the sweep

        Returns:
            np.ndarray: voltage applied (V) array
            np.ndarray: FWD voltage measured (V) array
            np.ndarray: FWD current measured (A) array
            np.ndarray: REV voltage measured (V) array
            np.ndarray: REV current measured (A) array
        """

        with self.lock:

            # make empty numpy arrays for data
            v = np.linspace(vstart, vend, steps)
            vm_fwd = np.zeros(v.shape)
            i_fwd = np.zeros(v.shape)
            vm_rev = np.zeros(v.shape)
            i_rev = np.zeros(v.shape)
            i_fwd[:] = np.nan
            i_rev[:] = np.nan

            # find point after voc
            voc = self.voc(0)
            end_index = np.where(np.diff(np.signbit(v - voc)))[0]
            if (v[end_index] - voc) < 0:
                end_index += 1

            # find point before jsc
            index = 0
            for v_point in v:
                if v_point >= 0:
                    break
                index += 1
            index -= 1
            start_index = index

            # turn on output
            self.output_on(channel)

            # scan rev until we get back to starting point
            index = end_index
            while index >= start_index:
                vm_rev[index], i_rev[index] = self.set_V_measure_I(channel,v[index], lock = False)
                index -= 1

            # cycle from there until we get out of the quadrant
            index = start_index
            while index <= end_index:
                vm_fwd[index], i_fwd[index] = self.set_V_measure_I(channel,v[index], lock = False)
                index += 1

            # turn output off
            self.output_off(channel)

        return v, vm_fwd, i_fwd, vm_rev, i_rev
