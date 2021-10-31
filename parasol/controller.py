import time
import asyncio
from threading import Thread, Lock
from concurrent.futures import ThreadPoolExecutor
from concurrent.futures._base import CancelledError
import numpy as np
import yaml
import os
import csv
from datetime import datetime

import asyncio
import time
import logging


from .hardware.relay import Relay
from .hardware.scanner import Scanner

NUM_MODULES = 24

MODULE_DIR = os.path.dirname(__file__)
with open(os.path.join(MODULE_DIR, "hardwareconstants.yaml"), "r") as f:
    constants = yaml.load(f, Loader=yaml.FullLoader)["controller"]


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


class Controller:
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

    def _make_module_subdir(self, name):
        idx = 0
        fpath = os.path.join(self.rootdir, name)
        while os.path.exists(fpath):
            idx += 1
            fpath = os.path.join(self.rootdir, f"{name}_{idx}")

        os.mkdir(fpath)
        return fpath

    def load_module(self, id, name, area, interval, vmin, vmax, steps):
        if id in self.modules:
            raise ValueError(f"Module {id} already loaded!")
        if id not in self.relay.relay_commands:
            raise ValueError(f"{id} not valid relay id!")

        future = asyncio.run_coroutine_threadsafe(self.timer(id=id), self.loop)
        future.add_done_callback(future_callback)

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
        }

    def unload_module(self, id):
        if id not in self.modules:
            raise ValueError(f"Module {id} not loaded!")
        self.modules[id]["_future"].cancel()
        del self.modules[id]
        while id in self.queue._queue:
            self.queue._queue.remove(id)

    async def worker(self, loop):
        while self.running:
            id = await self.queue.get()
            scan_future = asyncio.gather(
                loop.run_in_executor(
                    self.threadpool,
                    self.scan,
                    id,
                )
            )
            scan_future.add_done_callback(future_callback)
            print(f"Scanning {id}")
            await scan_future
            self.queue.task_done()
            print(f"Done Scanning {id}")

    async def timer(self, id):
        await asyncio.sleep(1)  # let the module dict populated
        while self.running:
            self.queue.put_nowait(id)
            await asyncio.sleep(self.modules[id]["interval"])

    def __make_background_event_loop(self):
        def exception_handler(loop, context):
            print("Exception raised in Controller loop")
            # self.logger.error(json.dumps(context))

        self.loop = asyncio.new_event_loop()
        self.loop.set_exception_handler(exception_handler)
        asyncio.set_event_loop(self.loop)
        self.queue = asyncio.Queue()
        self.loop.run_forever()

    def start(self):
        self.thread = Thread(target=self.__make_background_event_loop)
        self.thread.start()
        time.sleep(0.5)
        asyncio.run_coroutine_threadsafe(self.worker(self.loop), self.loop)
        # time.sleep(0.5)
        # asyncio.set_event_loop(self.loop)
        self.running = True

    def stop(self):
        self.running = False
        ids = list(self.modules.keys())
        for id in ids:
            self.unload_module(id)
        self.loop.call_soon_threadsafe(self.loop.stop)
        self.thread.join()

    def scan(self, id):
        d = self.modules.get(id, None)
        if d is None:
            raise ValueError(f"No module loaded at index {id}!")

        date_str = datetime.now().strftime("%Y-%m-%d")
        time_str = datetime.now().strftime("%H:%M:%S")
        fpath = os.path.join(d["_savedir"], f"{d['name']}_{d['scan_count']}.csv")

        self.relay.on(id)
        v, i = self.scanner.scan(vmin=d["vmin"], vmax=d["vmin"], steps=d["steps"])
        j = i / d["area"]
        p = v * j

        with open(fpath, "w", newline="") as f:
            writer = csv.writer(f, delimiter=",")
            writer.writerow(["Date", date_str])
            writer.writerow(["Time", time_str])
            writer.writerow(["Relay ID", id])
            writer.writerow(["Area (cm2)", d["area"]])
            writer.writerow(
                [
                    "Voltage (V)",
                    "Current Density (mA/cm2)",
                    "Current (mA)",
                    "Power Density (mW/cm2)",
                ]
            )
            for line in zip(v, j, i, p):
                writer.writerow(line)

        d["scan_count"] += 1

    def __del__(self):
        self.stop()
