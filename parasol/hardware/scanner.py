# import pyvisa
import time
import yaml
import os
import numpy as np

import pyvisa
import pandas as pd
import serial
import time
import numpy as np
import matplotlib as mpl
import matplotlib.pyplot as plt
from matplotlib import style

mpl.rcParams.update(mpl.rcParamsDefault)

import math
import csv


from threading import Lock

MODULE_DIR = os.path.dirname(__file__)
with open(os.path.join(MODULE_DIR, "..", "hardwareconstants.yaml"), "r") as f:
    constants = yaml.load(f, Loader=yaml.FullLoader)["yokogawa"]


class Scanner:
    def __init__(self) -> None:
        self.lock = Lock()
        self.connect(constants["address"])  # TODO actually connect
        self.RESPONSE_TIME = constants["response_time"]
        self.delay = 0.05

        self.srcV_measI()
        self._sourcing_current = False

    # Connect to yoko
    def connect(self, yoko_address):
        rm = pyvisa.ResourceManager()
        self.yoko = rm.open_resource(yoko_address)
        self.yoko.timeout = 10  # 10 seconds

        # Turn measurment on: Init settings for source V, measure I

    def srcV_measI(self):
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

    # Turn measurment on: Init settings for source I, measure V
    def srcI_measV(self):
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

    def output_on(self):
        self.yoko.write(":OUTP:STAT ON")  # Output ON

    def output_off(self):
        self.yoko.write(":OUTP:STAT OFF")

    def _trig_read(self) -> str:
        """
        initializes, apllies trigger, fetches value

        Note this returns read value as string.
        """
        return self.yoko.query(":INIT;*TRG;:FETC?")

    def set_voltage(self, v):
        if self._sourcing_current:
            self.srcV_measI()
        tempstr = ":SOUR:VOLT:LEV " + str(v) + "V"
        self.yoko.write(tempstr)

    def set_current(self, i):
        if not self._sourcing_current:
            self.srcI_measV()
        tempstr = ":SOUR:CURR:LEV " + str(i) + "A"
        self.yoko.write(tempstr)

    def voc(self) -> float:
        """measures the open circuit voltage (V)"""
        self.set_current(0)
        self.output_on()
        voc = float(self._trig_read())
        self.output_off()

        return voc

    def isc(self) -> float:
        """measures the short circuit current (Amps)"""

        self.set_voltage(0)
        self.output_on()
        isc = float(self._trig_read)
        self.output_off()

        return isc

    def _single_iv_sweep(self, vstart, vend, steps):
        self.srcV_measI()  # also turns output on
        self.set_voltage(vstart)

        v = np.linspace(vstart, vend, steps)
        i = np.zeros(v.shape)

        self.output_on()
        for idx, v_point in enumerate(v):
            self.set_voltage(v_point)
            i[idx] = float(self._trig_read())
        self.output_off()

        return v, i

    def scan(self, vmin, vmax, steps):
        with self.lock:  # this is important - only allows one thread to access the hardware at a time
            _, rev_i = self.do_jv_sweep(
                vstart=vmax, vend=vmin, steps=steps
            )  # reverse scan first (Voc -> Jsc)
            v, fwd_i = self.do_jv_sweep(vstart=vmin, vend=vmax, steps=steps)

        return v, fwd_i, rev_i
