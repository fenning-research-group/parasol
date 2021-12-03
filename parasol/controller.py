# import numpy as np
# import logging
# from threading import Lock

# Import Modules
import time
import asyncio
from threading import Thread
from concurrent.futures import ThreadPoolExecutor
from concurrent.futures._base import CancelledError
import yaml
import os
import csv
from datetime import datetime
import time
from .hardware.relay import Relay
from .hardware.scanner import Scanner


"""
NOTES ON HOW THE PROGRAM WORKS

# Init statement
c = parasol.Controller(rootdir = "filepath_to_save_in")

# Add Module to quelist
c.load_module(self, id, name, area, interval, vmin, vmax, steps)

# Remove Module from quelist
c.unload_module(self, id):
"""


# max number modules 
NUM_MODULES = 24


# Set yaml name, load controller info
MODULE_DIR = os.path.dirname(__file__)
with open(os.path.join(MODULE_DIR, "hardwareconstants.yaml"), "r") as f:
    constants = yaml.load(f, Loader=yaml.FullLoader)["controller"]


# Create controller class for schedueler
class Controller:

    # initialize controller
    def __init__(self, rootdir):
        self.running = False
        self.rootdir = rootdir
        if not os.path.exists(rootdir):
            os.mkdir(rootdir)

        self.relay = Relay()
        self.scanner = Scanner()

        self.modules = {}
        self.threadpool = ThreadPoolExecutor(max_workers=2)
        self.start()


    # Create new 'module' class for each test 
    def load_module(self, id, name, area, interval, vmin, vmax, steps, et_channel, mppt_duration, mppt_voltage_step, mppt_i_averagenum):

        # set these here for now
        mppt_duration = 120
        mppt_voltage_step = 0.05
        mppt_i_averagenum = 5

        # add module id, state if already there or if id is incorrect
        if id in self.modules:
            raise ValueError(f"Module {id} already loaded!")
        if id not in self.relay.relay_commands:
            raise ValueError(f"{id} not valid relay id!")

        # add to timer and loop
        future = asyncio.run_coroutine_threadsafe(self.timer(id=id), self.loop)
        future.add_done_callback(future_callback)

        # create self.modules[] info for running
        # ideally et_channel can be combined with the relay board information so that we can get that autopopulated
        self.modules[id] = {
            "name": name,
            "area": area,
            "interval": interval,
            "vmin": vmin,
            "vmax": vmax,
            "steps": steps,
            "scan_count": 0,
            "_future": future,
            "_savedir": self._make_module_subdir(name),
            "et_channel": et_channel,
            "mppt_duration": mppt_duration,
            "mppt_voltage_step": mppt_voltage_step,
            "mppt_i_averagenum": mppt_i_averagenum
        }


    # Delete 'module' class / remove module from testing que
    def unload_module(self, id):
        if id not in self.modules:
            raise ValueError(f"Module {id} not loaded!")
        self.modules[id]["_future"].cancel()
        del self.modules[id]
        while id in self.queue._queue:
            self.queue._queue.remove(id)


    # makes folders to hold data --> called by load_module()
    def _make_module_subdir(self, name):
        idx = 0
        fpath = os.path.join(self.rootdir, name)
        while os.path.exists(fpath):
            idx += 1
            fpath = os.path.join(self.rootdir, f"{name}_{idx}")

        os.mkdir(fpath)
        return fpath


    # manages scanning --> called by start()
    async def worker(self, loop):
        while self.running:
            id = await self.queue.get()
            scan_future = asyncio.gather(
                loop.run_in_executor(
                    self.threadpool,
                    self.scan_jv,
                    id,
                )
            )
            scan_future.add_done_callback(future_callback)
            print(f"Scanning {id}")
            await scan_future
            self.queue.task_done()
            print(f"Done Scanning {id}")


    # manages timing --> called by load_module()
    async def timer(self, id):
        # wait to let the module dict populate
        await asyncio.sleep(1) 
        while self.running:
            self.queue.put_nowait(id)
            await asyncio.sleep(self.modules[id]["interval"])


    # setup background event loop for schedueling tasks --> called by start()
    def __make_background_event_loop(self):
        def exception_handler(loop, context):
            print("Exception raised in Controller loop")

        self.loop = asyncio.new_event_loop()
        self.loop.set_exception_handler(exception_handler)
        asyncio.set_event_loop(self.loop)
        self.queue = asyncio.Queue()
        self.loop.run_forever()


    # start schedueler --> called by __init__()
    def start(self):
        self.thread = Thread(target=self.__make_background_event_loop)
        self.thread.start()
        time.sleep(0.5)
        asyncio.run_coroutine_threadsafe(self.worker(self.loop), self.loop)
        self.running = True


    # stop schedueler --> called by __del__()
    def stop(self):
        self.running = False
        ids = list(self.modules.keys())
        for id in ids:
            self.unload_module(id)
        self.loop.call_soon_threadsafe(self.loop.stop)
        self.thread.join()


    # JV scan a module & save the info --> called by worker()
    def scan_jv(self, id):
    
        # get list of modules
        d = self.modules.get(id, None)
        if d is None:
            raise ValueError(f"No module loaded at index {id}!")

        # Get date/time and make filepath
        date_str = datetime.now().strftime("%Y-%m-%d")
        time_str = datetime.now().strftime("%H:%M:%S")
        epoch_str = time.time()
        fpath = os.path.join(d["_savedir"], f"{d['name']}_{d['scan_count']}_JV.csv")

        # Scan device foward + reverse, calculate current density and power for both
        self.relay.on(id)
        v, fwd_i, rev_i = self.scanner.scan_jv(vmin=d["vmin"], vmax=d["vmax"], steps=d["steps"])
        fwd_j = fwd_i / d["area"]
        fwd_p = v * fwd_j
        rev_j = rev_i / d["area"]
        rev_p = v * rev_j

        # Open file, write header/column names then fill 
        with open(fpath, "w", newline="") as f:
            writer = csv.writer(f, delimiter=",")
            writer.writerow(["Date", date_str])
            writer.writerow(["Time", time_str])
            writer.writerow(["epoch_time", epoch_str])
            writer.writerow(["Relay ID", id])
            writer.writerow(["Area (cm2)", d["area"]])
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

        # increase scan count
        d["scan_count"] += 1


    # not sure how best to organize it but we have worker1 which scans JV
    # we then want to create worker2 that does MPP using Vmpp from JV (if JV was last thing done) or last MPP scan
    # for now i think we prioritize JV scans and do MPPT in downtime.




    # Take JV scan and obtain vmpp
    def calc_mpp_from_jv(self,fwd_p,rev_p,v):
        avg_p = (rev_p+fwd_p)/2
        v_maxloc = np.argmax(avg_p)
        v_mpp = v[v_maxloc]

        return v_mpp


    # hacked  this together from the scanner code --> Rishi can you please take a look at it?
    # idea is that we can feed in id & voltage to start scan at and then track mpp from there
    def track_mpp(self, id, voltage):

         # get list of modules
        d = self.modules.get(id, None)
        if d is None:
            raise ValueError(f"No module loaded at index {id}!")

        # Get date/time and make filepath
        date_str = datetime.now().strftime("%Y-%m-%d")
        time_str = datetime.now().strftime("%H:%M:%S")
        epoch_str = time.time()
        fpath = os.path.join(d["_savedir"], f"{d['name']}_{d['scan_count']}_MPP.csv")


        ## NEED TO KNOW HOW TO DEAL WITH 2 CHANNELS HERE (maybe connect with the relay commands) 
        self.relay.on(id)
        t, v, i ,p = self.easttester.track_mpp(d["et_channel"],voltage,d["mppt_duration"],d["mppt_voltage_step"],d["mppt_i_averagenum"])
        j = i / d["area"]
        p = p / d["area"]


        # Open file, write header/column names then fill 
        with open(fpath, "w", newline="") as f:
            writer = csv.writer(f, delimiter=",")
            writer.writerow(["Date", date_str])
            writer.writerow(["Time", time_str])
            writer.writerow(["epoch_time", epoch_str])
            writer.writerow(["Relay ID", id])
            writer.writerow(["Area (cm2)", d["area"]])
            writer.writerow(
                [
                    "Time (epoch)",
                    "Voltage (V)",
                    "Current (mA)",
                    "Current Density (mA/cm2)",
                    "Power Density (mW/cm2)",
                ]
            )
            for line in zip(t, v, i, j, p):
                writer.writerow(line)

        # increase scan count
        d["scan_count"] += 1


    # calls self.stop() if program closes
    def __del__(self):
        self.stop()

# allows errors to be seen outside of the main event loop --> called by load_module() and worker()
def future_callback(future):
    """
    Callback function triggered when a future completes.
    Allows errors to be seen outside event loop
    """
    try:
        if future.exception() is not None:
            print(f"Exception in future: {future.exception()}")
            raise future.exception()
    except CancelledError:
        pass
