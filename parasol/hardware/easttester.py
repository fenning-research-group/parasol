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

# We have several workers managing east tester so we need to make sure two dont try to work at the same time
def et_lock(f):
    """Locks easttester

    Args:
        f (function): any function that needs to be locked
    """

    def inner(self, *args, **kwargs):
        with self.lock:
            return f(self, *args, **kwargs)

    return inner


class EastTester:
    """EastTester package for PARASOL"""

    def __init__(self, port: str) -> None:
        """Initliazes the Eastester class for EastTester 5420

        Args:
            port (string): COM port connection to easttester
        """

        self.lock = Lock()
        self.connect(port=port)

        # Get constants from hardwareconstants
        self.source_delay = constants["source_delay"]
        self.sense_delay = constants["sense_delay"]
        self.et_delay = constants["command_delay"]
        self.et_avg_num = constants["avg_num"]
        self.et_v_max = constants["max_voltage"]
        self.et_i_max = constants["max_current"]
        self.et_v_min = constants["v_min"]
        self.voltage_range = constants["voltage_range"]
        self.current_range = constants["current_range"]

        # Set both channels to source voltage and measure current when initialized
        self._sourcing_current = [None, False, False]
        self.srcV_measI(1)
        self.srcV_measI(2)

    def connect(self, port: str) -> None:
        """Connects to the easttester at the given port

        Args:
            port (string): COM port connection to easttester
        """

        # Connect using serial, use highest transferrate and shortest timeout
        self.et = serial.Serial(port, baudrate=115200, timeout=0.005)

    # untested
    def srcI_measV(self, channel: int) -> None:
        """Setup source current and measure voltage

        Args:
            channel (int or string): eastester channel to alter
        """

        # Set to constant voltage, and continuous operation
        self.et.write(("CH" + str(channel) + ":MODE CC\n").encode())
        time.sleep(self.et_delay)
        # self.et.write(("TRAN" + str(channel) + ":MODE COUT\n").encode())
        # time.sleep(self.et_delay)

        # Set ranges for voltage, as well as max and min
        # "NAME" : RANGE (MAX/SHUTOFF)
        # "LOW": 0.1 -> 19.999 (21.000)
        # "HIGH": 0.1 -> 150.000 (155.000)
        self.et.write(
            ("LOAD" + str(channel) + ":VRAN " + str(self.voltage_range)).encode()
        )
        time.sleep(self.et_delay)
        self.et.write(("VOLT" + str(channel) + ":VMIN %f\n" % (self.et_v_min)).encode())
        time.sleep(self.et_delay)
        self.et.write(("VOLT" + str(channel) + ":VMAX %f\n" % (self.et_v_max)).encode())
        time.sleep(self.et_delay)

        # Set range for current, as well as max current (no min feature)
        # "NAME" : RANGE (MAX/SHUTOFF)
        # "LOW": 0 -> 3.000 (3.3)
        # "HIGH": 0 -> 20.000 (22.0)
        self.et.write(
            ("LOAD" + str(channel) + ":CRAN " + str(self.current_range)).encode()
        )
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

    def srcV_measI(self, channel: int) -> None:
        """Setup source voltage and measure current

        Args:
            channel (int or string): eastester channel to alter
        """

        # Set to constant voltage, and continuous operation
        self.et.write(("CH" + str(channel) + ":MODE CV\n").encode())
        time.sleep(self.et_delay)
        # self.et.write(("TRAN" + str(channel) + ":MODE COUT\n").encode())
        # time.sleep(self.et_delay)

        # Set ranges for voltage, as well as max and min
        # "NAME" : RANGE (MAX/SHUTOFF)
        # "LOW": 0.1 -> 19.999 (21.000)
        # "HIGH": 0.1 -> 150.000 (155.000)
        self.et.write(
            ("LOAD" + str(channel) + ":VRAN " + str(self.voltage_range)).encode()
        )
        time.sleep(self.et_delay)
        self.et.write(("VOLT" + str(channel) + ":VMIN %f\n" % (self.et_v_min)).encode())
        time.sleep(self.et_delay)
        self.et.write(("VOLT" + str(channel) + ":VMAX %f\n" % (self.et_v_max)).encode())
        time.sleep(self.et_delay)

        # Set range for current, as well as max current (no min feature)
        # "NAME" : RANGE (MAX/SHUTOFF)
        # "LOW": 0 -> 3.000 (3.3)
        # "HIGH": 0 -> 20.000 (22.0)
        self.et.write(
            ("LOAD" + str(channel) + ":CRAN " + str(self.current_range)).encode()
        )
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
    def output_on(self, channel: int) -> None:
        """Turns output on

        Args:
            channel (int or string): eastester channel to alter
        """

        self.et.write(("CH" + str(channel) + ":SW ON\n").encode())
        time.sleep(
            self.source_delay
        )  # if this delay reduced we get issues in measuring current (first point low)

    @et_lock
    def output_off(self, channel: int) -> None:
        """Turns output off

        Args:
            channel (int or string): eastester channel to alter
        """

        self.et.write(("CH" + str(channel) + ":SW OFF\n").encode())
        time.sleep(
            self.source_delay
        )  # if this delay reduced we get issues in measuring current (first point low)

    @et_lock
    def set_voltage(self, channel: int, voltage: float) -> None:
        """Sets voltage

        Args:
            channel (int or string): eastester channel to alter
            voltage (float): desired voltage (V)
        """

        # New
        if self._sourcing_current[channel] == True:
            self.srcV_measI(channel)
            self._sourcing_current[channel] = False

        self.et.write(("VOLT" + str(channel) + ":CV %f\n" % (voltage)).encode())
        time.sleep(self.source_delay)

    # untested
    @et_lock
    def set_current(self, channel: int, current: float) -> None:
        """Sets current

        Args:
            channel (int or string): eastester channel to alter
            current (float): desired current (A)
        """

        if self._sourcing_current[channel] == False:
            self.srcI_measV(channel)
            self._sourcing_current[channel] = True

        self.et.write(("CURR" + str(channel) + ":CC %f\n" % (current)).encode())

    @et_lock
    def measure_current(self, channel: int) -> float:
        """Measures current several times and then averages (number defined in hardwareconstants.yaml)

        Args:
            channel (int or string): eastester channel to alter

        Returns:
            float: current (A) reading
        """

        i = 0
        curr_tot = 0
        # To avoid marching in the wrong direction we need to average here
        while i < self.et_avg_num:

            self.et.write(("MEAS" + str(channel) + ":CURR?\n").encode())
            time.sleep(self.sense_delay)
            curr = self.et.readlines()
            curr = curr[-1].decode("utf-8")
            curr = re.findall("\d*\.?\d+", curr)
            curr = float(curr[0])
            curr_tot += curr
            i += 1

        curr_tot = curr_tot / self.et_avg_num

        return curr_tot

    # untested
    @et_lock
    def measure_voltage(self, channel: int) -> float:
        """Measures voltage several times and then averages (number defined in hardwareconstants.yaml)

        Args:
            channel (int or string): eastester channel to alter

        Returns:
            float: voltage (V) reading
        """
        i = 0
        volt_tot = 0
        # To avoid marching in the wrong direction we need to average here
        while i < self.et_avg_num:

            self.et.write(("MEAS" + str(channel) + ":VOLT?\n").encode())
            time.sleep(self.sense_delay)
            volt = self.et.readlines()[-1]
            volt = volt.decode("utf-8")
            volt = re.findall("\d*\.?\d+", volt)
            volt = float(volt[0])
            volt_tot += volt
            i += 1

        volt_tot = volt_tot / self.et_avg_num

        return volt_tot

    # untested
    def voc(self, channel: int) -> float:
        """Gets open circut voltage: V where I = 0

        Args:
            channel (int or string): eastester channel to alter

        Returns:
            float: open circut voltage (V)
        """
        self.set_current(channel, 0)
        voc = self.measure_voltage(channel)

        return voc

    # untested
    def isc(self, channel: int) -> float:
        """Gets short circut current: I where V = 0

        Args:
            channel (int or string): eastester channel to alter

        Returns:
            float: short circut current (A)
        """

        self.set_voltage(channel, 0)
        jsc = self.measure_current(channel)

        return jsc

    # no et lock, it calls functions with them
    def set_V_measure_I(self, channel: int, voltage: float) -> float:
        """Sets voltage and measures current

        Args:
            channel (int or string): eastester channel to alter
            voltage (float): voltage (V)

        Returns:
            float: current (A) reading
        """
        self.set_voltage(channel, voltage)
        curr = self.measure_current(channel)
        return curr

    def set_I_measure_V(self, channel: int, voltage: float) -> float:
        """Sets current and measures voltage

        Args:
            channel (int or string): eastester channel to alter
            voltage (float): current (A)

        Returns:
            float: voltage (V) reading
        """

        self.set_current(channel, voltage)
        volt = self.measure_voltage(channel)
        return volt
