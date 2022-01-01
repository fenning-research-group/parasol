import yaml
import os
import pyvisa
import numpy as np
import matplotlib as mpl
from threading import Lock

mpl.rcParams.update(mpl.rcParamsDefault)

# Set yaml name, load yokogawa info
MODULE_DIR = os.path.dirname(__file__)
with open(os.path.join(MODULE_DIR, "..", "hardwareconstants.yaml"), "r") as f:
    constants = yaml.load(f, Loader=yaml.FullLoader)["yokogawa"]


class Scanner:
    """Scanner package for PARASOL"""

    def __init__(self) -> None:
        """Initliazes the Scanner class for Yokogawa ____"""  # TODO add yoko address

        self.lock = Lock()
        self.connect(constants["address"])
        self.sourcedelay = constants["source_delay"]
        self.sensedelay = constants["sense_delay"]
        self.command_delay = constants["command_delay"]  # None, built in on yoko
        self.inttime = constants["integration_time"]
        self.max_voltage = constants["max_voltage"]
        self.max_current = constants["max_current"]
        self._sourcing_current = False
        self.srcV_measI()

    def connect(self, yoko_address: str) -> None:
        """Connects to the yokogawa

        Args:
            yoko_address (str): GPIB connection address
        """
        rm = pyvisa.ResourceManager()
        self.yoko = rm.open_resource(yoko_address)
        self.yoko.timeout = 10  # 10 seconds

    def srcV_measI(self) -> None:
        """Setup source voltage and measure current"""

        # Basic commands
        self.yoko.write("*RST")  # Reset Factory
        self.yoko.write(":SOUR:FUNC VOLT")  # Source function Voltage
        self.yoko.write(":SOUR:CURR:PROT:LINK ON")  # Limiter tracking ON
        self.yoko.write(":SOUR:CURR:PROT:STAT ON")  # Limiter ON
        self.yoko.write(":SOUR:VOLT:LEV 0V")  # Source level 0 VOLT
        self.yoko.write(":SENS:STAT ON")  # Measurement ON
        self.yoko.write(":SENS:FUNC CURR")  # Measurement function Current
        self.yoko.write(":SENS:AZER:STAT OFF")  # Auto zero OFF
        self.yoko.write(":TRIG:SOUR EXT")  # Trigger source External trigger

        # These settings depend on what we are running
        tempmaxvolt = ":SOUR:VOLT:RANG " + str(self.max_voltage) + "V"
        self.yoko.write(tempmaxvolt)  # Source range setting 1 V
        tempmaxcurr = ":SOUR:CURR:PROT:ULIM " + str(self.max_current) + "A"
        self.yoko.write(tempmaxcurr)  # Limiter 1 mA

        # These commands optimize the speed of our measurement
        tempinttime = ":SENS:ITIM " + str(self.inttime) + "ms"
        self.yoko.write(tempinttime)  # Integration time (20 us to 500 ms)
        tempsourcedelay = ":SOUR:DEL " + str(self.sourcedelay) + "ms"
        self.yoko.write(tempsourcedelay)  # Source delay (15 us to 3600 s)
        tempsensedelay = ":SENS:DEL " + str(self.sensedelay) + "ms"
        self.yoko.write(tempsensedelay)  # Sense Delay --> (0 to 3600 s)
        self._sourcing_current = False

        # Turn output off
        self.yoko.write(":OUTP:STAT OFF")

    def srcI_measV(self) -> None:
        """Setup source current and measure voltage"""
        self.yoko.write("*RST")  # Reset Factory
        self.yoko.write(":SOUR:FUNC CURR")  # Source function Current
        self.yoko.write(":SOUR:VOLT:PROT:LINK ON")  # Limiter tracking ON
        self.yoko.write(":SOUR:VOLT:PROT:STAT ON")  # Limiter ON
        self.yoko.write(":SOUR:CURR:LEV 0A")  # Source level –1.5 VOLT
        self.yoko.write(":SENS:STAT ON")  # Measurement ON
        self.yoko.write(":SENS:FUNC VOLT")  # Measurement function Current
        self.yoko.write(":SENS:AZER:STAT OFF")  # Auto zero OFF
        self.yoko.write(":TRIG:SOUR EXT")  # Trigger source External trigger

        # These settings depend on what we are running
        tempmaxcurr = ":SOUR:CURR:RANG " + str(self.max_current) + "A"
        self.yoko.write(tempmaxcurr)  # Source range setting 0 A
        tempmaxvolt = ":SOUR:VOLT:PROT:ULIM " + str(self.max_voltage) + "V"
        self.yoko.write(tempmaxvolt)  # Limiter 2 V

        # These commands optimize the speed of our measurement
        tempinttime = ":SENS:ITIM " + str(self.inttime)
        self.yoko.write(tempinttime)  # Integration time Minimum
        tempsourcedelay = ":SOUR:DEL " + str(self.sourcedelay)
        self.yoko.write(tempsourcedelay)  # Source delay Minimum
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
        if self._sourcing_current:
            self.srcV_measI()
        tempstr = ":SOUR:VOLT:LEV " + str(v) + "V"
        self.yoko.write(tempstr)

    def set_current(self, i: float) -> None:
        """Sets the current

        Args:
            i (float): desired current (A)
        """
        if not self._sourcing_current:
            self.srcI_measV()
        tempstr = ":SOUR:CURR:LEV " + str(i) + "A"
        self.yoko.write(tempstr)

    def voc(self) -> float:
        """Measures the open circuit voltage

        Returns:
            float: open circut voltage (V)
        """
        self.set_current(0)
        self.output_on()
        voc = float(self._trig_read())
        self.output_off()

        return voc

    def isc(self) -> float:
        """Measures the short circuit current

        Returns:
            float: short circuit current (A)
        """
        self.set_voltage(0)
        self.output_on()
        isc = float(self._trig_read)
        self.output_off()

        return isc

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

        # set up jv mode where # shoud match the if statment below and "" should match name of that test

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

        # Turn on output, set voltage, measure current, turn off output
        self.output_on()

        # Scan forward until we get out of the quadrant
        index = 0

        # find point before 1st point in quadrant
        for v_point in v:
            if v_point >= 0:
                break
            index += 1
        index -= 1
        start_index = index

        # cycle from there until we get out of the quadrant
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

        # find point before jsc
        index = 0
        for v_point in v:
            if v_point >= 0:
                break
            index += 1
        index -= 1
        start_index = index

        # Turn on output, set voltage, measure current, turn off output
        self.output_on()

        # Scan rev until we get back to starting point
        index = end_index
        while index >= start_index:
            self.set_voltage(v[index])
            i_rev[index] = float(self._trig_read())
            index -= 1

        # cycle from there until we get out of the quadrant
        index = start_index
        while index <= end_index:
            self.set_voltage(v[index])
            i_fwd[index] = float(self._trig_read())
            index += 1

        self.output_off()

        return v, i_fwd, i_rev

    # def scan_jv(self, vmin, vmax, steps):
    #     """Scans forward and reverse waves, returning voltage and fwd/reverse current"""
    #     # Run reverse scan
    #     _, rev_i = self.iv_sweep(vstart=vmax, vend=vmin, steps=steps)
    #     # Run forward scan
    #     v, fwd_i = self.iv_sweep(vstart=vmin, vend=vmax, steps=steps)

    #     return v, fwd_i, rev_i
