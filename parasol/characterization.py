import numpy as np
import time

from parasol.configuration.configuration import Configuration
config = Configuration()
constants = config.get_config()['characterization']

class Characterization:
    """Characterization package for PARASOL"""

    def __init__(self) -> None:
        """Initializes the Characterization class"""

        # Get constants
        self.et_voltage_step = constants["mppt_voltage_step"]
        self.nightmode_starthour = constants["nightmode_starthour"]
        self.nightmode_endhour = constants["nightmode_endhour"]


        # Set up JV mode: # should match the if statment below and "" should be the desired name
        self.jv_options = {
            0: "REV then FWD",
            1: "FWD then REV",
            2: "REV then FWD, Voc to Jsc",
            3: "FWD then REV, Jsc to Voc",
            4: "REV then FWD, Voc to Jsc, No scans at night",
            5: "FWD then REV, Jsc to Voc, No scans at night",
        }

        # Set up MPP mode: # shoud match the if statment below and "" should be the desired name
        self.mpp_options = {
            0: "Perturb and Observe (constant V step)",
            1: "75% of Voc",
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
        
        # Mode = 4, scan rev then fwd (quadrant 4 only, no night scans)
        elif jv_mode == 4:
            yr,month,day,hr,minute = map(int,time.strftime("%Y %m %d %H %M").split())
            if hr < self.nightmode_endhour or hr >= self.nightmode_starthour:
                v, fwd_vm, fwd_i, rev_vm, rev_i = [
                    np.array([np.nan,np.nan]),
                    np.array([np.nan,np.nan]),
                    np.array([np.nan,np.nan]),
                    np.array([np.nan,np.nan]),
                    np.array([np.nan,np.nan])
                    ]
            else:
                v, fwd_vm, fwd_i, rev_vm, rev_i = scanner.iv_sweep_quadrant_fwd_rev(
                    vstart=d["jv"]["vmin"], vend=d["jv"]["vmax"], steps=d["jv"]["steps"]
                )
        
        # Mode = ,5 scan fwd then rev (quadrant 4 only, no night scans)
        elif jv_mode == 5:
            
            yr,month,day,hr,minute = map(int,time.strftime("%Y %m %d %H %M").split())
            if hr < self.nightmode_endhour or hr >= self.nightmode_starthour:
                v, fwd_vm, fwd_i, rev_vm, rev_i = [
                    np.array([np.nan,np.nan]),
                    np.array([np.nan,np.nan]),
                    np.array([np.nan,np.nan]),
                    np.array([np.nan,np.nan]),
                    np.array([np.nan,np.nan])
                    ]
            else:
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

        # TODO Community: Expand! Examples below.
        
        # Perturb and observe, two measurements to eliminate time axes, Hidenori SAITO no check for stabilization
        # DOI:10.5796/electrochemistry.20-00022

        # Modified perturb and observe: taken from David Sanz Morales Thesis
        # http://lib.tkk.fi/Dipl/2010/urn100399.pdf
        
        # PID controller?
        # note that the number of values kept for d['mpp'][parameter] are set in hardwareconstants.yaml

        # Get MPP mode
        mpp_mode = d["mpp"]["mode"]
        
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
                if d["mpp"]["last_voltages"][1] <= d["mpp"]["last_voltages"][0]:
                    voltage_step = self.et_voltage_step
                # if the most recent voltage < voltage before it, use opposite voltage step (-)
                else:
                    voltage_step = -self.et_voltage_step

                # if power isnt increasing, invert voltage step to move in the other direction
                if d["mpp"]["last_powers"][1] >= d["mpp"]["last_powers"][0]:
                    voltage_step *= -1

            # set the voltage equal to last voltage + voltage step (determined above)
            v = vmpp_last + voltage_step

            # If we are less than 0, move to voltage step or in correct direction
            if (v <= max(d["mpp"]["vmin"], 0)):
                voltage_step = self.et_voltage_step
                v = max(voltage_step, vmpp_last + voltage_step)
            
            # If we are greater than max mpp, move to max mpp - voltage step or in correct direction
            elif (v >= d["mpp"]["vmax"]):
                voltage_step = -1*self.et_voltage_step
                v = min((vmpp_last + voltage_step), (d["mpp"]["vmax"] + voltage_step))

            # note 23/07/31 --> this was originall written off [0] but meant to be off [1], left as is
            # If last current was 0, move to max mpp - voltage step or in correct direction
            elif (d["mpp"]["last_currents"][0] is not None):
                if (d["mpp"]["last_currents"][0] <= 0):
                    voltage_step = -1*self.et_voltage_step
                    v = min((vmpp_last + voltage_step), (d["mpp"]["vmax"] + voltage_step))

            # get time, set voltage measure current
            t = time.time()
            vm, i = chroma.set_V_measure_I(ch, v)

        # Mode = 1, bias at 75% of Voc
        # This is just an example. 
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
        # check_orientation turns on scanner, checks isc, turns off scanner
        isc = scanner.check_orientation()

        minisc = -0.0005
        if isc < minisc:
            orientation_correct = True
        elif isc > minisc:
            orientation_correct = False

        return orientation_correct

