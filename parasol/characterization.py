import numpy as np
import time
import yaml
import os

# Set module directory, import constants from yaml file
MODULE_DIR = os.path.dirname(__file__)
with open(os.path.join(MODULE_DIR, "hardwareconstants.yaml"), "r") as f:
    constants = yaml.safe_load(f)["characterization"]


class Characterization:
    """Characterization package for PARASOL"""

    def __init__(self) -> None:
        """Initializes the Characterization class"""

        # Get constants
        self.et_voltage_step = constants["mppt_voltage_step"]

        # Set up JV mode: # should match the if statment below and "" should be the desired name
        self.jv_options = {
            0: "REV then FWD",
            1: "FWD then REV",
            2: "REV then FWD, Voc to Jsc",
            3: "FWD then REV, Jsc to Voc",
        }

        # Set up MPP mode: # shoud match the if statment below and "" should be the desired name
        self.mpp_options = {
            0: "Perturb and Observe (constant V step)",
            1: "75% of Voc --> Untested",
        }

    def scan_jv(self, d: dict, scanner: object) -> np.ndarray:
        """Conducts JV scan

        Args:
            d (dict): dictionary containing all necessary information (defined in controller.py)
            scanner (object): pointer to the controller for the scanner

        Returns:
            np.ndarray: voltage (V) values
            np.ndarray: FWD voltage measured (V) values
            np.ndarray: FWD current (A) values
            np.ndarray: REV voltage measured (V) values
            np.ndarray: REV current (A) values
        """

        # Get JV mode
        jv_mode = d["jv"]["mode"]

        # Mode 0 = scan rev then fwd
        if jv_mode == 0:

            # Run reverse scan
            _, rev_vm, rev_i = scanner.iv_sweep(
                vstart=d["jv"]["vmax"], vend=d["jv"]["vmin"], steps=d["jv"]["steps"]
            )
            # Run forward scan
            v, fwd_vm, fwd_i = scanner.iv_sweep(
                vstart=d["jv"]["vmin"], vend=d["jv"]["vmax"], steps=d["jv"]["steps"]
            )

        # Mode 1 = scan fwd then rev
        elif jv_mode == 1:

            # Run forward scan
            v, fwd_vm, fwd_i = scanner.iv_sweep(
                vstart=d["jv"]["vmin"], vend=d["jv"]["vmax"], steps=d["jv"]["steps"]
            )
            # Run reverse scan
            _, rev_vm, rev_i = scanner.iv_sweep(
                vstart=d["jv"]["vmax"], vend=d["jv"]["vmin"], steps=d["jv"]["steps"]
            )

        # Mode = 2 scan rev then fwd (quadrant 4 only)
        elif jv_mode == 2:

            v, fwd_vm, fwd_i, rev_vm, rev_i = scanner.iv_sweep_quadrant_rev_fwd(
                vstart=d["jv"]["vmin"], vend=d["jv"]["vmax"], steps=d["jv"]["steps"]
            )

        # Mode = 3, scan fwd then rev (quadrant 4 only)
        elif jv_mode == 3:

            v, fwd_vm, fwd_i, rev_vm, rev_i = scanner.iv_sweep_quadrant_fwd_rev(
                vstart=d["jv"]["vmin"], vend=d["jv"]["vmax"], steps=d["jv"]["steps"]
            )

        return v, fwd_vm, fwd_i, rev_vm, rev_i
    

    def track_mpp(
        self, d: dict, chroma: object, ch: int, vmpp_last: float
    ) -> np.ndarray:
        """Tracks Vmpp for next point

        Args:
            d (dict): dictionary containing all necessary information (defined in controller.py)
            chroma (object): pointer to the contoller for the chroma
            ch (int): chroma channel
            vmpp_last (float): last maximum power point tracking voltage (V)

        Returns:
            np.ndarray: time (epoch) values
            np.ndarray: voltage applied (V) values
            np.ndarray: voltage measured (V) values
            np.ndarray: current (A) values
        """

        # Get MPP mode
        mpp_mode = d["mpp"]["mode"]

        # # Perturb and observe, standard
        # if mpp_mode == 0:

        #     # If we have not tracked yet, step in standard direction from MPP calc from JV, else run algorithm
        #     if (d["mpp"]["last_powers"][0] is None) or (
        #             d["mpp"]["last_powers"][1] is None
        #         ):
        #             v= vmpp_last + self.et_voltage_step
        #             t = time.time()
        #             i = chroma.set_V_measure_I(ch, v)

        #     else:

        #         # calcualte changes in I, P, V
        #         delta_v = d["mpp"]["last_voltages"][1] - d["mpp"]["last_voltages"][0]
        #         delta_i = d["mpp"]["last_currents"][1] - d["mpp"]["last_currents"][0]
        #         delta_p = d["mpp"]["last_powers"][1] - d["mpp"]["last_powers"][0]

        #         # apply standard perturb and observe logic
        #         if delta_p == 0:
        #             v = vmpp_last
        #         elif delta_p > 0:
        #             if delta_v > 0:
        #                 v = vmpp_last + self.et_voltage_step
        #             else:
        #                 v = vmpp_last - self.et_voltage_step
        #         elif delta_p < 0:
        #             if delta_v > 0:
        #                 v = vmpp_last - self.et_voltage_step
        #             else:
        #                 v = vmpp_last + self.et_voltage_step

        #         # ensure we are within bounds and in correct quadrant
        #         if v <= max(d["mpp"]["vmin"], 0):
        #             v = vmpp_last + 2 * self.et_voltage_step
        #         elif (v >= d["mpp"]["vmax"]) or (d["mpp"]["last_currents"][1] < 0):
        #             v = vmpp_last - 2 * self.et_voltage_step

        #         # ensure we arent sitting in the noise
        #         if 0 <= d["mpp"]["last_currents"][1] <= 1:
        #             v = max(self.et_voltage_step, d["mpp"]["vmin"] + self.et_voltage_step)

        #         # bias at calc point
        #         t = time.time()
        #         i = chroma.set_V_measure_I(ch, v)

        # # Perturb and observe, two measurements to eliminate time axes
        # elif mpp_mode == 1:

        #      # If we have not tracked yet, step in standard direction from MPP calc from JV, else run algorithm
        #     if (d["mpp"]["last_powers"][0] is None) or (
        #             d["mpp"]["last_powers"][1] is None
        #         ):
        #             v= vmpp_last + self.et_voltage_step
        #             t = time.time()
        #             i = chroma.set_V_measure_I(ch, v)

        #     else:

        #         # calcualte changes in I, P, V
        #         delta_v = d["mpp"]["last_voltages"][1] - d["mpp"]["last_voltages"][0]
        #         delta_i = d["mpp"]["last_currents"][1] - d["mpp"]["last_currents"][0]
        #         delta_p = d["mpp"]["last_powers"][1] - d["mpp"]["last_powers"][0]

        #         # standard perturb and observe logic
        #         if delta_p == 0:
        #             v = vmpp_last
        #         elif delta_p > 0:
        #             if delta_v > 0:
        #                 v = vmpp_last + self.et_voltage_step
        #             else:
        #                 v = vmpp_last - self.et_voltage_step
        #         elif delta_p < 0:
        #             if delta_v > 0:
        #                 v = vmpp_last - self.et_voltage_step
        #             else:
        #                 v = vmpp_last + self.et_voltage_step

        #         # ensure we are within bounds and in correct quadrant
        #         if v <= max(d["mpp"]["vmin"], 0):
        #             v = vmpp_last + 2 * self.et_voltage_step
        #         elif (v >= d["mpp"]["vmax"]) or (d["mpp"]["last_currents"][1] < 0):
        #             v = vmpp_last - 2 * self.et_voltage_step

        #         # ensure we arent sitting in the noise
        #         if 0 <= d["mpp"]["last_currents"][1] <= 1:
        #             v = max(self.et_voltage_step, d["mpp"]["vmin"] + self.et_voltage_step)

        #         # bias at calc point and last point, determine greater value
        #         p0 = chroma.set_V_measure_I(ch, vmpp_last)*vmpp_last
        #         p1 = chroma.set_V_measure_I(ch, v)*v
        #         if p1 > p0:
        #             v_set = v
        #         else:
        #             v_set = vmpp_last

        #         # set voltage and measure
        #         t = time.time()
        #         i = chroma.set_V_measure_I(ch, v_set)

        # # Perturb and observe, two measurements to eliminate time axes, Hidenori SAITO no check for stabilization
        # # DOI:10.5796/electrochemistry.20-00022
        # elif mpp_mode == 2:

        #      # If we have not tracked yet, step in standard direction from MPP calc from JV, else run algorithm
        #     if (d["mpp"]["last_powers"][0] is None) or (
        #             d["mpp"]["last_powers"][1] is None
        #         ):
        #             v= vmpp_last + self.et_voltage_step
        #             t = time.time()
        #             i = chroma.set_V_measure_I(ch, v)

        #     else:

        #         # calcualte changes in I, P, V
        #         delta_v = d["mpp"]["last_voltages"][1] - d["mpp"]["last_voltages"][0]
        #         delta_i = d["mpp"]["last_currents"][1] - d["mpp"]["last_currents"][0]
        #         delta_p = d["mpp"]["last_powers"][1] - d["mpp"]["last_powers"][0]

        #         # standard perturb and observe logic
        #         if delta_p == 0:
        #             v = vmpp_last
        #         elif delta_p > 0:
        #             if delta_v > 0:
        #                 v = vmpp_last + self.et_voltage_step
        #             else:
        #                 v = vmpp_last - self.et_voltage_step
        #         elif delta_p < 0:
        #             if delta_v > 0:
        #                 v = vmpp_last - self.et_voltage_step
        #             else:
        #                 v = vmpp_last + self.et_voltage_step

        #         # ensure we are within bounds and in correct quadrant
        #         if v <= max(d["mpp"]["vmin"], 0):
        #             v = vmpp_last + 2 * self.et_voltage_step
        #         elif (v >= d["mpp"]["vmax"]) or (d["mpp"]["last_currents"][1] < 0):
        #             v = vmpp_last - 2 * self.et_voltage_step

        #         # ensure we arent sitting in the noise
        #         if 0 <= d["mpp"]["last_currents"][1] <= 1:
        #             v = max(self.et_voltage_step, d["mpp"]["vmin"] + self.et_voltage_step)

        #         # bias at calc point and last point, determine greater value
        #         firstv = max((min(vmpp_last, v)-self.et_voltage_step),(d["mpp"]["vmin"]+ self.et_voltage_step)) # smallest point - vstep or vmin+vstep
        #         seccondv = min(vmpp_last, v) # smallest point
        #         thirdv = max(vmpp_last, v) # smallest point + vstep

        #         # set voltage and measure
        #         _ = chroma.set_V_measure_I(ch, firstv)*firstv
        #         p0 = chroma.set_V_measure_I(ch, seccondv)*seccondv
        #         p1 = chroma.set_V_measure_I(ch, thirdv)*thirdv

        #         # compare last two measurements
        #         if p1 > p0:
        #             v_set = thirdv
        #         else:
        #             v_set = seccondv

        #         # set voltage and measure at max power point
        #         t = time.time()
        #         i = chroma.set_V_measure_I(ch, v_set)

        # # Modified perturb and observe: taken from David Sanz Morales Thesis
        # # http://lib.tkk.fi/Dipl/2010/urn100399.pdf
        # elif mpp_mode == 3:

        # if mpp_mode == 0:
        #     # If we have not tracked yet, step in standard direction from MPP calc from JV, else run algorithm
        #     if (d["mpp"]["last_powers"][0] is None) or (
        #         d["mpp"]["last_powers"][1] is None
        #     ):
        #         v = vmpp_last + self.et_voltage_step
        #         t = time.time()
        #         i = chroma.set_V_measure_I(ch, v)

        #     else:
        #         # Calcualte changes in I, P, V
        #         delta_v = d["mpp"]["last_voltages"][1] - d["mpp"]["last_voltages"][0]
        #         delta_i = d["mpp"]["last_currents"][1] - d["mpp"]["last_currents"][0]
        #         delta_p = d["mpp"]["last_powers"][1] - d["mpp"]["last_powers"][0]

        #         # Modified perturb and observe logic
        #         # TODO: Not working great. If we get stuck at 0 then dv = 0 and we get v_inc = 0 unless we decrease in energy.
        #         if delta_p == 0:
        #             v_increase = 0
        #         elif delta_i < 0:
        #             if delta_i / delta_p == 0:
        #                 v_increase = 0
        #             elif delta_i / delta_p < 0:
        #                 v_increase = 1
        #             else:
        #                 v_increase = -1
        #         else:
        #             if delta_v / delta_p == 0:
        #                 v_increase = 0
        #             elif delta_v / delta_p > 0:
        #                 v_increase = 1
        #             else:
        #                 v_increase = -1

        #         # Set voltage using constant step + direction determined above
        #         v = vmpp_last + v_increase * self.et_voltage_step

        #         # Ensure we are within bounds and in correct quadrant
        #         if v < max(d["mpp"]["vmin"], 0.0):
        #             v = vmpp_last + 2 * self.et_voltage_step
        #         elif (v > d["mpp"]["vmax"]) or (d["mpp"]["last_currents"][1] < 0.0):
        #             v = vmpp_last - 2 * self.et_voltage_step

        #         # bias at calc point
        #         t = time.time()
        #         i = chroma.set_V_measure_I(ch, v)

        # Constant perturb and observe (1 = newest, 0 = oldest)
        if mpp_mode == 0:

            # If we just have one scan, use native voltage step (+)
            if (d["mpp"]["last_powers"][0] is None) or (
                d["mpp"]["last_powers"][1] is None
            ):
                voltage_step = self.et_voltage_step

            # If we have two scans saved work out direction of voltage step
            else:
                # if the most recent voltage >= voltage before it, use native voltage step (+)
                if d["mpp"]["last_voltages"][1] >= d["mpp"]["last_voltages"][0]:
                    voltage_step = self.et_voltage_step
                # if the most recent voltage < voltage before it, use opposite voltage step (-)
                else:
                    voltage_step = -self.et_voltage_step

                # if power isnt increasing, invert voltage step to move in the other direction
                if d["mpp"]["last_powers"][1] <= d["mpp"]["last_powers"][0]:
                    voltage_step *= -1

            # set the voltage equal to last voltage + voltage step (determined above)
            v = vmpp_last + voltage_step

            # Ensure min v,0 < voltage < max v, else step in the other direction
            if (v <= max(d["mpp"]["vmin"], 0)) or (v >= d["mpp"]["vmax"]):
                voltage_step *= -1
                v = vmpp_last + 2 * voltage_step

            # get time, set voltage measure current
            t = time.time()
            vm, i = chroma.set_V_measure_I(ch, v)

        # Mode = 1, bias at 75% of Voc
        elif mpp_mode == 1:

            num_modules = len(d["module_channels"])

            # Set voltage to voltage wave, make empty currents
            v_vals = d["jv"]["v"][0]
            j_fwd = 0
            j_rev = 0

            # Add up currents  from devices in parallel in fwd/rev
            for value in d["jv"]["j_fwd"]:
                j_fwd += value
            j_fwd /= num_modules
            for value in d["jv"]["j_rev"]:
                j_rev += value
            j_rev /= num_modules

            # Average forward and reverse current
            j = (j_fwd + j_rev) / 2

            # Calc voc, set voltage to fraction of voc
            voc = v_vals[np.argmin(np.abs(j))]
            v = voc * 0.75
            t = time.time()
            vm, i = chroma.set_V_measure_I(ch, v)

        return t, v, vm, i


    def calc_last_vmp(self, d: dict) -> float:
        """Gets last vmpp from tracking if it exists. If not, calculates from JV curves

        Args:
            d (dict): dictionary containing all necessary information (defined in controller.py)

        Returns:
            float: last maximum power point tracking voltage (V)
        """

        num_modules = len(d["module_channels"])

        # Take vmp from mpp tracking if it has value
        if d["mpp"]["vmpp"] is not None:
            vmpp = d["mpp"]["vmpp"]

        # If we have run all modules on the string, use JV curves to calcualte
        elif d["jv"]["j_fwd"][num_modules - 1] is not None:

            # Set voltage to voltage wave, make empty currents
            v = d["jv"]["v"][0]
            j_fwd = 0
            j_rev = 0

            # Add up currents (parallel) in fwd/rev
            for value in d["jv"]["j_fwd"]:
                j_fwd += value
            j_fwd /= num_modules
            for value in d["jv"]["j_rev"]:
                j_rev += value
            j_rev /= num_modules

            # Average forward and reverse current, calc p and vmpp
            j = (j_fwd + j_rev) / 2
            p = np.array(v * j)
            vmpp = v[np.argmax(p)]

        # Else, flag with None
        else:
            vmpp = None

        return vmpp

    def check_orientation(self, scanner: object) -> bool:
        """Checks the orientation of the module by verifying that Jsc > 0
        
        Args:
            scanner (object): pointer to the controller for the scanner
        
        Returns:
            boolean: Check for correct orientation
        """

        orientation_correct = None
        isc = scanner.isc()

        minisc = -0.0005
        if isc < minisc:
            orientation_correct = True
        elif isc > minisc:
            orientation_correct = False

        print(isc)
        return orientation_correct

    def monitor_environment(self, labjack: object) -> float:
        """Monitors the labjack for temperature

        Args:
            labjack (object): pointer to the dontoller for the labjack

        Returns:
            float: time (epoch)
            float: temperature (C)
            float: humidity (%)
            flaot: intensity (# suns)
        """

        t = time.time()
        # TODO: Add read monitoring
        temp, rh, intensity = labjack.monitor_env()

        return t, temp, rh, intensity
        # return t, 27, 50.0, 1.0
