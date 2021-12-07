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
        self.RESPONSE_TIME = constants["response_time"]
        self.running = False
        self.rootdir = rootdir
        if not os.path.exists(rootdir):
            os.mkdir(rootdir)

        self.relay = Relay()
        self.scanner = Scanner()
        self.easttester = EastTester()

        self.modules = {}
        # probably want to change max_workers
        self.threadpool = ThreadPoolExecutor(max_workers=2)
        self.start()



    # Create new 'module' class for each test 
    def load_module(self, id, name, area, interval, vmin, vmax, steps):

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
        # also, we will need to implement the finding MPP of string, combine in series (i assume), and calc mpp to start tracking with
        self.modules[id] = {
            "name": name,
            "area": area,
            "interval": interval,
            "vmin": vmin,
            "vmax": vmax,
            "steps": steps,
            "jv_scan_count": 0,
            "_future": future,
            "_savedir": self._make_module_subdir(name),
            "mpp_scan_count": 0,
            "v_mpp": None,
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


    # manages JV scanning --> called by start()
    async def jv_worker(self, loop):
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


    # manages MPP tracking for ET #1 --> called by start()
    async def mpp_worker_12(self, loop):
        # maybe here we could edit for priority 
        while self.running:
            id = await self.queue.get()
            scan_future = asyncio.gather(
                loop.run_in_executor(
                    self.threadpool,
                    self.track_mpp,
                    id,
                )
            )
            scan_future.add_done_callback(future_callback)
            print(f"Tracking {id}")
            await scan_future
            self.queue.task_done()
            print(f"Done Tracking {id}")


    # manages MPP tracking for ET #2 --> called by start()
    async def mpp_worker_34(self, loop):
        while self.running:
            id = await self.queue.get()
            scan_future = asyncio.gather(
                loop.run_in_executor(
                    self.threadpool,
                    self.track_mpp,
                    id,
                )
            )
            scan_future.add_done_callback(future_callback)
            print(f"Tracking {id}")
            await scan_future
            self.queue.task_done()
            print(f"Done Tracking {id}")


    # manages MPP tracking for ET #3 --> called by start()
    async def mpp_worker_56(self, loop):
        while self.running:
            id = await self.queue.get()
            scan_future = asyncio.gather(
                loop.run_in_executor(
                    self.threadpool,
                    self.track_mpp,
                    id,
                )
            )
            scan_future.add_done_callback(future_callback)
            print(f"Tracking {id}")
            await scan_future
            self.queue.task_done()
            print(f"Done Tracking {id}")


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
        asyncio.run_coroutine_threadsafe(self.jv_worker(self.loop), self.loop)
        asyncio.run_coroutine_threadsafe(self.mpp_worker_12(self.loop), self.loop)
        asyncio.run_coroutine_threadsafe(self.mpp_worker_34(self.loop), self.loop)
        asyncio.run_coroutine_threadsafe(self.mpp_worker_56(self.loop), self.loop)
        self.running = True


    # stop schedueler --> called by __del__()
    def stop(self):
        self.running = False
        ids = list(self.modules.keys())
        for id in ids:
            self.unload_module(id)
        self.loop.call_soon_threadsafe(self.loop.stop)
        self.thread.join()


    # JV scan a module & save the info --> called by jv_worker()
    def scan_jv(self, id):
    
        # get list of modules
        d = self.modules.get(id, None)
        if d is None:
            raise ValueError(f"No module loaded at index {id}!")

        # Get date/time and make filepath
        date_str = datetime.now().strftime("%Y-%m-%d")
        time_str = datetime.now().strftime("%H:%M:%S")
        epoch_str = time.time()
        fpath = os.path.join(d["_savedir"], f"{d['name']}_JV_{d['jv_scan_count']}.csv")

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

        # calculate MPP
        if ["jv_scan_count"] == 0:
            d["v_mpp"] = self.calc_mpp_from_jv(v,fwd_p,rev_p)

        # increase scan count
        d["jv_scan_count"] += 1



    # Take JV scan and obtain vmpp --> wrote into seperate function so we can change later
    def calc_mpp_from_jv(self,v,fwd_p,rev_p):
        avg_p = (rev_p+fwd_p)/2
        v_maxloc = np.argmax(avg_p)
        v_mpp = v[v_maxloc]

        return v_mpp


    # eventually we can scale these by stats from JV scans to approx param from each
    def track_mpp(self, id):

        # go through ids, make sure they are real, add up vmps and areas
        vmpp_all = 0
        area_all = 0
        for id in ids:

            # make sure it exists
            d = self.modules.get(id, None)
            if d is None:
                raise ValueError(f"No module loaded at index {id}!")

            # grab MPP & areas
            vmpp_all += d["v_mpp"]
            area_all += d["area"]


        # Get date/time
        date_str = datetime.now().strftime("%Y-%m-%d")
        time_str = datetime.now().strftime("%H:%M:%S")
        epoch_str = time.time()

        # MPPT string using area and vmpp from above
        t, v1, i1 ,p1 = self.easttester.track_mpp(self.relay.et_channels[id],vmpp_all)

        # cycle through IDs, save and update each file indivisually (should help with processing)
        for id in ids:

            # make sure it exists
            d = self.modules.get(id, None)
            if d is None:
                raise ValueError(f"No module loaded at index {id}!")

            # get info:
            v = v1 / len(ids)
            i = i1 * d["area"] / area_all
            j = i / d["area"] 
            p = j * v


            # grab filepath
            fpath = os.path.join(d["_savedir"], f"{d['name']}_MPP_{d['mpp_scan_count']}.csv")

            # Open file, write header/column names then fill 
            with open(fpath, "w", newline="") as f:
                writer = csv.writer(f, delimiter=",")
                writer.writerow(["Date", date_str])
                writer.writerow(["Time", time_str])
                writer.writerow(["epoch_time", epoch_str])
                writer.writerow(["Relay IDs", ids])
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
            d["mpp_scan_count"] += 1

             # set MPP
            d["v_mpp"] = v1[-1]/len(ids)



    # calls self.stop() if program closes
    def __del__(self):
        self.stop()


# allows errors to be seen outside of the main event loop --> called by load_module() and jv_worker()
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
