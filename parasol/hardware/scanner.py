# import pyvisa
import time
import yaml
import os
import numpy as np

from threading import Lock

MODULE_DIR = os.path.dirname(__file__)
with open(os.path.join(MODULE_DIR, "..", "hardwareconstants.yaml"), "r") as f:
    constants = yaml.load(f, Loader=yaml.FullLoader)["scanner"]


class Scanner:
    def __init__(self) -> None:
        self.lock = Lock()
        pass

    def scan(self, vmin, vmax, steps):
        with self.lock:  # this is important - only allows one thread to access the hardware at a time
            v = np.linspace(vmin, vmax, steps)
            i = np.zeros(steps)
        time.sleep(3)  # simulate the time it takes to scan
        return v, i
