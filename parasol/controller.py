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
import logging
import sys

from parasol.hardware.relay import Relay
from parasol.hardware.yokogawa import Yokogawa
from parasol.hardware.labjack import LabJack
from parasol.analysis.analysis import Analysis
from parasol.characterization import Characterization
from parasol.filestructure import FileStructure
from parasol.hardware.chroma import Chroma

# Set module directory, import constants from yaml file
MODULE_DIR = os.path.dirname(__file__)
with open(os.path.join(MODULE_DIR, "hardwareconstants.yaml"), "r") as f:
    constants = yaml.safe_load(f)["controller"]


class Controller:
    """Controller package for PARASOL"""

    # Initialize kit, start/stop workers, file management

    def __init__(self, logging_on=True) -> None:
        """Initializes the Controller class

        Args:
            logging_on (boolean): Option to log or not, default True
        """

        # Connect to other modules
        self.relay = Relay()
        self.scanner = Yokogawa()
        self.characterization = Characterization()
        self.analysis = Analysis()
        self.filestructure = FileStructure()
        self.monitor = LabJack()
        self.load = Chroma()

        # Get constants
        self.monitor_delay = constants["monitor_delay"]

        # Initialize running
        self.running = False

        # Create blank message that can be checked from other programs (mainly GUI)
        self.message = None

        # Create characterization/monitor/logging directories
        self.characterizationdir = self.filestructure.get_characterization_dir()
        if not os.path.exists(self.characterizationdir):
            os.mkdir(self.characterizationdir)
        self.monitordir = self.filestructure.get_environment_dir()
        if not os.path.exists(self.monitordir):
            os.mkdir(self.monitordir)
        self.logdir = self.filestructure.get_log_dir()
        if not os.path.exists(self.logdir):
            os.mkdir(self.logdir)

        # Map string ID to load port and channel
        # self.load_channels = {
        #     1: ("12", 1),
        #     2: ("12", 2),
        #     3: ("34", 1),
        #     4: ("34", 2),
        #     5: ("56", 1),
        #     6: ("56", 2),
        # }
        self.load_channels = {
            1: 1,
            2: 2,
            3: 3,
            4: 4,
            5: 7,
            6: 8,
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

        # Create blank dictionary to hold all info about strings
        self.strings = {}

        # Create list of active strings
        self.active_strings = [False] * (len(self.load_channels)+1)

        # Create logger with options to log or not
        date = datetime.now().strftime("%Y%m%d")
        self.logger = logging.getLogger("PARASOL")
        self.logger.setLevel(logging.DEBUG)
        fh = logging.FileHandler(os.path.join(self.logdir, f"{date}_Log.log"))
        sh = logging.StreamHandler(sys.stdout)
        sh.setLevel(logging.INFO)
        fh_formatter = logging.Formatter(
            "%(asctime)s %(levelname)s: %(message)s",
            datefmt="%m/%d/%Y %I:%M:%S %p",
        )
        sh_formatter = logging.Formatter(
            "%(asctime)s %(message)s",
            datefmt="%I:%M:%S",
        )
        fh.setFormatter(fh_formatter)
        sh.setFormatter(sh_formatter)
        if logging_on:
            self.logger.addHandler(fh)
            self.logger.addHandler(sh)

        # Create workers (1 for scanner, n for loads, 1 for random tasks, 1 for environment) & start queue
        self.threadpool = ThreadPoolExecutor(max_workers=3+(len(self.load_channels)))
        self.start()

    def load_string(
        self,
        id: int,
        startdate: str,
        name: str,
        area: float,
        jv_mode: int,
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
            startdate (string): start date for test (xYYYYMMDD)
            name (string): test name (basename, no _idx added)
            area (float): area of each module on string (cm^2)
            jv_mode (int): JV mode (#'s correspond to option # in UI)
            mpp_mode (int): MPP mode (#'s correspond to option # in UI)
            module_channels (list[int]): modules connected
            jv_interval (float): time between JV sweeps (s)
            mpp_interval (float): time between MPP sweeps (s)
            jv_vmin (float): minimum JV sweep voltage (V)
            jv_vmax (float): maximum JV sweep voltage (V)
            jv_steps (int): number of voltage steps

        Raises:
            ValueError: String ID already loaded
            ValueError: ID not valid string ID

        Returns:
            string: path to save directory
        """

        # Ensure id is not already in use and can be used
        if id in self.strings:
            raise ValueError(f"String {id} already loaded!")
        if id not in self.load_channels:
            raise ValueError(f"{id} not valid string id!")

        # Setup JV and MPP timers in main loop
        jv_future = asyncio.run_coroutine_threadsafe(self.jv_timer(id=id), self.loop)
        jv_future.add_done_callback(future_callback)
        mpp_future = asyncio.run_coroutine_threadsafe(self.mpp_timer(id=id), self.loop)
        mpp_future.add_done_callback(future_callback)

        # If we are not monitoring the environment, start the monitor
        if not any(self.active_strings):
            self.logger.debug(f"Starting environmental monitoring")
            self.monitor_future = asyncio.run_coroutine_threadsafe(
                self.monitor_timer(), self.loop
            )
            self.monitor_future.add_done_callback(future_callback)
            self.logger.info(f"Started environmental monitoring")

        # Make string active
        self.active_strings[id] = True

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
                "vmin": jv_vmin,
                "vmax": jv_vmax,
                "last_currents": [None, None],
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
        self.logger.info(f"String {id} loaded")

        # Turn on the load here, stays on when not being scanned
        self.logger.debug(f"Turning on load output for string {id}")
        ch = self.load_channels[id]
        self.load.output_on(ch)
        self.logger.debug(f"Turned off load output for string {id}")

        return self.strings[id]["name"]

    def load_check_orientation(self, modules: list) -> None:
        """Checks the orientation of the input modules by verifying that Jsc < 0 on the scanner.

        Args:
            modules (list[int]): modules to check

        """
        check_task_future = asyncio.run_coroutine_threadsafe(
            self.random_task_timer(modules=modules), self.loop
        )
        check_task_future.add_done_callback(future_callback)

    def unload_string(self, id: int) -> None:
        """Unloads a string of modules

        Args:
            id (int): string number

        Raises:
            ValueError: string ID not loaded
        """

        # Log unload
        self.logger.debug(f"Unloading string {id}")

        # Get string saveloc
        d = self.strings.get(id, None)
        if id not in self.strings:
            raise ValueError(f"String {id} not loaded!")

        # Lock all actions on string
        with d["lock"]:
            
            # Get saveloc
            saveloc = d["_savedir"]

            # Destroy all future tasks for the string
            if id not in self.strings:
                raise ValueError(f"String {id} not loaded!")
            self.logger.debug(f"Canceling tasks for {id}")
            self.strings[id]["jv"]["_future"].cancel()
            self.strings[id]["mpp"]["_future"].cancel()
            self.logger.debug(f"Canceled tasks for {id}")

            # Remove all tasks in que not already started (can start 1 from each worker)
            self.logger.debug(f"Removing tasks from que for {id}")
            while id in self.jv_queue._queue:
                self.jv_queue._queue.remove(id)
            while id in self.mpp_queue._queue:
                self.mpp_queue._queue.remove(id)
            self.logger.debug(f"Removed tasks from que for {id}")

            # Decrease number of tests active by one
            self.active_strings[id] = False

            # If we have no active tests, stop monitoring
            if not any(self.active_strings):
                self.logger.debug(f"Canceling environmental monitoring")
                time.sleep(self.monitor_delay)
                self.monitor_future.cancel()
                self.logger.info(f"Environmental monitoring canceled")

            # Turn load output off
            self.logger.debug(f"Resetting load for {id}")
            ch = self.load_channels[id]
            self.load.srcV_measI(ch)
            self.load.output_off(ch)
            self.logger.debug(f"Load reset for {id}")

            # Analyze the saveloc in a new thread
            self.logger.debug(f"Saving analysis at : {saveloc}")
            analyze_thread = Thread(
                target=self.analysis.analyze_from_savepath, args=(saveloc,)
            )
            analyze_thread.start()

        # Delete the string
        del self.strings[id]

        self.logger.info(f"Analysis saved at : {saveloc}")

    def make_mpp_file(self, id: int) -> None:
        """Creates base file for MPP data

        Args:
            id (int): string number
        """

        # Get dictionary for test string
        d = self.strings.get(id, None)

        # Get date/time and make filepath
        date_str = datetime.now().strftime("%Y-%m-%d")
        time_str = datetime.now().strftime("%H:%M:%S")
        epoch_str = time.time()

        # Save in base filepath: stringname: MPP: stringname_stringid_mpp_# (matches JV #)
        mppfolder = self.filestructure.get_mpp_folder(d["start_date"], d["name"])
        mppfile = self.filestructure.get_mpp_file_name(
            d["start_date"], d["name"], id, d["jv"]["scan_count"]
        )
        fpath = os.path.join(mppfolder, mppfile)

        # If it doesnt exist, make it:
        if os.path.exists(fpath) != True:
            
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
                        "Applied Voltage (V)",
                        "Voltage (V)",
                        "Current (mA)",
                        "Current Density (mA/cm2)",
                        "Power Density (mW/cm2)",
                    ]
                )

            self.logger.debug(f"MPP file made for {id} at {fpath}")

        return fpath

    def make_env_file(self) -> None:
        """Creates base file for environmental monitoring data"""

        # Get date/time and make filepath
        currenttime = datetime.now()
        cdate = currenttime.strftime("x%Y%m%d")

        # Get environment folder and file
        envfolder = self.filestructure.get_environment_folder(cdate)
        if not os.path.exists(envfolder):
            os.mkdir(envfolder)
        envfile = self.filestructure.get_environment_file_name(cdate)
        fpath = os.path.join(envfolder, envfile)

        # Make file if it doesnt exist
        if os.path.exists(fpath) != True:

            # Open file, write header/column names then fill
            with open(fpath, "w", newline="") as f:
                writer = csv.writer(f, delimiter=",")
                writer.writerow(
                    [
                        "Time (Epoch)",
                        "Temperature (C)",
                        "RH (%)",
                        "Intensity (# Suns)",
                    ]
                )

            self.logger.debug(f"Environmental monitoring file made at {fpath}")

        return fpath

    # Workers

    async def jv_worker(self, loop: asyncio.AbstractEventLoop) -> None:
        """Worker for JV sweeps

        Args:
            loop (asyncio.AbstractEventLoop): timer loop to insert JV worker into
        """

        # We need a sleep here or it never gets added to the queue
        time.sleep(0.5)

        # While the loop is running, add JV scans to queue
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

            # Scan the module
            await scan_future
            self.jv_queue.task_done()

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
            # Track the string
            await scan_future
            self.mpp_queue.task_done()



    async def check_orientation_worker(self, loop: asyncio.AbstractEventLoop) -> None:
        """
        Worker for checking orientation of select modules by verifying that Jsc < 0 on the scanner.

        Args:
            loop (asyncio.AbstractEventLoop): timer loop to insert MPP worker into
        """

        # We need a sleep here or it never gets added to the queue
        time.sleep(0.5)

        # While the loop is running, add mpp scans to queue
        while self.running:
            modules = await self.random_queue.get()
            scan_future = asyncio.gather(
                loop.run_in_executor(
                    self.threadpool,
                    self.check_orientation,
                    modules,
                )
            )
            scan_future.add_done_callback(future_callback)

            # Check orientation of modules
            await scan_future
            self.random_queue.task_done()

    async def monitor_worker(self, loop: asyncio.AbstractEventLoop) -> None:
        """Worker for monitoring the evnironment

        Args:
            loop (asyncio.AbstractEventLoop): timer loop to insert monitor worker into
        """

        # We need a sleep here or it never gets added to the queue
        time.sleep(0.5)

        # While the loop is running, add monitor scans to queue
        while self.running:
            dummyid = await self.monitor_queue.get()
            scan_future = asyncio.gather(
                loop.run_in_executor(self.threadpool, self.monitor_env, dummyid)
            )
            scan_future.add_done_callback(future_callback)

            # Track the environemnt
            await scan_future
            self.monitor_queue.task_done()

    # Timers

    async def random_task_timer(self, modules: list) -> None:
        """Manages inserting random tasks

        Args:
            modules (list[int]): modules to check
        """

        # Add worker to que and start when possible
        self.random_queue.put_nowait(modules)

    async def jv_timer(self, id: int) -> None:
        """Manages timing for JV worker

        Args:
            id (int): string number
        """
        # Add worker to que and start when possible
        await asyncio.sleep(1)
        while self.running:
            self.jv_queue.put_nowait(id)
            await asyncio.sleep(self.strings[id]["jv"]["interval"])

    async def mpp_timer(self, id: int) -> None:
        """Manages scanning for MPP worker

        Args:
            id (int): string number
        """

        # Add worker to que and start when possible
        await asyncio.sleep(1)
        while self.running:           
            # add worker to queue, increase mpp worker count
            self.mpp_queue.put_nowait(id)
            await asyncio.sleep(self.strings[id]["mpp"]["interval"])

    async def monitor_timer(self) -> None:
        """Manages scanning for monitor worker"""

        # Add worker to que and start when possible
        await asyncio.sleep(1)
        while self.running:
            self.monitor_queue.put_nowait(1)
            await asyncio.sleep(self.monitor_delay)

    # Event Loops

    def __make_background_event_loop(self) -> None:
        """Setup background event loop for schedueling tasks"""

        # If we have an issue in the loop, log it
        def exception_handler(loop, context):
            self.logger.info(f"Exception raised in Controller loop")

        # Start event loop, add workers
        self.loop = asyncio.new_event_loop()
        self.loop.set_exception_handler(exception_handler)
        asyncio.set_event_loop(self.loop)
        self.jv_queue = asyncio.Queue()
        self.mpp_queue = asyncio.Queue()
        self.random_queue = asyncio.Queue()
        self.monitor_queue = asyncio.Queue()
        self.loop.run_forever()

    def start(self) -> None:
        """Create workers / start queue"""

        # Start background event loops
        self.thread = Thread(target=self.__make_background_event_loop)
        self.thread.start()
        time.sleep(0.5)

        # Create Monitor worker for RH, Temp, illumination intensity
        asyncio.run_coroutine_threadsafe(self.monitor_worker(self.loop), self.loop)

        # Create JV worker for scanner
        asyncio.run_coroutine_threadsafe(self.jv_worker(self.loop), self.loop)

        # Create MPP workers for each load
        asyncio.run_coroutine_threadsafe(self.mpp_worker(self.loop), self.loop)
        asyncio.run_coroutine_threadsafe(self.mpp_worker(self.loop), self.loop)
        asyncio.run_coroutine_threadsafe(self.mpp_worker(self.loop), self.loop)
        asyncio.run_coroutine_threadsafe(self.mpp_worker(self.loop), self.loop)
        asyncio.run_coroutine_threadsafe(self.mpp_worker(self.loop), self.loop)
        asyncio.run_coroutine_threadsafe(self.mpp_worker(self.loop), self.loop)

        # Create check orientation workers
        asyncio.run_coroutine_threadsafe(
            self.check_orientation_worker(self.loop), self.loop
        )

        # Turn on running
        self.running = True

    def stop(self) -> None:
        """Delete workers,  stop queue, and reset hardware"""

        # Unload all strings
        ids = list(self.strings.keys())
        for id in ids:
            self.unload_string(id)

        # Cancel loops, join threads
        self.loop.call_soon_threadsafe(self.loop.stop)
        self.thread.join()

        # TODO: Reset hardware on stop
        # force wait until all active strings have been terminated
        # while any(self.active_strings):
        #     time.sleep(1)

        # # Close all channels on the relay
        # self.logger.debug(f"Turning off relays")
        # self.relay.all_off()
        # self.logger.debug(f"Turned off relays")

        # # Reset scanner
        # self.logger.debug(f"Resetting scanner")
        # self.scanner.output_off()
        # self.logger.debug(f"Scanner reset")

        # # Turn off running
        # self.running = False

    # Worker Functions

    def scan_jv(self, id: int) -> None:
        """Conduct a JV scan using Scanner class

        Args:
            id (int): string number
        """

        self.logger.debug(f"Scanning {id}")

        # Get dictionary information
        d = self.strings.get(id, None)

        # If dictionary is not found, return
        if d is None:
            self.logger.info(f"Empty dictionary passed to MPPT")
            return

        # Lock the string
        with d['lock']:

            # If string is not active return
            if self.active_strings[id] == False:
                self.logger.info(f"Last JV scan of string {id} aborted")
                return

            # Turn off load output
            self.logger.debug(f"Turning off load output for string {id}")
            ch = self.load_channels[id]
            self.load.output_off(ch)
            self.logger.debug(f"Turned off load output for string {id}")

            # Cycle through each device on the string
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
                self.logger.debug(f"Opening relay for string {id}")
                self.relay.on(module)
                self.logger.debug(f"Opened relay for string {id}")
                self.logger.debug(f"Scanning string {id}")
                v, fwd_vm, fwd_i, rev_vm, rev_i = self.characterization.scan_jv(d, self.scanner)
                self.logger.debug(f"Scanned string {id}")
                self.logger.debug(f"Closing relay for string {id}")
                self.relay.all_off()
                self.logger.debug(f"Closed relay for string {id}")

                # Convert to mA, calculate parameters
                # TODO: GET RID OF (-) SIGN
                fwd_i *= -1000
                rev_i *= -1000
                fwd_j = fwd_i / d["area"]
                fwd_p = fwd_vm * fwd_j
                rev_j = rev_i / d["area"]
                rev_p = rev_vm * rev_j

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
                            "Applied Voltage (V)",
                            "FWD Voltage (V)",
                            "FWD Current (mA)",
                            "FWD Current Density (mA/cm2)",
                            "FWD Power Density (mW/cm2)",
                            "REV Voltage (V)",
                            "REV Current (mA)",
                            "REV Current Density (mA/cm2)",
                            "REV Power Density (mW/cm2)",
                        ]
                    )
                    for line in zip(v, fwd_vm, fwd_i, fwd_j, fwd_p, rev_vm, rev_i, rev_j, rev_p):
                        writer.writerow(line)

                self.logger.debug(f"Writing JV file for {id} at {fpath}")

                # Save any useful raw data to the string dictionary
                d["jv"]["v"][index] = v
                d["jv"]["j_fwd"][index] = fwd_j
                d["jv"]["j_rev"][index] = rev_j

            # Increase JV scan count
            d["jv"]["scan_count"] += 1

            # Turn on load output at old vmpp if we have one
            vmp = self.characterization.calc_last_vmp(d)
            if vmp is not None:
                self.logger.debug(f"Turning on load output for string {id}")
                self.load.output_on(ch)
                self.load.set_voltage(ch, vmp)
                self.logger.debug(f"Turned on load output for string {id}")

            self.logger.info(f"Scanned {id}")

    def track_mpp(self, id: int) -> None:
        """Conduct an MPP scan using Chroma class

        Args:
            id (int): string number
        """

        self.logger.debug(f"Tracking {id}")

        d = self.strings.get(id, None)

        if d is None:
            self.logger.info(f"Empty dictionary passed to JV")
            return

        # Lock string
        with d['lock']:

            # If string is not active return
            if self.active_strings[id] == False:
                self.logger.info(f"Last MPP scan of string {id} aborted")
                return

            # Get last MPP, will be none if JV not filled
            last_vmpp = self.characterization.calc_last_vmp(d)

            # If we dont have a Vmpp return
            if last_vmpp is None:
                return

            # Turn on load output
            ch = self.load_channels[id]
            
            # Scan mpp (pass last MPP to it)
            self.logger.debug(f"Tracking MPP for {id}")
            t, v, vm, i = self.characterization.track_mpp(d, self.load, ch, last_vmpp)
            self.logger.debug(f"Tracked MPP for {id}")

            # Convert current to mA and calc j and p
            i *= 1000
            j = i / (d["area"] * len(d["module_channels"]))
            p = v * j
            pm = vm*j

            # Update dictionary by moving last value to first and append new values
            d["mpp"]["last_powers"][0] = d["mpp"]["last_powers"][1]
            d["mpp"]["last_powers"][1] = (p+pm)/2 # incase resolution doesnt change V value

            d["mpp"]["last_voltages"][0] = d["mpp"]["last_voltages"][1]
            d["mpp"]["last_voltages"][1] = (v+vm)/2 # incase resolution doesnt change V value

            d["mpp"]["last_currents"][0] = d["mpp"]["last_currents"][1]
            d["mpp"]["last_currents"][1] = i

            d["mpp"]["vmpp"] = v

            # Get MPP file path, if it doesnt exist, create it, iterate for each JV curve taken
            fpath = self.make_mpp_file(id)

            # Open file, append values to columns
            with open(fpath, "a", newline="") as f:
                writer = csv.writer(f, delimiter=",")
                writer.writerow([t, v, vm, i, j, pm])

            self.logger.debug(f"Writing MPP file for {id} at {fpath}")

            self.logger.info(f"Tracked {id}")
            

    def monitor_env(self, dummyid: int) -> None:
        """
        Monitors environment using the Monitor class

        Args:
            dummyid (int): passes int 1 to the monitor class
        """

        self.logger.debug(f"Monitoring environment")

        # Get Temperature, Humidity, Relative Humidity, and Temperature
        t, temp, rh, intensity = self.characterization.monitor_environment(self.monitor)

        # Make env file if needed (done 1x per experiment)
        fpath = self.make_env_file()

        # Append to file
        with open(fpath, "a", newline="") as f:
            writer = csv.writer(f, delimiter=",")
            writer.writerow([t, temp, rh, intensity])

        self.logger.debug(f"Writing Monitoring file at {fpath}")
        self.logger.debug(f"Monitored environment")

    def check_orientation(self, modules: list) -> None:
        """Checks the orientation of the list of modules by verifying that Jsc > 0 using the scanner

        Args:
            modules (list[int]): list of modules
        """

        self.logger.debug(f"Checking orientation")

        # Make string to hold # of correct orientations
        correct_orientation = [None] * len(modules)

        # Cycle through each module
        for idx, module in enumerate(modules):

            # Turn on relay
            self.logger.debug(f"Turning on relay for module {module}")
            self.relay.on(module)
            self.logger.debug(f"Turned on relay for module {module}")

            # Pass scanner to characterization module, returns true if Isc < 0, false otherwise
            self.logger.debug(f"Checking orientation for module {module}")
            self.scanner.output_on()
            correct_orientation[idx] = self.characterization.check_orientation(
                self.scanner
            )
            self.scanner.output_off()
            self.logger.debug(f"Checked orientation for module {module}")

            # Turn off relay
            self.logger.debug(f"Turning off all relays")
            self.relay.all_off()
            self.logger.debug(f"Turned off all relays")

        # Return true if orientation is correct, False otherwise
        check_module_string = ""
        for module in modules:
            self.logger.info(
                f"Module {module} orientation correct: {correct_orientation[idx]}"
            )
            check_module_string += (
                f"Module {module} orientation correct: {correct_orientation[idx]},\n"
            )

        self.logger.info(f"Checked orientation of modules {modules}")

        if len(check_module_string) > 1:
            self.message = check_module_string[0:-2] + "."
        else:
            self.message = "No modules were checked."

    def pass_message(self) -> str:
        """
        Passes message from controller using self.message, set to None after

        Args:
            message (str): message to pass
        """

        self.logger.debug(f"Passing message to controller")

        # Pass message to controller
        message = self.message
        self.message = None
        return message

    def __del__(self) -> None:
        """Stops queue and program on exit"""
        self.stop()


def future_callback(future):
    """Callback function triggered when a future completes. Allows errors to be seen outside event loop"""
    try:
        if future.exception() is not None:
            print(f"Exception in future: {future.exception()}")
            future.result()
    except CancelledError:
        pass
