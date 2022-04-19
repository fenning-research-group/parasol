import yaml
import os
import pyvisa
import numpy as np
import matplotlib as mpl
from threading import Lock

from parasol.hardware.port_finder import get_port


mpl.rcParams.update(mpl.rcParamsDefault)

# Set module directory, import constants from yaml file
MODULE_DIR = os.path.dirname(__file__)
with open(os.path.join(MODULE_DIR, "..", "hardwareconstants.yaml"), "r") as f:
    constants = yaml.safe_load(f)["yokogawa"]  # , Loader=yaml.FullLoader)["yokogawa"]


class Scanner:
    """Scanner package for PARASOL"""

    def __init__(self) -> None:
        """Initliazes the Scanner class for Yokogawa GS610"""

        # Create lock
        self.lock = Lock()

        # Load constants
        self.sourcedelay = constants["source_delay"]
        self.sensedelay = constants["sense_delay"]
        self.command_delay = constants["command_delay"]
        self.inttime = constants["integration_time"]
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

    def srcV_measI(self) -> None:
        """Setup source voltage and measure current"""

        # Basic commands
        self.yoko.write("*RST")  # Reset factory
        self.yoko.write(":SOUR:FUNC VOLT")  # Source function voltage
        self.yoko.write(":SOUR:CURR:PROT:LINK ON")  # Limiter tracking on
        self.yoko.write(":SOUR:CURR:PROT:STAT ON")  # Limiter on
        self.yoko.write(":SOUR:VOLT:LEV 0V")  # Source level 0 V
        self.yoko.write(":SENS:STAT ON")  # Measurement on
        self.yoko.write(":SENS:FUNC CURR")  # Measurement function current
        self.yoko.write(":SENS:AZER:STAT OFF")  # Auto zero off
        self.yoko.write(":TRIG:SOUR EXT")  # Trigger source external trigger

        # These settings depend on what we are running
        tempmaxvolt = ":SOUR:VOLT:RANG " + str(self.max_voltage) + "V"
        self.yoko.write(
            tempmaxvolt
        )  # Source voltage range setting to user specification
        tempmaxcurr = ":SOUR:CURR:PROT:ULIM " + str(self.max_current) + "A"
        self.yoko.write(tempmaxcurr)  # Limit current to user specification

        # These commands optimize the speed of our measurement
        tempinttime = ":SENS:ITIM " + str(self.inttime) + "ms"
        self.yoko.write(tempinttime)  # Integration time in ms
        tempsourcedelay = ":SOUR:DEL " + str(self.sourcedelay) + "ms"
        self.yoko.write(tempsourcedelay)  # Source delay minmum in ms
        tempsensedelay = ":SENS:DEL " + str(self.sensedelay) + "ms"
        self.yoko.write(tempsensedelay)  # Sense delay minmum in ms
        self._sourcing_current = False

        # Turn output off
        self.yoko.write(":OUTP:STAT OFF")

    def srcI_measV(self) -> None:
        """Setup source current and measure voltage"""

        # Basic commands
        self.yoko.write("*RST")  # Reset factory
        self.yoko.write(":SOUR:FUNC CURR")  # Source function current
        self.yoko.write(":SOUR:VOLT:PROT:LINK ON")  # Limiter tracking on
        self.yoko.write(":SOUR:VOLT:PROT:STAT ON")  # Limiter on
        self.yoko.write(":SOUR:CURR:LEV 0A")  # Source level 0 V
        self.yoko.write(":SENS:STAT ON")  # Measurement on
        self.yoko.write(":SENS:FUNC VOLT")  # Measurement function voltage
        self.yoko.write(":SENS:AZER:STAT OFF")  # Auto zero off
        self.yoko.write(":TRIG:SOUR EXT")  # Trigger source external trigger

        # These settings depend on what we are running
        tempmaxcurr = ":SOUR:CURR:RANG " + str(self.max_current) + "A"
        self.yoko.write(
            tempmaxcurr
        )  # Source current range setting to user specification
        tempmaxvolt = ":SOUR:VOLT:PROT:ULIM " + str(self.max_voltage) + "V"
        self.yoko.write(tempmaxvolt)  # Limit voltage to user specification

        # These commands optimize the speed of our measurement
        tempinttime = ":SENS:ITIM " + str(self.inttime)
        self.yoko.write(tempinttime)  # Integration time minimum
        tempsourcedelay = ":SOUR:DEL " + str(self.sourcedelay)
        self.yoko.write(tempsourcedelay)  # Source delay minimum
        tempsensedelay = ":SENS:DEL " + str(self.sensedelay) + " ms"
        self.yoko.write(tempsensedelay)  # Measure delay as set above
        self._sourcing_current = True

        # Turn output off
        self.yoko.write(":OUTP:STAT OFF")

    def output_on(self) -> None:
        """Turn output on"""

        self.yoko.write(":OUTP:STAT ON")

    def output_off(self) -> None:
        """Turn output off"""

        self.yoko.write(":OUTP:STAT OFF")

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

        # Set current (A)
        tempstr = ":SOUR:CURR:LEV " + str(i) + "A"
        self.yoko.write(tempstr)

    def voc(self) -> float:
        """Measures the open circuit voltage

        Returns:
            float: open circut voltage (V)
        """

        # Set current to 0, measure voltage (V)
        self.set_current(0)
        self.output_on()
        vocval = float(self._trig_read())
        self.output_off()

        return vocval

    # TODO: Isc called from check orientation can overlap with scanner recieving other commands and crash it. Need to fix this.
    def isc(self) -> float:
        """Measures the short circuit current

        Returns:
            float: short circuit current (A)
        """

        # Set voltage to 0, measure current (A)
        self.set_voltage(0)
        self.output_on()
        iscval = float(self._trig_read())
        self.output_off()

        return iscval

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

        # Make empty numpy arrays for data
        v = np.linspace(vstart, vend, steps)
        i = np.zeros(v.shape)

        # Turn on output, set voltage, measure current, turn off output
        self.output_on()
        for idx, v_point in enumerate(v):
            self.set_voltage(v_point)
            i[idx] = float(self._trig_read())
        self.output_off()

        # Flip reverse scan order so that it aligns with voltage
        if abs(vstart) > abs(vend):
            i = i[::-1]

        return v, i

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

        # Make empty numpy arrays for data
        v = np.linspace(vstart, vend, steps)
        i_fwd = np.zeros(v.shape)
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
            self.set_voltage(v[index])
            i_fwd[index] = float(self._trig_read())
            if i_fwd[index] > 0:
                break
            index += 1

        # Scan backwards until we get back to starting point
        while index >= start_index:
            self.set_voltage(v[index])
            i_rev[index] = float(self._trig_read())
            index -= 1

        # Turn output off
        self.output_off()

        return v, i_fwd, i_rev

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

        # Make empty numpy arrays for data
        v = np.linspace(vstart, vend, steps)
        i_fwd = np.zeros(v.shape)
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
            self.set_voltage(v[index])
            i_rev[index] = float(self._trig_read())
            index -= 1

        # Cycle from there until we get out of the quadrant
        index = start_index
        while index <= end_index:
            self.set_voltage(v[index])
            i_fwd[index] = float(self._trig_read())
            index += 1

        # Turn output off
        self.output_off()

        return v, i_fwd, i_rev
