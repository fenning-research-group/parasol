import numpy as np
import time
import yaml
import os

# Set yaml name, load controller info
MODULE_DIR = os.path.dirname(__file__)
with open(os.path.join(MODULE_DIR, "hardwareconstants.yaml"), "r") as f:
    constants = yaml.load(f, Loader=yaml.FullLoader)["characterization"]


class Characterization:
    def __init__(self):

        self.et_voltage_step = constants["mppt_voltage_step"]

        # set up jv mode where # shoud match the if statment below and "" should match name of that test
        self.jv_options = {
            0: "REV then FWD",
            1: "FWD then REV",
            2: "REV then FWD, Voc to Jsc",
            3: "FWD then REV, Jsc to Voc",
        }

        # set up mpp mode where # shoud match the if statment below and "" should match name of that test
        self.mpp_options = {
            0: "Perturb and Observe (constant V step)",
            1: "75% of Voc --> Untested",
        }

    def scan_jv(self, d, scanner):
        """
        Takes in dictionary and scanner, scans JV, returns v, i fwd, and i rev
        """
        # Get JV mode
        jv_mode = d["jv"]["mode"]

        # Mode 0 = scan rev then fwd
        if jv_mode == 0:

            # Run reverse scan
            _, rev_i = scanner.iv_sweep(
                vstart=d["jv"]["vmax"], vend=d["jv"]["vmin"], steps=d["jv"]["steps"]
            )
            # Run forward scan
            v, fwd_i = scanner.iv_sweep(
                vstart=d["jv"]["vmin"], vend=d["jv"]["vmax"], steps=d["jv"]["steps"]
            )

        # Mode 1 = scan fwd then rev
        elif jv_mode == 1:

            # Run forward scan
            v, fwd_i = scanner.iv_sweep(
                vstart=d["jv"]["vmin"], vend=d["jv"]["vmax"], steps=d["jv"]["steps"]
            )
            # Run reverse scan
            _, rev_i = scanner.iv_sweep(
                vstart=d["jv"]["vmax"], vend=d["jv"]["vmin"], steps=d["jv"]["steps"]
            )

        # Mode = 2 scan rev then fwd (quadrant 4 only)
        elif jv_mode == 2:

            v, fwd_i, rev_i = scanner.iv_sweep_quadrant_rev_fwd(
                vstart=d["jv"]["vmin"], vend=d["jv"]["vmax"], steps=d["jv"]["steps"]
            )

        # Mode = 3, scan fwd then rev (quadrant 4 only)
        elif jv_mode == 3:

            v, fwd_i, rev_i = scanner.iv_sweep_quadrant_fwd_rev(
                vstart=d["jv"]["vmin"], vend=d["jv"]["vmax"], steps=d["jv"]["steps"]
            )

        return v, fwd_i, rev_i

    def track_mpp(self, d, easttester, ch, vmpp_last):
        """Takes last vmpp, dictionary, et, and ch, tracks vmpp for next point, returns t, v, o"""

        mpp_mode = d["mpp"]["mode"]

        # MPP mode 0 is constant perturb and observe
        if mpp_mode == 0:

            # Get voltage step (make sure we are moving toward the MPP)
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

            # get time, set voltage measure current
            t = time.time()
            i = easttester.set_V_measure_I(ch, v)

        # Mode = 1, bias at 75% of Voc
        elif mpp_mode == 1:

            num_modules = len(d["module_channels"])

            # set voltage to voltage wave, make empty currents
            v_vals = d["jv"]["v"][0]
            j_fwd = 0
            j_rev = 0

            # add up currents (parallel) in fwd/rev
            for value in d["jv"]["j_fwd"]:
                j_fwd += value
            j_fwd /= num_modules
            for value in d["jv"]["j_rev"]:
                j_rev += value
            j_rev /= num_modules

            # average forward and reverse current, calc p and vmpp
            j = (j_fwd + j_rev) / 2

            voc = v_vals[np.argmin(np.abs(v_vals))]

            v = voc * 0.75
            t = time.time()
            i = easttester.set_V_measure_I(ch, v)

        # send back vmpp
        return t, v, i

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

            # add up currents (parallel) in fwd/rev
            for value in d["jv"]["j_fwd"]:
                j_fwd += value
            j_fwd /= num_modules
            for value in d["jv"]["j_rev"]:
                j_rev += value
            j_rev /= num_modules

            # average forward and reverse current, calc p and vmpp
            j = (j_fwd + j_rev) / 2
            p = np.array(v * j)
            vmpp = v[np.argmax(p)]

        # else flag with None
        else:
            vmpp = None

        return vmpp
