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
    """Used for JV scanning"""

    def __init__(self) -> None:
        """Initialize Yokogawa"""
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

    def connect(self, yoko_address):
        """Connect to Yokogawa"""
        rm = pyvisa.ResourceManager()
        self.yoko = rm.open_resource(yoko_address)
        self.yoko.timeout = 10  # 10 seconds

    def srcV_measI(self):
        """Turn measurment on: Init settings for source V, measure I"""

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
        tempinttime = ":SENS:ITIM " + str(self.inttime)
        self.yoko.write(tempinttime)  # Integration time (20 us to 500 ms)
        tempsourcedelay = ":SOUR:DEL " + str(self.sourcedelay)
        self.yoko.write(tempsourcedelay)  # Source delay (15 us to 3600 s)
        tempsensedelay = ":SENS:DEL " + str(self.sensedelay) + " ms"
        self.yoko.write(tempsensedelay)  # Sense Delay --> (0 to 3600 s)
        self._sourcing_current = False

        # Turn output off
        self.yoko.write(":OUTP:STAT OFF")

    def srcI_measV(self):
        """Turn measurment on: Init settings for source I, measure V"""
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

    def output_on(self):
        """Turn output on"""
        self.yoko.write(":OUTP:STAT ON")

    def output_off(self):
        """Turn output off"""
        self.yoko.write(":OUTP:STAT OFF")

    def _trig_read(self) -> str:
        """Initializes, apllies trigger, fetches value & returns as string"""
        return self.yoko.query(":INIT;*TRG;:FETC?")

    def set_voltage(self, v):
        """Set voltage"""
        if self._sourcing_current:
            self.srcV_measI()
        tempstr = ":SOUR:VOLT:LEV " + str(v) + "V"
        self.yoko.write(tempstr)

    def set_current(self, i):
        """Set current"""
        if not self._sourcing_current:
            self.srcI_measV()
        tempstr = ":SOUR:CURR:LEV " + str(i) + "A"
        self.yoko.write(tempstr)

    def voc(self) -> float:
        """Measures the open circuit voltage (V)"""
        self.set_current(0)
        self.output_on()
        voc = float(self._trig_read())
        self.output_off()

        return voc

    def isc(self) -> float:
        """Measures the short circuit current (A)"""
        self.set_voltage(0)
        self.output_on()
        isc = float(self._trig_read)
        self.output_off()

        return isc

    def _single_iv_sweep(self, vstart, vend, steps):
        """Runs a single IV sweep"""
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

    def scan_jv(self, vmin, vmax, steps):
        """Scans forward and reverse waves, returning voltage and fwd/reverse current"""
        # Run reverse scan
        _, rev_i = self._single_iv_sweep(vstart=vmax, vend=vmin, steps=steps)
        # Run forward scan
        v, fwd_i = self._single_iv_sweep(vstart=vmin, vend=vmax, steps=steps)

        return v, fwd_i, rev_i
