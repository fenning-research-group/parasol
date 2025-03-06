import time
import asyncio
from threading import Thread, Lock
from concurrent.futures import ThreadPoolExecutor
from concurrent.futures._base import CancelledError
import os
import csv
from datetime import datetime
import time
import logging
import sys
import traceback #added by ZJD 01/13/2025
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import smtplib

import numpy as np

from parasol.relay.relay import Relay
from parasol.hardware.yokogawa import Yokogawa
from parasol.hardware.chroma import Chroma
from parasol.environmental import Environmental

from parasol.analysis.analysis import Analysis
from parasol.characterization import Characterization
from parasol.filestructure import FileStructure

from parasol.configuration.configuration import Configuration
config = Configuration()
constants = config.get_config()['controller']


class Controller:
    """Controller package for PARASOL"""

    # Initialize kit, start/stop workers, file management
    
    def __init__(self, mode = None, logging_on=True, backup = True) -> None:
        """Initializes the Controller class

        Args:
            logging_on (boolean): Option to log or not, default True
        """
        
        # Grab mode -> indoor or outdoor
        self.mode = mode

        # Grab backup -> local disk or backup drive
        # self.backup = backup #added by ZJD 01/29/2024
        
        # Get constants from yaml file
        self.monitor_delay = constants["monitor_delay"]
        self.measurement_delay = constants["measurement_delay"]
        self.mpp_points = constants["mpp_points"]
        self.num_modules = constants["num_modules"]
        self.num_strings = constants["num_strings"]
        
        # Load modules that dont have hardware associated & Relay (needed for base organization), load optionals as False (load in during customize)
        self.characterization = Characterization()
        self.analysis = Analysis()
        self.filestructure = FileStructure() 
        # self.fstructure_backup = FileStructure(backup = self.backup)# added by ZJD 01/29/2024
        self.relay = Relay()
        
        self.environment = False
        self.scanner = False
        self.load = False
        self.monitor = False
        self.env_control = False

        # # Create variables to save the name of the file that is to be copied, ZJD 01/29/2024
        # self.savedEnv = None
        # self.backup_savedEnv = None

        # self.savedMPP = None
        # self.backup_savedMPP = None

        # Initialize running
        self.running = False

        # Create blank message that can be checked from other programs (used in RUN_UI)
        self.message = None

        # Map string ID to load port and channel
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
        
        # Create a blank dictionary to hold all info about monitoring stations
        self.monitor_stations = {}
        
        # Create blank dictionary to hold all info about strings
        self.strings = {}

        # Create list of active strings
        self.active_strings = [False] * (len(self.load_channels)+1)
        
        # Create characterization and logging directories
        self.characterizationdir = self.filestructure.get_characterization_dir()
        if not os.path.exists(self.characterizationdir):
            os.mkdir(self.characterizationdir)
        self.logdir = self.filestructure.get_log_dir()
        if not os.path.exists(self.logdir):
            os.mkdir(self.logdir)

        # # Create backup characterization and logging directories, added by ZJD 01/29/2024
        # self.backup_characterizationdir = self.fstructure_backup.get_characterization_dir()
        # if not os.path.exists(self.backup_characterizationdir):
        #     os.mkdir(self.backup_characterizationdir)
        # self.logdir = self.fstructure_backup.get_log_dir()
        # if not os.path.exists(self.logdir):
        #     os.mkdir(self.logdir)

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

        # Create workers (1 for scanner, 1 for loads, 1 for random tasks, 1 for environment) & start queue
        self.threadpool = ThreadPoolExecutor(max_workers=4)
        self.start()
        
        # Initialize appropriate modules for the mode
        self.customize()


    def customize(self) -> None:
        """Initializes hardware for test type"""
        
        if self.mode == 'outdoor':

            if constants['outdoor_config']['scanner']:
                self.scanner = Yokogawa()
            if constants['outdoor_config']['load']:
                self.load = Chroma()
            if constants['outdoor_config']['monitor']:
                self.monitor = True
            if constants['outdoor_config']['env_control']:
                self.env_control = False
            
            # Map string id to monitoring station
            self.monitor_stations = {
                1: 0,
                2: 0,
                3: 0,
                4: 0,
                5: 0,
                6: 0,
            }
            
        if self.mode == 'indoor':

            if constants['indoor_config']['scanner']:
                self.scanner = Yokogawa()
            if constants['indoor_config']['load']:
                self.load = False
            if constants['indoor_config']['monitor']:
                self.monitor = True
            if constants['indoor_config']['env_control']:
                self.env_control = True
            
            
            # Map string id to monitoring station
            self.monitor_stations = {
                1: 1,
                2: 2,
                3: 3,
                4: 4,
                5: 5,
                6: 6,
            }
        
        if self.monitor or self.env_control:
            stations = list(set(self.monitor_stations.values()))
            self.environment = Environmental(self.mode, stations)

    def update_monitoring(self):
        
        # for all active strings, calculate strings that must be monitored
        self.monitor_list = []
        for id in range(len(self.active_strings)):
            if self.active_strings[id]:
                self.monitor_list.append(self.monitor_stations[id])
        self.monitor_list = list(set(self.monitor_list))

        # create dictionary to map monitoring stations to string ids for saving
        self.station_to_id = {}

        # cycle through monitor stations
        for monitor_station in self.monitor_list:
            
            # if string is active and its station is the monitor station were on, then add to list
            temp = []
            for id in range(len(self.active_strings)):
                if self.active_strings[id]:
                    if self.monitor_stations[id] == monitor_station:
                        temp.append(id)
            
            # create dict item for each monitoring station
            self.station_to_id[monitor_station] = temp
        


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
        temp: float,
        rh: float,
        intensity: float,
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
            temp (float): temperature setpoint
            rh (float): relative humidity setpoint
            intensity (float): light intensity setpoint

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

        # Setup JV and MPP timers in main loop if interval exists, else set to None
        if jv_interval:
            jv_future = asyncio.run_coroutine_threadsafe(self.jv_timer(id=id), self.loop)
            jv_future.add_done_callback(future_callback)
        else:
            jv_future = None
        if mpp_interval:
            mpp_future = asyncio.run_coroutine_threadsafe(self.mpp_timer(id=id), self.loop)
            mpp_future.add_done_callback(future_callback)
        else:
            mpp_future = None
            
        # If we are not already monitoring the environment, start the monitor
        if not any(self.active_strings):
            self.logger.debug(f"Starting environmental monitoring")
            self.monitor_future = asyncio.run_coroutine_threadsafe(
                self.monitor_timer(), self.loop
            )
            self.monitor_future.add_done_callback(future_callback)
            self.logger.info(f"Started environmental monitoring")

        # Make string active, update monitoring list
        self.active_strings[id] = True
        self.update_monitoring()

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
                "last_currents": [None]*self.mpp_points,
                "last_powers": [None]*self.mpp_points,
                "last_voltages": [None]*self.mpp_points,
                "_future": mpp_future,
                "vmpp": None,
            },
            "setpoints": {
                "temp": temp,
                "rh": rh,
                "intensity": intensity,
            },
            "lock": Lock(),
        }

        # TODO: check if this works
        # if JV scans are off, set first mpp to 0 so that MPP progresses
        if jv_interval is None:
            self.strings[id]["mpp"]["last_currents"][0] = 0
            self.strings[id]["mpp"]["last_powers"][0] = 0
            self.strings[id]["mpp"]["last_voltages"][0] = 0
            self.strings[id]["mpp"]["vmpp"] = 0

        # Make directories/file structure
        (
            self.strings[id]["_savedir"],
            self.strings[id]["name"],
        ) = self.filestructure.make_module_subdir(name, module_channels, startdate)

        # # Make backup directories/file structure, added by ZJD 01/29/2024
        # (
        #     self.strings[id]["_savedir"],
        #     self.strings[id]["name"],
        # ) = self.fstructure_backup.make_module_subdir(name, module_channels, startdate)        
        self.logger.info(f"String {id} loaded")
        
        # start environmental control
        if self.env_control:
            if self.strings[id]["setpoints"]["temp"]:
                self.environment.set_temperature(id, self.strings[id]["setpoints"]["temp"])
            if self.strings[id]["setpoints"]["rh"]:
                self.environment.set_rh(id, self.strings[id]["setpoints"]["rh"])
            if self.strings[id]["setpoints"]["intensity"]:
                self.environment.set_intensity(id, self.strings[id]["setpoints"]["intensity"])

        # Turn on the load here, stays on when not being scanned
        if self.load:
            self.logger.debug(f"Turning on load output for string {id}")
            ch = self.load_channels[id]
            self.load.load_on(ch, 0.00)
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

            # Destroy all future tasks for the string if that task has a future
            if id not in self.strings:
                raise ValueError(f"String {id} not loaded!")
            self.logger.debug(f"Canceling tasks for {id}")
            if self.strings[id]["jv"]["_future"]:
                self.strings[id]["jv"]["_future"].cancel()
            if self.strings[id]["mpp"]["_future"]:
                self.strings[id]["mpp"]["_future"].cancel()
            self.logger.debug(f"Canceled tasks for {id}")

            # Remove all tasks in que not already started (can start 1 from each worker)
            self.logger.debug(f"Removing tasks from que for {id}")
            while id in self.jv_queue._queue:
                self.jv_queue._queue.remove(id)
            while id in self.mpp_queue._queue:
                self.mpp_queue._queue.remove(id)
            self.logger.debug(f"Removed tasks from que for {id}")

            # Make string inactive, and update monitoring list
            self.active_strings[id] = False
            self.update_monitoring()

            # If we have no active tests, stop monitoring
            if not any(self.active_strings):
                self.logger.debug(f"Canceling environmental monitoring")
                time.sleep(self.monitor_delay)
                self.monitor_future.cancel()
                self.logger.info(f"Environmental monitoring canceled")

            # Turn load output off
            if self.load:
                self.logger.debug(f"Resetting load for {id}")
                ch = self.load_channels[id]
                self.load.load_off(ch)
                self.logger.debug(f"Load reset for {id}")
            
            # Turn off environmental control
            if self.env_control:
                if self.strings[id]["setpoints"]["temp"]:
                    self.environment.temperature_off(id)
                if self.strings[id]["setpoints"]["rh"]:
                    self.environment.rh_off(id)
                if self.strings[id]["setpoints"]["intensity"]:
                    self.environment.intensity_off(id)

            # Analyze the saveloc in a new thread
            self.logger.debug(f"Saving analysis at : {saveloc}")
            analyze_thread = Thread(
                target=self.analysis.analyze_from_savepath, args=(saveloc,)
            )
            analyze_thread.start()

        # Delete the string
        del self.strings[id]

        self.logger.info(f"Analysis saved at : {saveloc}")

    def make_mpp_file(self, id: int, backup_mpp = False) -> None:
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

    #    # Save in backup base filepath: stringname: MPP: stringname_stringid_mpp_# (matches JV #), added by ZJD 01/29/2024
    #     backup_mppfolder = self.fstructure_backup.get_mpp_folder(d["start_date"], d["name"])
    #     backup_mppfile = self.fstructure_backup.get_mpp_file_name(
    #         d["start_date"], d["name"], id, d["jv"]["scan_count"]
    #     )
        fpath = os.path.join(mppfolder, mppfile)
        # backup_fpath = os.path.join(backup_mppfolder, backup_mppfile)

        # if not backup_mpp:
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
        # else:
        #     return backup_fpath

    def make_env_file(self, id, backup_env = False) -> None:
        """Creates base file for environmental monitoring data
        
        Args:
            id (int): string number
        """

        # Get dictionary for string
        d = self.strings.get(id, None)

        # Get date/time
        currenttime = datetime.now()
        cdate = currenttime.strftime("x%Y%m%d")

        # Get environment folder and file
        envfolder = self.filestructure.get_environment_folder(d["start_date"], d["name"])
        envfile = self.filestructure.get_environment_file_name(cdate)
        fpath = os.path.join(envfolder, envfile)


        # # Get backup environment folder and file, added by ZJD 01/29/2024
        # backup_envfolder = self.fstructure_backup.get_environment_folder(d["start_date"], d["name"])
        # backup_envfile = self.fstructure_backup.get_environment_file_name(cdate)
        # backup_fpath = os.path.join(backup_envfolder, backup_envfile)

        # if not backup_env: # ZJD
        #     Make file if it doesn't exist
        if os.path.exists(fpath) != True:

            # Open file, write header/column names then fill
            with open(fpath, "w", newline="") as f:
                writer = csv.writer(f, delimiter=",")
                writer.writerow(
                    [
                        "Time (Epoch)",
                        "Temperature Dark (C)",
                        "Temperature Light (C)",
                        "RH (%)",
                        "Intensity (# Suns)",
                    ]
                )

            self.logger.debug(f"Environmental monitoring file made at {fpath}")

        return fpath
        # else: # ZJD
        #     return backup_fpath 

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
            # Add worker to queue, increase mpp worker count
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
            self.send_error_email('Error occured on rooftop')

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

        # Create MPP workers for load
        asyncio.run_coroutine_threadsafe(self.mpp_worker(self.loop), self.loop)

        # Create check orientation worker
        asyncio.run_coroutine_threadsafe(
            self.check_orientation_worker(self.loop), self.loop
        )

        # Turn on running
        self.running = True


    def stop(self) -> None:
        """Delete workers,  stop queue, and reset hardware"""

        # Unload all strings, reset loads
        ids = list(self.strings.keys())
        for id in ids:
            self.unload_string(id)

        # Cancel loops, join threads
        self.loop.call_soon_threadsafe(self.loop.stop)
        self.thread.join()

        # force wait until all active strings have been terminated
        while any(self.active_strings):
            time.sleep(1)

        # Close all channels on the relay
        self.logger.debug(f"Turning off relays")
        self.relay.all_off()
        self.logger.debug(f"Turned off relays")

        # Reset scanner
        self.logger.debug(f"Resetting scanner")
        self.scanner.output_off()
        self.logger.debug(f"Scanner reset")

        # Turn off running
        self.running = False

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
            if self.load:
                self.logger.debug(f"Turning off load output for string {id}")
                ch = self.load_channels[id]
                self.load.load_off(ch)
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


                # # Save in backup base filepath: stringname: JV_modulechannel: stringname_stringid_modulechannel_JV_scannumber, added by ZJD 01/29/2024
                # backup_jvfolder = self.fstructure_backup.get_jv_folder(
                #     d["start_date"], d["name"], module
                # )

                fpath = os.path.join(jvfolder, jvfile) 
                # backup_fpath = os.path.join(backup_jvfolder, jvfile) 

                

                # Open relay, scan device foward + reverse, turn off relay
                self.logger.debug(f"Opening relay for string {id}")
                self.relay.on(module)
                self.logger.debug(f"Opened relay for string {id}")
                self.logger.debug(f"Scanning string {id}")

                # Wait set time and scan
                time.sleep(self.measurement_delay)
                v, fwd_vm, fwd_i, rev_vm, rev_i = self.characterization.scan_jv(d, self.scanner)


                self.logger.debug(f"Scanned string {id}")
                self.logger.debug(f"Closing relay for string {id}")
                self.relay.all_off()
                self.logger.debug(f"Closed relay for string {id}")

                # Convert to mA, calculate parameters
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
                # shutil.copy(fpath, backup_fpath)# ZJD 01/29/2024
                self.logger.debug(f"Writing JV file for {id} at {fpath}")
                # self.logger.debug(f"Backup'ed JV file for {id} at {backup_fpath}")# ZJD 01/29/2024

                # Save any useful raw data to the string dictionary
                d["jv"]["v"][index] = v
                d["jv"]["j_fwd"][index] = fwd_j
                d["jv"]["j_rev"][index] = rev_j

            # Increase JV scan count
            d["jv"]["scan_count"] += 1
            
            # After last scan/relay shut, wait 0.5s before turning on mpp
            time.sleep(self.measurement_delay)

            # Turn on load output at old vmpp if we have one
            if self.load:
                vmp = self.characterization.calc_last_vmp(d)
                if vmp is not None:
                    self.logger.debug(f"Turning on load output for string {id}")
                    self.load.load_on(ch,vmp)
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

            # shift index to index + 1 and add new reading at 0
            d["mpp"]["last_voltages"] = [(v+vm)/2] + d["mpp"]["last_voltages"][:-1]
            d["mpp"]["last_currents"] = [i] + d["mpp"]["last_currents"][:-1]
            d["mpp"]["last_powers"]= [(p+pm)/2] + d["mpp"]["last_powers"][:-1]
            d["mpp"]["vmpp"] = v            

            # Get MPP file path, if it doesnt exist, create it, iterate for each JV curve taken
            fpath = self.make_mpp_file(id)
            backup_fpath = self.make_mpp_file(id, backup_mpp=True) # just a path, no file written

            # if self.savedMPP is None: #ZJD 10/29/2024
            #     self.savedMPP = fpath
            # if self.backup_savedMPP is None:
            #     self.backup_savedMPP = backup_fpath

            # if self.savedMPP != fpath: #ZJD 10/29/2024
            #     shutil(self.savedMPP, self.backup_savedMPP)
            #     self.savedMPP = fpath
            #     self.backup_savedMPP = backup_fpath

            # Open file, append values to columns
            with open(fpath, "a", newline="") as f:
                writer = csv.writer(f, delimiter=",")
                writer.writerow([t, v, vm, i, j, pm])
            # shutil.copy(fpath, backup_fpath) # ZJD 01/29/2024

            self.logger.debug(f"Writing MPP file for {id} at {fpath}")
            # self.logger.debug(f"Backup'ed MPP file for {id} at {backup_fpath}")# ZJD 01/29/2024

            self.logger.info(f"Tracked {id}")
            

    def monitor_env(self, dummyid: int) -> None:
        """
        Monitors environment using the Monitor class

        Args:
            dummyid (int): passes int 1 to the monitor class
        """
        
        self.logger.debug(f"Monitoring environment")

        
        #cycle through monitor stations active
        for monitor_station in self.monitor_list:
        
            # Set time and -1 for temp, rh, and humidity 
            t, temp_dark, temp_light, rh, intensity = time.time(), -1, -1, -1, -1
            
            # If we are monittoring: get Time, Temperature, Relative Humidity, and Temperature
            if self.monitor:
                t, temp_dark, temp_light, rh, intensity = self.environment.monitor_environment(monitor_station)

            # Save monitor information for each channel
            for id in self.station_to_id[monitor_station]:
                # Make env file if needed and append to file
                fpath = self.make_env_file(id)
                # backup_fpath = self.make_env_file(id, backup_env=True) #ZJD 01/29/2024

                # # If savedEnv and backup_savedEnv are not initialized: ZJD 01/29/2024
                # if self.savedEnv is None:
                #     self.savedEnv = fpath
                # if self.backup_savedEnv is None:
                #     self.backup_savedEnv = backup_fpath
                
                # # Check if the file has been updated, ZJD 01/29/2024
                # if self.savedEnv != fpath:
                #     shutil(self.savedEnv, self.backup_savedEnv)
                #     self.savedEnv = fpath
                #     self.backup_fpath = backup_fpath
                    
                with open(fpath, "a", newline="") as f:
                    writer = csv.writer(f, delimiter=",")
                    writer.writerow([t, temp_dark, temp_light, rh, intensity])
                self.logger.debug(f"Writing Monitoring file at {fpath}")


        self.logger.debug(f"Monitored environment")

    def check_orientation(self, modules: list) -> None:
        """Checks the orientation of the list of modules by verifying that Jsc > 0 using the scanner

        Args:
            modules (list[int]): list of modules
        """
        # x = 10/0

        self.logger.debug(f"Checking orientation")

        # Make string to hold # of correct orientations
        correct_orientation = [None] * len(modules)
        check_module_string = ""

        # Cycle through each module, calc orientation
        for idx, module in enumerate(modules):

            # Turn on relay
            self.logger.debug(f"Turning on relay for module {module}")
            self.relay.on(module)
            self.logger.debug(f"Turned on relay for module {module}")

            # Wait for everything to settle
            time.sleep(self.measurement_delay)

            # Pass scanner to characterization module, returns true if Isc < 0, false otherwise
            self.logger.debug(f"Checking orientation for module {module}")
            correct_orientation[idx] = self.characterization.check_orientation(
                self.scanner
            )
            self.logger.debug(f"Checked orientation for module {module}")

            # Turn off relay
            self.logger.debug(f"Turning off all relays")
            self.relay.all_off()
            self.logger.debug(f"Turned off all relays")

        
        # Return true if orientation is correct, False otherwise
        for idx, module in enumerate(modules):
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

    # def send_error_email(self, error_message) -> None:
    #     """
    #     Send user an alert email when an error is raised
    #     """
    #     sender_email = "frgrooftopalert@gmail.com"
    #     receiver_email = "z8deng@ucsd.edu"
    #     password = "FrgRooftopAlertZJD"  # Use an app-specific password for security

    #     message = MIMEMultipart()
    #     message['From'] = sender_email
    #     message['To'] = receiver_email
    #     message['Subject'] = "Error Occurred in Python Script"

    #     body = f"An error occurred:\n\n{error_message}"
    #     message.attach(MIMEText(body, 'plain'))

    #     try:
    #         with smtplib.SMTP('smtp.gmail.com', 587) as server:
    #             server.starttls()
    #             server.login(sender_email, password)
    #             server.send_message(message)
    #         print("Error email sent successfully!")
    #     except Exception as e:
    #         print(f"Failed to send email: {e}")

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


