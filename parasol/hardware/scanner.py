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


def yok_lock(f):
    """Lock Yokogawa"""

    def inner(self, *args, **kwargs):
        with self.lock:
            f(self, *args, **kwargs)

    return inner


class Scanner:
    """Used for JV scanning"""

    def __init__(self) -> None:
        """Initialize Yokogawa"""
        self.lock = Lock()
        self.connect(constants["address"])
        self.RESPONSE_TIME = constants["response_time"]
        self.delay = 0.05
        self._sourcing_current = False
        self.srcV_measI()

    def connect(self, yoko_address):
        """Connect to Yokogawa"""
        rm = pyvisa.ResourceManager()
        self.yoko = rm.open_resource(yoko_address)
        self.yoko.timeout = 10  # 10 seconds

    @yok_lock
    def srcV_measI(self):
        """Turn measurment on: Init settings for source V, measure I"""
        self.yoko.write("*RST")  # Reset Factory
        self.yoko.write(":SOUR:FUNC VOLT")  # Source function Voltage
        self.yoko.write(":SOUR:VOLT:RANG 1V")  # Source range setting 1 V
        self.yoko.write(":SOUR:CURR:PROT:LINK ON")  # Limiter tracking ON
        self.yoko.write(":SOUR:CURR:PROT:ULIM 50mA")  # Limiter 50 mA
        self.yoko.write(":SOUR:CURR:PROT:STAT ON")  # Limiter ON
        self.yoko.write(":SOUR:VOLT:LEV 0V")  # Source level 0 VOLT
        self.yoko.write(":SENS:STAT ON")  # Measurement ON
        self.yoko.write(":SENS:FUNC CURR")  # Measurement function Current
        self.yoko.write(":SENS:ITIM MIN")  # Integration time Minimum
        self.yoko.write(":SENS:AZER:STAT OFF")  # Auto zero OFF
        self.yoko.write(":TRIG:SOUR EXT")  # Trigger source External trigger
        self.yoko.write(":SOUR:DEL MIN")  # Source delay Minimum
        tempdelay = ":SENS:DEL " + str(self.delay) + " ms"
        self.yoko.write(tempdelay)  # Measure delay set in __init__
        self._sourcing_current = False

    @yok_lock
    def srcI_measV(self):
        """Turn measurment on: Init settings for source I, measure V"""
        self.yoko.write("*RST")  # Reset Factory
        self.yoko.write(":SOUR:FUNC CURR")  # Source function Current
        self.yoko.write(":SOUR:CURR:RANG 1A")  # Source range setting 0 A
        self.yoko.write(":SOUR:VOLT:PROT:LINK ON")  # Limiter tracking ON
        self.yoko.write(":SOUR:VOLT:PROT:ULIM 2V")  # Limiter 2 V
        self.yoko.write(":SOUR:VOLT:PROT:STAT ON")  # Limiter ON
        self.yoko.write(":SOUR:CURR:LEV 0A")  # Source level –1.5 VOLT
        self.yoko.write(":SENS:STAT ON")  # Measurement ON
        self.yoko.write(":SENS:FUNC VOLT")  # Measurement function Current
        self.yoko.write(":SENS:ITIM MIN")  # Integration time Minimum
        self.yoko.write(":SENS:AZER:STAT OFF")  # Auto zero OFF
        self.yoko.write(":TRIG:SOUR EXT")  # Trigger source External trigger
        self.yoko.write(":SOUR:DEL MIN")  # Source delay Minimum
        tempdelay = ":SENS:DEL " + str(self.delay) + " ms"  # read delay from __init__
        self.yoko.write(tempdelay)  # Measure delay as set above
        self._sourcing_current = True

    @yok_lock
    def output_on(self):
        """Turn output on"""
        self.yoko.write(":OUTP:STAT ON")

    @yok_lock
    def output_off(self):
        """Turn output off"""
        self.yoko.write(":OUTP:STAT OFF")

    @yok_lock
    def _trig_read(self) -> str:
        """Initializes, apllies trigger, fetches value & returns as string"""
        return self.yoko.query(":INIT;*TRG;:FETC?")

    @yok_lock
    def set_voltage(self, v):
        """Set voltage"""
        if self._sourcing_current:
            self.srcV_measI()
        tempstr = ":SOUR:VOLT:LEV " + str(v) + "V"
        self.yoko.write(tempstr)

    @yok_lock
    def set_current(self, i):
        """Set current"""
        if not self._sourcing_current:
            self.srcI_measV()
        tempstr = ":SOUR:CURR:LEV " + str(i) + "A"
        self.yoko.write(tempstr)

    @yok_lock
    def voc(self) -> float:
        """Measures the open circuit voltage (V)"""
        self.set_current(0)
        self.output_on()
        voc = float(self._trig_read())
        self.output_off()

        return voc

    @yok_lock
    def isc(self) -> float:
        """Measures the short circuit current (A)"""
        self.set_voltage(0)
        self.output_on()
        isc = float(self._trig_read)
        self.output_off()

        return isc

    @yok_lock
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

    @yok_lock
    def scan_jv(self, vmin, vmax, steps):
        """Scans forward and reverse waves, returning voltage and fwd/reverse current"""
        print("trying to scan")
        # Run reverse scan
        _, rev_i = self._single_iv_sweep(vstart=vmax, vend=vmin, steps=steps)
        # Run forward scan
        v, fwd_i = self._single_iv_sweep(vstart=vmin, vend=vmax, steps=steps)

        return v, fwd_i, rev_i
