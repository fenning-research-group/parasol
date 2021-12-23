# from parasol.hardware.scanner import Scanner
# from parasol.hardware.easttester import EastTester
import numpy as np


class Characterization:
    def __init__(self):
        self.et_voltage_step = 0.05

    def scan_jv(self, d, scanner):

        # Get JV mode
        jv_mode = d["jv"]["mode"]

        # Mode 1 = scan fwd then rev
        if jv_mode == 1:

            v, fwd_i, rev_i = scanner.scan_jv(
                vmin=d["jv"]["vmin"], vmax=d["jv"]["vmax"], steps=d["jv"]["steps"]
            )

        return v, fwd_i, rev_i

    #
    def calc_last_vmp(self, d):
        """Grabs last vmpp from tracking if it exists. If not, calculates from JV curves"""

        vmpp = 0
        num_modules = len(d["module_channels"])

        # take vmp from mpp tracking if it has value
        if d["mpp"]["vmpp"] is not None:
            vmpp = d["mpp"]["vmpp"]

        # if we have run all modules on the string use JV curves
        elif d["jv"]["j_fwd"][num_modules - 1] is not None:

            # set voltage to voltage wave, make empty currents
            v = d["jv"]["v"][0]
            j_fwd = 0
            j_rev = 0

            # add up currents (parallel) in fwd/rev, then avg & calc vmpp
            for value in d["jv"]["j_fwd"]:
                j_fwd += value
            j_fwd /= num_modules
            for value in d["jv"]["j_rev"]:
                j_rev += value
            j_rev /= num_modules
            j = (j_fwd + j_rev) / 2
            p = np.array(v * j)
            vmpp = v[np.argmax(p)]

        # else flag with None
        else:
            vmpp = None

        return vmpp

    def track_mpp(self, d, easttester):

        # Get MPP mode
        mpp_mode = d["mpp"]["mode"]

        # Calculate last vmpp
        vmpp_last = self.calc_last_vmp(d)

        # MPP mode 1 = perturb and observe
        if mpp_mode == 1:

            # If we decreased in power, march in opposite direction
            if (d["mpp"]["last_powers"][0] is None) or (
                d["mpp"]["last_powers"][1] is None
            ):
                voltage_step = self.et_voltage_step
            else:
                if d["mpp"]["last_voltages"][1] >= d["mpp"]["last_voltages"][0]:
                    voltage_step = self.et_voltage_step
                else:
                    voltage_step = -self.et_voltage_step

                if d["mpp"]["last_powers"][1] <= d["mpp"]["last_powers"][0]:
                    voltage_step *= -1

            # set the voltage
            v = vmpp_last + voltage_step

        # Ensure voltage is between the easttesters max and min values
        if (v <= d["mpp"]["vmin"]) or (v >= d["mpp"]["vmax"]):
            v = vmpp_last - 2 * voltage_step

        # Run the test

        # # Turn on easttester output, set voltage, measure current
        # eeastester.set_voltage(ch, v)
        # t = time.time()
        # i = et.measure_current(ch)

        # return t, i
