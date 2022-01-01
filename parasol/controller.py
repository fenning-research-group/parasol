import time
import asyncio
from threading import Thread, Lock
from concurrent.futures import ThreadPoolExecutor
from concurrent.futures._base import CancelledError
import yaml
import os
import csv
from datetime import datetime
import time

from parasol.hardware.relay import Relay
from parasol.hardware.scanner import Scanner
from parasol.hardware.easttester import EastTester
from parasol.analysis.analysis import Analysis
from parasol.characterization import Characterization
from parasol.filestructure import FileStructure


# Set yaml name, load controller info
MODULE_DIR = os.path.dirname(__file__)
with open(os.path.join(MODULE_DIR, "hardwareconstants.yaml"), "r") as f:
    constants = yaml.load(f, Loader=yaml.FullLoader)["controller"]


class Controller:
    """Controller package for PARASOL"""

    def __init__(self) -> None:
        """Initializes the Controller class"""

        # Connect to Relay, Scanner, 3 EastTesters, and Characterization files
        self.relay = Relay()
        self.scanner = Scanner()
        self.easttester = {
            "12": EastTester(port=constants["ET_1_PORT"]),
            #        "34": EastTester(port=constants["ET_2_PORT"]),
            #        "56": EastTester(port=constants["ET_3_PORT"]),
        }
        self.characterization = Characterization()
        self.analysis = Analysis()
        self.filestructure = FileStructure()

        # Initialize running variable, create root directory
        self.running = False
        self.rootdir = self.filestructure.get_root_dir()
        if not os.path.exists(self.rootdir):
            os.mkdir(self.rootdir)

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
        id: int,
        startdate: str,
        name: str,
        area: float,
        jv_modeL: int,
        mpp_mode: int,
        module_channels: list,
        jv_interval: float,
        mpp_interval: float,
        jv_vmin: float,
        jv_vmax: float,
        jv_steps: int,
    ) -> str:
        """Loads a string of modules

        Args:
            id (int): string number
            startdate (datetime): start date for test
            name (string): test name
            area (float): area of each module on string
            jv_mode (int): JV mode (#'s correspond to option # in UI)
            mpp_mode (int): MPP mode (#'s correspond to option # in UI)
            module_channels (list[int]): modules connected
            jv_interval (float): time between JV sweeps (s)
            mpp_interval (float): time between MPP sweeps (s)
            jv_vmin (float): minimum JV sweep voltage (V)
            jv_vmax (float): maximum JV sweep voltage (V)
            jv_steps (int): number of voltage steps

        Raises:
            ValueError: String is already loaded
            ValueError: String ID does not exist

        Returns:
            string: path to save directory
        """

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
        self.strings[id] = {
            "name": name,
            "area": area,
            "start_date": startdate,
            "module_channels": module_channels,
            "jv": {
                "mode": jv_mode,
                "interval": jv_interval,
                "vmin": jv_vmin,
                "vmax": jv_vmax,
                "steps": jv_steps,
                "scan_count": 0,
                "_future": jv_future,
                "v": [None for i in range(len(module_channels))],
                "j_fwd": [None for i in range(len(module_channels))],
                "j_rev": [None for i in range(len(module_channels))],
            },
            "mpp": {
                "mode": mpp_mode,
                "interval": mpp_interval,
                "vmin": 0.1,
                "vmax": jv_vmax,
                "last_powers": [None, None],
                "last_voltages": [None, None],
                "_future": mpp_future,
                "vmpp": None,
            },
            "lock": Lock(),
        }

        (
            self.strings[id]["_savedir"],
            self.strings[id]["name"],
        ) = self.filestructure.make_module_subdir(name, module_channels, startdate)

        # Create the base MPP file with header and no data (we will append to it)
        self._make_mpp_file(id)

        return self.strings[id]["_savedir"]

    def unload_string(self, id: int) -> None:
        """Unloads a string of modules

        Args:
            id (int): string number

        Raises:
            ValueError: string ID not loaded
        """

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
        print("Analysis saved at :", saveloc)
        self.analysis.analyze_from_savepath(saveloc)

    def _make_mpp_file(self, id: int) -> None:
        """Creates base file for MPP data

        Args:
            id (int): string number
        """

        d = self.strings.get(id, None)

        # Get date/time and make filepath
        date_str = datetime.now().strftime("%Y-%m-%d")
        time_str = datetime.now().strftime("%H:%M:%S")
        epoch_str = time.time()

        # Save in base filepath: stringname: MPP: stringname_stringid_mpp_1 (we only have 1 mpp file)
        mppfolder = self.filestructure.get_mpp_folder(d["start_date"], d["name"])
        mppfile = self.filestructure.get_mpp_file_name(
            d["start_date"], d["name"], id, d["jv"]["scan_count"]
        )
        fpath = os.path.join(mppfolder, mppfile)

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

    async def jv_worker(self, loop: asyncio.AbstractEventLoop) -> None:
        """Worker for JV sweeps

        Args:
            loop (asyncio.AbstractEventLoop): timer loop to insert JV worker into
        """

        # We need a sleep here or it never gets added to the queue
        time.sleep(0.5)
        # While the loop is running, add jv scans to queue
        while self.running:
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

    async def mpp_worker(self, loop: asyncio.AbstractEventLoop) -> None:
        """Worker for MPP scans

        Args:
            loop (asyncio.AbstractEventLoop): timeer loop to insert MPP worker into
        """

        # We need a sleep here or it never gets added to the queue
        time.sleep(0.5)
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

    async def jv_timer(self, id: int) -> None:
        """Manages timing for JV worker

        Args:
            id (int): string number
        """
        await asyncio.sleep(1)
        while self.running:
            self.jv_queue.put_nowait(id)
            await asyncio.sleep(self.strings[id]["jv"]["interval"])

    async def mpp_timer(self, id: int) -> None:
        """Manages scanning for MPP worker

        Args:
            id (int): string number
        """

        await asyncio.sleep(1)
        while self.running:
            self.mpp_queue.put_nowait(id)
            await asyncio.sleep(self.strings[id]["mpp"]["interval"])

    def __make_background_event_loop(self) -> None:
        """Setup background event loop for schedueling tasks"""

        def exception_handler(loop, context):
            print("Exception raised in Controller loop")

        self.loop = asyncio.new_event_loop()
        self.loop.set_exception_handler(exception_handler)
        asyncio.set_event_loop(self.loop)
        self.jv_queue = asyncio.Queue()
        self.mpp_queue = asyncio.Queue()
        self.loop.run_forever()

    def start(self) -> None:
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

    def stop(self) -> None:
        """Delete workers,  stop queue, and reset hardware"""

        # close all channels
        self.relay.all_off()
        # turn off yokogawa
        self.scanner.srcV_measI()

        self.running = False
        ids = list(self.strings.keys())
        for id in ids:
            # Unload all strings
            self.unload_string(id)
            # Reset east tester
            et_key, ch = self.et_channels[id]
            et = self.easttester[et_key]
            et.srcV_measI(ch)

        self.loop.call_soon_threadsafe(self.loop.stop)
        self.thread.join()

    def scan_jv(self, id: int) -> None:
        """Conduct a JV scan using Scanner class

        Args:
            id (int): string number
        """

        # get dictionary information
        d = self.strings.get(id, None)

        # Emsure MPP isn't running.
        with d["lock"]:

            # Turn off easttester output
            et_key, ch = self.et_channels[id]
            et = self.easttester[et_key]
            et.output_off(ch)

            # cycle through each device on the string
            for index, module in enumerate(d["module_channels"]):

                # Get date/time and make filepath
                date_str = datetime.now().strftime("%Y-%m-%d")
                time_str = datetime.now().strftime("%H:%M:%S")
                epoch_str = time.time()

                # Save in base filepath: stringname: JV_modulechannel: stringname_stringid_modulechannel_JV_scannumber
                jvfolder = self.filestructure.get_jv_folder(
                    d["start_date"], d["name"], module
                )
                jvfile = self.filestructure.get_jv_file_name(
                    d["start_date"], d["name"], id, module, d["jv"]["scan_count"]
                )
                fpath = os.path.join(jvfolder, jvfile)

                # Open relay, scan device foward + reverse, turn off relay
                self.relay.on(module)
                v, fwd_i, rev_i = self.characterization.scan_jv(d, self.scanner)
                self.relay.all_off()

                # flip the current density, convert to mA, calculate parameters
                fwd_i *= -1 * 1000
                rev_i *= -1 * 1000
                fwd_j = fwd_i / d["area"]
                fwd_p = v * fwd_j
                rev_j = rev_i / d["area"]
                rev_p = v * rev_j

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

            # increase jv scan count
            d["jv"]["scan_count"] += 1

            # Turn on easttester output at old vmpp if we have one --> will need to change
            vmp = self.characterization.calc_last_vmp(d)
            if vmp is not None:
                et.output_on(ch)
                et.set_voltage(ch, vmp)

    def track_mpp(self, id: int) -> None:
        """Conduct an MPP scan using Easttester class

        Args:
            id (int): string number
        """

        d = self.strings.get(id, None)

        # Get last MPP, will be none if JV not filled
        last_vmpp = self.characterization.calc_last_vmp(d)

        # if we dont have a vmpp, skip
        if last_vmpp is None:
            return

        # Ensure that JV isn't running
        with d["lock"]:

            # Turn on easttester output, set voltage, measure current
            et_key, ch = self.et_channels[id]
            et = self.easttester[et_key]

            # scan mpp
            t, v, i = self.characterization.track_mpp(d, et, ch, last_vmpp)

            # Convert current to mA and calc j and p
            i *= 1000
            j = i / (d["area"] * len(d["module_channels"]))
            p = v * j

            # Update d[] by moving last value to first and append new values
            d["mpp"]["last_powers"][0] = d["mpp"]["last_powers"][1]
            d["mpp"]["last_powers"][1] = p
            d["mpp"]["last_voltages"][0] = d["mpp"]["last_voltages"][1]

            d["mpp"]["last_voltages"][1] = v
            d["mpp"]["vmpp"] = v

            # Save in base filepath:MPP_stringID:
            mppfolder = self.filestructure.get_mpp_folder(d["start_date"], d["name"])
            mppfile = self.filestructure.get_mpp_file_name(
                d["start_date"], d["name"], id, d["jv"]["scan_count"]
            )
            fpath = os.path.join(mppfolder, mppfile)

            # Open file, append values to columns
            with open(fpath, "a", newline="") as f:
                writer = csv.writer(f, delimiter=",")
                writer.writerow([t, v, i, j, p])

    def __del__(self) -> None:
        """Stops que and program on exit"""
        self.stop()


def future_callback(future):
    """Callback function triggered when a future completes. Allows errors to be seen outside event loop"""
    try:
        if future.exception() is not None:
            print(f"Exception in future: {future.exception()}")
            future.result()
    except CancelledError:
        pass
