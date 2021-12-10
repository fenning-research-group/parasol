import yaml
import os
import re
import serial
import time
from threading import Lock


# Set yaml name, load yokogawa info
MODULE_DIR = os.path.dirname(__file__)
with open(os.path.join(MODULE_DIR, "..", "hardwareconstants.yaml"), "r") as f:
    constants = yaml.load(f, Loader=yaml.FullLoader)["easttester"]


def et_lock(f):
    """Locks Easttester"""

    def inner(self, *args, **kwargs):
        with self.lock:
            f(self, *args, **kwargs)

    return inner


class EastTester:
    """used for MPP tracking"""

    def __init__(self, port):
        """initialize and set bounds for measurement (see srcV_measI for bounds)"""
        self.lock = Lock()
        self.connect(port=port)
        self.et_delay = constants["response_time"]
        self.et_v_min = constants["v_min"]
        self.et_v_max = constants["v_shutoff"]
        self.et_i_max = constants["i_shutoff"]
        self.et_avg_num = constants["avg_num"]

        # Set both channels to source voltage and measure current when initialized
        self.srcV_measI(1)
        self.srcV_measI(2)

    def connect(self, port):
        """Connect to Easttester"""
        # Connect using serial, use highest transferrate and shortest timeout
        self.et = serial.Serial(port, baudrate=115200, timeout=0.005)

    @et_lock
    def srcV_measI(self, channel):
        """Setup source voltage and measure I"""
        # Set to external operation, constant voltage, and continuous operation
        self.et.write(("LOAD:TRIGger EXT").encode())
        time.sleep(self.et_delay)
        self.et.write(("CH" + str(channel) + ":MODE CV\n").encode())
        time.sleep(self.et_delay)
        self.et.write(("TRAN" + str(channel) + ":MODE COUT\n").encode())
        time.sleep(self.et_delay)

        # Set ranges for voltage, as well as max and min
        # "NAME" : RANGE (MAX/SHUTOFF)
        # "LOW": 0.1 -> 19.999 (21.000)
        # "HIGH": 0.1 -> 150.000 (155.000)
        self.et.write(("LOAD:VRAN LOW").encode())
        time.sleep(self.et_delay)
        self.et.write(("VOLT" + str(channel) + ":VMIN %f\n" % (self.et_v_min)).encode())
        time.sleep(self.et_delay)
        self.et.write(("VOLT" + str(channel) + ":VMAX %f\n" % (self.et_v_max)).encode())
        time.sleep(self.et_delay)

        # Set range for current, as well as max current (no min feature)
        # "NAME" : RANGE (MAX/SHUTOFF)
        # "LOW": 0 -> 3.000 (3.3)
        # "HIGH": 0 -> 20.000 (22.0)
        self.et.write(("LOAD:CRAN LOW").encode())
        time.sleep(self.et_delay)
        self.et.write(("CURR" + str(channel) + ":IMAX %f\n" % (self.et_i_max)).encode())
        time.sleep(self.et_delay)

        # Set max power output
        # "NAME" : RANGE (MAX/SHUTOFF)
        # ALL: 0 --> 200 (220)
        self.et.write(
            (
                "POWE" + str(channel) + ":PMAX %f\n" % (self.et_v_max * self.et_i_max)
            ).encode()
        )
        time.sleep(self.et_delay)

        # Close channel
        self.et.write(("CH" + str(channel) + ":SW OFF\n").encode())
        time.sleep(self.et_delay)

    @et_lock
    def output_on(self, channel):
        """Turns on output"""
        self.et.write(("CH" + str(channel) + ":SW ON\n").encode())
        time.sleep(self.et_delay)

    @et_lock
    def output_off(self, channel):
        """Turns off output"""
        self.et.write(("CH" + str(channel) + ":SW OFF\n").encode())
        time.sleep(self.et_delay)

    @et_lock
    def set_voltage(self, channel, voltage):
        """Sets voltage"""
        self.et.write(("VOLT" + str(channel) + ":CV %f\n" % (voltage)).encode())
        time.sleep(self.et_delay)

    @et_lock
    def measure_current(self, channel):
        """Measure current several times and average"""
        i = 0
        curr_tot = 0

        # The easttester is not very accurate, so we need to average several times
        while i < self.et_avg_num:

            self.et.write(("MEAS" + str(channel) + ":CURR?\n").encode())
            time.sleep(self.et_delay)

            curr = self.et.readlines()[-1]
            curr = curr.decode("utf-8")
            curr = re.findall("\d*\.?\d+", curr)
            curr = float(curr[0])
            curr_tot += curr
            i += 1

        curr_tot /= self.et_avg_num

        return curr_tot
