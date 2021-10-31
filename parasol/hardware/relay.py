# import pyvisa
import time
import yaml
import os

from threading import Lock

MODULE_DIR = os.path.dirname(__file__)
with open(os.path.join(MODULE_DIR, "..", "hardwareconstants.yaml"), "r") as f:
    constants = yaml.load(f, Loader=yaml.FullLoader)["relay"]


class Relay:
    def __init__(self):
        self.RESPONSE_TIME = constants[
            "response_time"
        ]  # seconds for command to complete
        self.relay_commands = {
            1: (65, 1),
            2: (65, 2),
            3: (65, 3),
            4: (65, 4),
            5: (66, 5),
            6: (66, 6),
            7: (66, 7),
            8: (66, 8),
            9: (67, 9),
            10: (67, 10),
            11: (67, 11),
            12: (67, 12),
            13: (68, 13),
            14: (68, 14),
            15: (68, 15),
            16: (68, 16),
            17: (69, 17),
            18: (69, 18),
            19: (69, 19),
            20: (69, 20),
            21: (70, 21),
            22: (70, 22),
            23: (70, 23),
            24: (70, 24),
        }

        self.connect(constants["address"]) #TODO actually connect
        self.lock = Lock()

    def connect(self, address: str):
        self.rm = pyvisa.ResourceManager()
        self.inst = self.rm.open_resource(address)

    def on(self, id: int):
        if id not in self.relay_commands:
            raise ValueError(f"Invalid relay id")

        cmd0, cmd1 = self.relay_commands[id]
        with self.lock:  # this is important - only allows one thread to access the hardware at a time
            print(f"Turning on relay {id}")
            self.inst.write_raw((cmd0).to_bytes(1, "big"))
            self.inst.write_raw((cmd1).to_bytes(1, "big"))
        time.sleep(self.RESPONSE_TIME)

    def all_off(self):
        with self.lock:
            print(f"Turning off all relays")
            self.inst.write_raw((71).to_bytes(1, "big"))
        time.sleep(self.RESPONSE_TIME)
