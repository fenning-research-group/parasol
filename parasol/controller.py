import time
import asyncio
import numpy as np
from threading import Thread, Lock
from concurrent.futures import ThreadPoolExecutor
from concurrent.futures._base import CancelledError
import yaml
import os
import csv
from datetime import datetime
import time
from .hardware.relay import Relay
from .hardware.scanner import Scanner
from .hardware.easttester import EastTester
from .analysis.initial_parasol_analysis import Parasol_String


# Set yaml name, load controller info
MODULE_DIR = os.path.dirname(__file__)
with open(os.path.join(MODULE_DIR, "hardwareconstants.yaml"), "r") as f:
    constants = yaml.load(f, Loader=yaml.FullLoader)["controller"]


class Controller:
    """Create controller class to manage eastester, relay, and yokogawa"""

    def __init__(self, rootdir):
        """Initialize controller"""

        # Initialize running variable, create root directory
        self.running = False
        self.rootdir = rootdir
        if not os.path.exists(rootdir):
            os.mkdir(rootdir)

        # grab voltage step used for perturb and observe algorithm
        self.et_voltage_step = constants["et_voltage_step"]

        # Connect to Relay, Scanner, and 3 EastTesters
        self.relay = Relay()
        self.scanner = Scanner()
        self.easttester = {
            "12": EastTester(port=constants["ET_1_PORT"]),
            #        "34": EastTester(port=constants["ET_2_PORT"]),
            #        "56": EastTester(port=constants["ET_3_PORT"]),
        }

        # Maps string ID to ET port (which of the 3 ET) and channel
        self.et_channels = {
            1: ("12", 1),
            2: ("12", 2),
            3: ("34", 1),
            4: ("34", 2),
            5: ("56", 1),
            6: ("56", 2),
        }
        # Maps string ID to module channels
        self.module_channels = {
            1: [1, 2, 3, 4],
            2: [5, 6, 7, 8],
            3: [9, 10, 11, 12],
            4: [13, 14, 15, 16],
            5: [17, 18, 19, 20],
            6: [21, 22, 23, 24],
        }
        self.strings = {}

        # Decide how many workers we will allow and start the queue
        self.threadpool = ThreadPoolExecutor(max_workers=6)
        self.start()

    def load_string(
        self,
        id,
        name,
        n_modules,
        area,
        jv_interval,
        jv_vmin,
        jv_vmax,
        jv_steps,
        mpp_interval,
    ):
        """Master command used to load a string of modules"""

        # Ensure id is not already in use and can be used
        if id in self.strings:
            raise ValueError(f"String {id} already loaded!")
        if id not in self.et_channels:
            raise ValueError(f"{id} not valid string id!")

        # Setup jv and mpp timers in main loop
        jv_future = asyncio.run_coroutine_threadsafe(self.jv_timer(id=id), self.loop)
        jv_future.add_done_callback(future_callback)
        mpp_future = asyncio.run_coroutine_threadsafe(self.mpp_timer(id=id), self.loop)
        mpp_future.add_done_callback(future_callback)

        # Setup string dict with important information for running the program
        modulechannels = self.module_channels[id][:n_modules]
        self.strings[id] = {
            "name": name,
            "area": area,
            "module_channels": modulechannels,
            "jv": {
                "interval": jv_interval,
                "vmin": jv_vmin,
                "vmax": jv_vmax,
                "steps": jv_steps,
                "scan_count": 0,
                "_future": jv_future,
                "v": [None for i in range(n_modules)],
                "j_fwd": [None for i in range(n_modules)],
                "j_rev": [None for i in range(n_modules)],
                "vmpp": [None for i in range(n_modules)],
            },
            "mpp": {
                "interval": mpp_interval,
                "vmin": 0.1,
                "vmax": jv_vmax * n_modules,
                "last_powers": [None, None],
                "last_voltages": [None, None],
                "_future": mpp_future,
                "vmpp": None,
            },
            "lock": Lock(),
        }

        self.strings[id]["_savedir"] = self._make_module_subdir(
            name, id, modulechannels
        )

        # Create the base MPP file with header and no data (we will append to it)
        self.create_mpp_file(id)

    def unload_string(self, id):
        """Master command used to unload a string of modules"""

        # get string saveloc
        d = self.strings.get(id, None)
        saveloc = d["_savedir"]

        # destroy all future tasks for the string
        if id not in self.strings:
            raise ValueError(f"String {id} not loaded!")
        self.strings[id]["jv"]["_future"].cancel()
        self.strings[id]["mpp"]["_future"].cancel()

        # delete the stringid from the dict, remove from queue
        del self.strings[id]
        while id in self.jv_queue._queue:
            self.jv_queue._queue.remove(id)
        while id in self.mpp_queue._queue:
            self.mpp_queue._queue.remove(id)

        # analyze the saveloc
        Parasol_String(saveloc)

    def _make_module_subdir(self, name, id, modulechannels):
        """Make subdirectory for saving"""

        # Make base file path for saving
        idx = 0
        basefpath = os.path.join(self.rootdir, f"{name}")
        while os.path.exists(basefpath):
            idx += 1
            basefpath = os.path.join(self.rootdir, f"{name}_{idx}")
        os.mkdir(basefpath)

        # Make subdirectory for MMP
        mppfpath = os.path.join(basefpath, "MPP")
        os.mkdir(mppfpath)

        # Make subdirectory for each module
        for modulechannel in modulechannels:
            modulepath = os.path.join(basefpath, f"JV_{modulechannel}")
            os.mkdir(modulepath)

        return basefpath

    async def jv_worker(self, loop):
        """Uses Yokogawa to conudct a JV scan by calling scan_jv"""
        print("Starting JV worker")
        # While the loop is running, add jv scans to queue
        while self.running:
            print("Jv worker running")
            id = await self.jv_queue.get()

            scan_future = asyncio.gather(
                loop.run_in_executor(
                    self.threadpool,
                    self.scan_jv,
                    id,
                )
            )
            scan_future.add_done_callback(future_callback)

            # Scan the module and let user know
            print(f"Scanning {id}")
            await scan_future
            self.jv_queue.task_done()
            print(f"Done Scanning {id}")

    async def mpp_worker(self, loop):
        """Uses EastTester to conudct a MPP scan by calling track_mpp"""

        # While the loop is running, add mpp scans to queue
        while self.running:
            id = await self.mpp_queue.get()
            scan_future = asyncio.gather(
                loop.run_in_executor(
                    self.threadpool,
                    self.track_mpp,
                    id,
                )
            )
            scan_future.add_done_callback(future_callback)

            # Scan the string and let the user know
            print(f"Tracking {id}")
            await scan_future
            self.mpp_queue.task_done()
            print(f"Done Tracking {id}")

    async def jv_timer(self, id):
        """Manages timing for JV worker"""
        await asyncio.sleep(1)
        while self.running:
            self.jv_queue.put_nowait(id)
            await asyncio.sleep(self.strings[id]["jv"]["interval"])

    async def mpp_timer(self, id):
        """Manages scanning for MPP worker"""
        await asyncio.sleep(1)
        while self.running:
            self.mpp_queue.put_nowait(id)
            await asyncio.sleep(self.strings[id]["mpp"]["interval"])

    def __make_background_event_loop(self):
        """Setup background event loop for schedueling tasks"""

        def exception_handler(loop, context):
            print("Exception raised in Controller loop")

        self.loop = asyncio.new_event_loop()
        self.loop.set_exception_handler(exception_handler)
        asyncio.set_event_loop(self.loop)
        self.jv_queue = asyncio.Queue()
        self.mpp_queue = asyncio.Queue()
        self.loop.run_forever()

    def start(self):
        """Create workers / start queue"""
        self.thread = Thread(target=self.__make_background_event_loop)
        self.thread.start()
        time.sleep(0.5)

        # Create JV worker for yokogawa
        asyncio.run_coroutine_threadsafe(self.jv_worker(self.loop), self.loop)

        # Create MPP workers for easttester (1 for each yoko channel)
        asyncio.run_coroutine_threadsafe(self.mpp_worker(self.loop), self.loop)
        asyncio.run_coroutine_threadsafe(self.mpp_worker(self.loop), self.loop)
        asyncio.run_coroutine_threadsafe(self.mpp_worker(self.loop), self.loop)
        asyncio.run_coroutine_threadsafe(self.mpp_worker(self.loop), self.loop)
        asyncio.run_coroutine_threadsafe(self.mpp_worker(self.loop), self.loop)
        asyncio.run_coroutine_threadsafe(self.mpp_worker(self.loop), self.loop)
        self.running = True

    def stop(self):
        """Delete workers / stop queue"""
        self.running = False
        ids = list(self.strings.keys())
        for id in ids:
            self.unload_string(id)
        self.loop.call_soon_threadsafe(self.loop.stop)
        self.thread.join()

    def scan_jv(self, id):
        """Uses Yokogawa to conudct a JV scan"""

        print("jvscan!")
        d = self.strings.get(id, None)

        # Emsure MPP isn't running.
        with d["lock"]:
            print("jvscan!2")

            # Turn off easttester output
            et_key, ch = self.et_channels[id]
            et = self.easttester[et_key]
            et.output_off(ch)

            for index, module in enumerate(d["module_channels"]):
                print(f"jvscan!3")
                # Get date/time and make filepath
                date_str = datetime.now().strftime("%Y-%m-%d")
                time_str = datetime.now().strftime("%H:%M:%S")
                epoch_str = time.time()

                # Save in base filepath: stringname: JV_modulechannel: stringname_stringid_modulechannel_JV_scannumber
                jvfolder = os.path.join(d["_savedir"], f"JV_{module}")
                fpath = os.path.join(
                    jvfolder,
                    f"{d['name']}_{id}_{module}_JV_{d['jv']['scan_count']}.csv",
                )

                # Scan device foward + reverse, calculate current density and power for both
                self.relay.on(module)
                print(f"jvscan!4")
                v, fwd_i, rev_i = self.scanner.scan_jv(
                    vmin=d["jv"]["vmin"], vmax=d["jv"]["vmax"], steps=d["jv"]["steps"]
                )
                print(f"jvscan!5")
                fwd_j = fwd_i / d["area"]
                fwd_p = v * fwd_j
                rev_j = rev_i / d["area"]
                rev_p = v * rev_j
                print(f"jvscan!6")

                # Open file, write header/column names then fill
                with open(fpath, "w", newline="") as f:
                    writer = csv.writer(f, delimiter=",")
                    writer.writerow(["Date:", date_str])
                    writer.writerow(["Time:", time_str])
                    writer.writerow(["epoch_time:", epoch_str])
                    writer.writerow(["String ID:", id])
                    writer.writerow(["Module ID:", module])
                    writer.writerow(["Area (cm2):", d["area"]])
                    writer.writerow(
                        [
                            "Voltage (V)",
                            "FWD Current (mA)",
                            "FWD Current Density (mA/cm2)",
                            "FWD Power Density (mW/cm2)",
                            "REV Current (mA)",
                            "REV Current Density (mA/cm2)",
                            "REV Power Density (mW/cm2)",
                        ]
                    )
                    for line in zip(v, fwd_i, fwd_j, fwd_p, rev_i, rev_j, rev_p):
                        writer.writerow(line)

                # save any useful raw data to the string dictionary
                d["jv"]["v"][index] = v
                d["jv"]["j_fwd"][index] = fwd_j
                d["jv"]["j_rev"][index] = rev_j

                # Calculate MPP, save to string dictionary
                avg_p = (rev_p + fwd_p) / 2
                v_maxloc = np.argmax(avg_p)
                v_mpp = v[v_maxloc]
                d["jv"]["vmpp"][index] = v_mpp

            # increase jv scan count
            d["jv"]["scan_count"] += 1
        print("jvscan!7")

    def create_mpp_file(self, id):
        """Creates base file for MPP data"""

        d = self.strings.get(id, None)

        # Get date/time and make filepath
        date_str = datetime.now().strftime("%Y-%m-%d")
        time_str = datetime.now().strftime("%H:%M:%S")
        epoch_str = time.time()

        # Save in base filepath: stringname: MPP: stringname_stringid_mpp_1 (we only have 1 mpp file)
        mppfolder = os.path.join(d["_savedir"], "MPP")
        fpath = os.path.join(mppfolder, f"{d['name']}_{id}_MPP_1.csv")

        # Open file, write header/column names then fill
        with open(fpath, "w", newline="") as f:
            writer = csv.writer(f, delimiter=",")
            writer.writerow(["Date:", date_str])
            writer.writerow(["Time:", time_str])
            writer.writerow(["epoch_time:", epoch_str])
            writer.writerow(["String ID:", id])
            writer.writerow(["Module ID:", d["module_channels"]])
            writer.writerow(["Area (cm2):", d["area"]])
            writer.writerow(
                [
                    "Time (epoch)",
                    "Voltage (V)",
                    "Current (mA)",
                    "Current Density (mA/cm2)",
                    "Power Density (mW/cm2)",
                ]
            )

    def track_mpp(self, id):
        """Uses Easttester to track MPP with a perturb and observe algorithm"""

        d = self.strings.get(id, None)

        # Dont run until we have done JV scan
        if d["jv"]["vmpp"][-1] is None:
            return

        # Ensure that JV isn't running
        with d["lock"]:

            # Get last vmp, ideally from mpp tracking value, else from addition of jv vmpps
            vmpp = 0
            if d["mpp"]["vmpp"] is not None:
                vmpp = d["mpp"]["vmpp"]
            else:
                for value in d["jv"]["vmpp"]:
                    vmpp += value

            # Get voltage step
            if (d["mpp"]["last_powers"][0] is None) or (
                d["mpp"]["last_powers"][1] is None
            ):
                voltage_step = self.et_voltage_step
            else:
                if d["mpp"]["last_voltages"][1] > d["mpp"]["last_voltages"][0]:
                    voltage_step = self.et_voltage_step
                else:
                    voltage_step = -self.et_voltage_step

                if d["mpp"]["last_powers"][1] <= d["mpp"]["last_powers"][0]:
                    voltage_step *= -1

            # Get time, set voltage
            t = time.time()
            v = vmpp + voltage_step

            # Ensure voltage is between the easttesters max and min values
            if (v < d["mpp"]["vmin"]) or (v > d["mpp"]["vmax"]):
                v = vmpp - 2 * voltage_step

            # Turn on easttester output, set voltage, measure current, calculate desired parameters
            et_key, ch = self.et_channels[id]
            et = self.easttester[et_key]
            et.output_on(ch)
            et.set_voltage(ch, v)
            i = et.measure_current(ch)
            j = i / (d["area"] * len(d["module_channels"]))
            p = v * j

            # Update d[] by moving last value to first and append new values
            d["mpp"]["last_powers"][0] = d["mpp"]["last_powers"][1]
            d["mpp"]["last_powers"][1] = p
            d["mpp"]["last_voltages"][0] = d["mpp"]["last_voltages"][1]
            d["mpp"]["last_voltages"][1] = v

            # Save in base filepath:MPP_stringID:
            mppfolder = os.path.join(d["_savedir"], "MPP")
            fpath = os.path.join(mppfolder, f"{d['name']}_{id}_MPP_1.csv")

            # Open file, append values to columns
            with open(fpath, "a", newline="") as f:
                writer = csv.writer(f, delimiter=",")
                writer.writerow([t, v, i, j, p])

    def __del__(self):
        """Stops que and program on exit"""
        self.stop()


def future_callback(future):
    """Callback function triggered when a future completes. Allows errors to be seen outside event loop"""
    try:
        if future.exception() is not None:
            print(f"Exception in future: {future.exception()}")
            raise future.exception()
    except CancelledError:
        pass
