import yaml
import os
import pyvisa
import numpy as np
import matplotlib as mpl
from threading import Lock

mpl.rcParams.update(mpl.rcParamsDefault)

# Set module directory, import constants from yaml file
MODULE_DIR = os.path.dirname(__file__)
with open(os.path.join(MODULE_DIR, "..", "hardwareconstants.yaml"), "r") as f:
    constants = yaml.safe_load(f)["yokogawa"]  # , Loader=yaml.FullLoader)["yokogawa"]

class Yokogawa:
    """Yokowaga package for PARASOL
    
    Note:Chroma default status is off
    """

    def __init__(self) -> None:
        """Initliazes the class for Yokogawa GS610"""

        self.lock = Lock()

        # Load constants
        self.source_delay = constants["source_delay"]
        self.sense_delay = constants["sense_delay"]
        self.int_time = constants["integration_time"]
        self.max_voltage = constants["max_voltage"]
        self.max_current = constants["max_current"]
        self.yoko_address = constants["address"]

        # Connect
        self.connect()

        # Set up to source V and measure I
        self._sourcing_current = False
        self.srcV_measI()

    def connect(self) -> None:
        """Connects to the yokogawa"""

        # Connect to the yokogawa using pyvisa (GPIB)
        rm = pyvisa.ResourceManager()
        self.yoko = rm.open_resource(self.yoko_address)
        self.yoko.timeout = constants["timeout"]
        self.yoko.write("*RST")  # Reset factory
        self.yoko.write(":SENS:RSEN 1") # Set 4 terminal
        self.yoko.write(":TRIG:SOUR EXT")  # Trigger source external trigger


    def disconnect(self):
        """Disconnects from the yokogawa"""
        self.inst.close()
        self.rm.close()

    def srcV_measI(self) -> None:
        """Setup source voltage and measure current"""

        # Source functions
        self.yoko.write(":SOUR:FUNC VOLT")  # Source function voltage
        self.yoko.write((":SOUR:DEL " + str(self.source_delay) + "ms"))  # Source delay minmum in ms

        # source volt options
        self.yoko.write((":SOUR:VOLT:RANG " + str(self.max_voltage) + "V"))  # Source voltage range setting to user specification
        self.yoko.write(":SOUR:VOLT:LEV 0V")  # Source level 0 V

        # source current options
        self.yoko.write(":SOUR:CURR:PROT:ULIM " + str(self.max_current) + "A") # Limit current to user specification
        self.yoko.write(":SOUR:CURR:PROT:LLIM -" + str(self.max_current) + "A") # NEW Limit current to user specification
        self.yoko.write(":SOUR:CURR:PROT:LINK ON")  # Limiter tracking on
        self.yoko.write(":SOUR:CURR:PROT:STAT ON")  # Limiter on

        # sense options
        self.yoko.write(":SENS:FUNC CURR")  # Measurement function current
        # self.yoko.write(":SENS:CURR:RANG 1A") # NEW doesnt work
        self.yoko.write((":SENS:DEL " + str(self.sense_delay) + "ms"))  # Sense delay minmum in ms
        self.yoko.write((":SENS:ITIM " + str(self.int_time) + "ms"))  # Integration time in ms
        self.yoko.write(":SENS:AZER:STAT OFF")  # Auto zero off

        # turn off measurement and load output
        self._sourcing_current = False
        self.yoko.write(":OUTP:STAT OFF") # Output off
        self.yoko.write(":SENS:STAT OFF")  # Measurement off

    def srcI_measV(self) -> None:
        """Setup source current and measure voltage"""

        # Source functions
        self.yoko.write(":SOUR:FUNC CURR")  # Source function current
        self.yoko.write((":SOUR:DEL " + str(self.source_delay) + "ms"))  # Source delay minmum in ms #

        # source current options
        self.yoko.write((":SOUR:CURR:RANG " + str(self.max_current) + "A"))
        self.yoko.write(":SOUR:CURR:LEV 0A")  # Source level 0 V

        # source volt options
        self.yoko.write((":SOUR:VOLT:PROT:ULIM " + str(self.max_voltage) + "V")) # Limit current to user specification
        self.yoko.write((":SOUR:VOLT:PROT:ULIM -" + str(self.max_voltage) + "V")) # NEW Limit current to user specification
        self.yoko.write(":SOUR:VOLT:PROT:LINK ON")  # Limiter tracking on#
        self.yoko.write(":SOUR:VOLT:PROT:STAT ON")  # Limiter on#

        # sense functions
        self.yoko.write(":SENS:FUNC VOLT")  # Measurement function voltage
        # curr equiv self.yoko.write(":SENS:CURR:RANG 1A") # NEW doesnt work
        self.yoko.write((":SENS:DEL " + str(self.sense_delay) + "ms"))  # Sense delay minmum in ms #
        self.yoko.write((":SENS:ITIM " + str(self.int_time) + "ms"))  # Integration time in ms #
        self.yoko.write(":SENS:AZER:STAT OFF")  # Auto zero off #

        # turn off measurement and load ouput
        self._sourcing_current = True
        self.yoko.write(":SENS:STAT OFF")  # Measurement off
        self.yoko.write(":OUTP:STAT OFF") # Output off


    def output_on(self) -> None:
        """Turn output on"""

        self.yoko.write(":OUTP:STAT ON")
        self.yoko.write(":SENS:STAT ON")

    def output_off(self) -> None:
        """Turn output off"""

        self.yoko.write(":OUTP:STAT OFF")
        self.yoko.write(":SENS:STAT OFF")

    def _trig_read(self) -> str:
        """Reads the last output

        Returns:
            str : last output value
        """

        return self.yoko.query(":INIT;*TRG;:FETC?")

    def set_voltage(self, v: float) -> None:
        """Sets the voltage

        Args:
            v (float): desired voltage (V)
        """

        # Ensure we are sourcing voltage
        if self._sourcing_current:
            self.srcV_measI()
            self.output_on()
            self._sourcing_current = False

        # Set voltage (V)
        tempstr = ":SOUR:VOLT:LEV " + str(v) + "V"
        self.yoko.write(tempstr)

    def set_current(self, i: float) -> None:
        """Sets the current

        Args:
            i (float): desired current (A)
        """

        # Ensure we are sourcing current
        if not self._sourcing_current:
            self.srcI_measV()
            self.output_on
            self._sourcing_current = True

        # Set current (A)
        tempstr = ":SOUR:CURR:LEV " + str(i) + "A"
        self.yoko.write(tempstr)

    def measure_voltage(self) -> float:
        """Measures voltage several times and then averages (number defined in hardwareconstants.yaml)

        Returns:
            float: voltage (V) reading
        """
        self.yoko.write(":SENS:FUNC VOLT")
        return (float(self._trig_read()))

    def measure_current(self) -> float:
        """Measures current several times and then averages (number defined in hardwareconstants.yaml)

        Returns:
            float: current (A) reading
        """
        self.yoko.write(":SENS:FUNC CURR")
        return (float(self._trig_read()))


    def set_V_measure_I(self, voltage: float, lock = True) -> float:
        """Sets voltage and measures current

        Args:
            voltage (float): voltage (V)
            lock (boolean = True): option to lock instrument while command is running

        Returns:
            float: voltage (V) reading
            float: current (A) reading 
        """
        if lock:
            with self.lock:
                # set voltage, measure current and voltage
                self.set_voltage(voltage)
                curr = self.measure_current()
                volt = self.measure_voltage()
        else:
            # set voltage, measure current and voltage
            self.set_voltage(voltage)
            curr = self.measure_current()
            volt = self.measure_voltage()

        return volt, curr


    def set_I_measure_V(self, current: float, lock = True) -> float:
        """Sets current and measures voltage

        Args:
            voltage (float): current (A)
            lock (boolean = True): option to lock instrument while command is running

        Returns:
            float: voltage (V) reading
        """
        if lock:
            with self.lock:
                # set current, measure current and voltage
                self.set_current(current)
                volt = self.measure_voltage()
                curr = self.measure_current()

        else:
            # set current, measure current and voltage
            self.set_current(current)
            volt = self.measure_voltage()
            curr = self.measure_current()
        
        return curr, volt


    def voc(self) -> float:
        """Measures the open circuit voltage

        Returns:
            float: open circut voltage (V)
        """

        # Set current to 0, measure voltage (V)
        i,v = self.set_I_measure_V(0)

        return v


    def isc(self) -> float:
        """Measures the short circuit current

        Returns:
            float: short circuit current (A)
        """

        # Set voltage to 0, measure current (A)
        v,i = self.set_V_measure_I(0)

        return i


    def iv_sweep(self, vstart: float, vend: float, steps: int) -> np.ndarray:
        """Runs a single IV sweep and returns the data

        Args:
            vstart (float): FWD sweep start voltage (V)
            vend (float): FWD sweep end voltage (V)
            steps (float): number of voltage steps in the sweep

        Returns:
            np.ndarray: voltage (V) array
            np.ndarray: current (A) array
        """
        with self.lock:
            
            # Make empty numpy arrays for data
            v = np.linspace(vstart, vend, steps)
            i = np.zeros(v.shape)
            vm = np.zeros(v.shape)

            # Turn on output, set voltage, measure current, turn off output
            self.output_on()
            for idx, v_point in enumerate(v):
                vm[idx],i[idx] = self.set_V_measure_I(v_point, lock = False)
            self.output_off()

            # Flip reverse scan order so that it aligns with voltage
            if abs(vstart) > abs(vend):
                i = i[::-1]
                vm = vm[::-1]

        return v, vm, i


    def iv_sweep_quadrant_fwd_rev(
        self, vstart: float, vend: float, steps: int
    ) -> np.ndarray:
        """Runs FWD and then REV IV sweep in the power producing quadrant and returns the data

        Args:
            vstart (float): FWD sweep start voltage (V)
            vend (float): FWD sweep end voltage (V)
            steps (float): number of voltage steps in the sweep

        Returns:
            vstart (float): sweep start voltage (V)
            vend (float): sweep end voltage (V)
            steps (float): number of voltage steps in the sweep

        Returns:
            np.ndarray: voltage (V) array
            np.ndarray: current (A) array
        """

        with self.lock:
            # Make empty numpy arrays for data
            v = np.linspace(vstart, vend, steps)
            vm_fwd = np.zeros(v.shape)
            i_fwd = np.zeros(v.shape)
            vm_rev = np.zeros(v.shape)
            i_rev = np.zeros(v.shape)
            i_fwd[:] = np.nan
            i_rev[:] = np.nan

            # Turn on output
            self.output_on()

            # Find point before 1st point in quadrant
            index = 0
            for v_point in v:
                if v_point >= 0:
                    break
                index += 1
            index -= 1
            start_index = index

            # Cycle from there until we get out of the quadrant
            while index <= len(v):
                vm_fwd[index], i_fwd[index] = self.set_V_measure_I(v[index], lock = False)
                if i_fwd[index] > 0:
                    break
                index += 1

            # Scan backwards until we get back to starting point
            while index >= start_index:
                vm_rev[index], i_rev[index] = self.set_V_measure_I(v[index], lock = False)
                index -= 1

            # Turn output off
            self.output_off()

        return v, vm_fwd, i_fwd, vm_rev, i_rev

    def iv_sweep_quadrant_rev_fwd(
        self, vstart: float, vend: float, steps: int
    ) -> np.ndarray:
        """Runs REV and then FWD IV sweep in the power producing quadrant and returns the data

        Args:
            vstart (float): FWD sweep start voltage (V)
            vend (float): FWD sweep end voltage (V)
            steps (float): number of voltage steps in the sweep

        Returns:
            vstart (float): sweep start voltage (V)
            vend (float): sweep end voltage (V)
            steps (float): number of voltage steps in the sweep

        Returns:
            np.ndarray: voltage (V) array
            np.ndarray: current (A) array
        """
        
        with self.lock:
        
            # Make empty numpy arrays for data
            v = np.linspace(vstart, vend, steps)
            vm_fwd = np.zeros(v.shape)
            i_fwd = np.zeros(v.shape)
            vm_rev = np.zeros(v.shape)
            i_rev = np.zeros(v.shape)
            i_fwd[:] = np.nan
            i_rev[:] = np.nan

            # Find point after voc
            voc = self.voc(0)
            end_index = np.where(np.diff(np.signbit(v - voc)))[0]
            if (v[end_index] - voc) < 0:
                end_index += 1

            # Find point before jsc
            index = 0
            for v_point in v:
                if v_point >= 0:
                    break
                index += 1
            index -= 1
            start_index = index

            # Turn on output
            self.output_on()

            # Scan rev until we get back to starting point
            index = end_index
            while index >= start_index:
                vm_rev[index], i_rev[index] = self.set_V_measure_I(v[index], lock = False)
                index -= 1

            # Cycle from there until we get out of the quadrant
            index = start_index
            while index <= end_index:
                vm_fwd[index], i_fwd[index] = self.set_V_measure_I(v[index], lock = False)
                index += 1

            # Turn output off
            self.output_off()

        return v, vm_fwd, i_fwd, vm_rev, i_rev
