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
            5: (65, 5),
            6: (65, 6),
            7: (65, 7),
            8: (65, 8),
            9: (65, 9),
            10: (65, 10),
            11: (65, 11),
            12: (65, 12),
            13: (65, 13),
            14: (65, 14),
            15: (65, 15),
            16: (65, 16),
            17: (65, 17),
            18: (65, 18),
            19: (65, 19),
            20: (65, 20),
            21: (65, 21),
            22: (65, 22),
            23: (65, 23),
            24: (65, 24),
        }

        # self.connect(constants["address"]) #TODO actually connect
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
            # self.inst.write_raw((cmd0).to_bytes(1, "big"))
            # self.inst.write_raw((cmd1).to_bytes(1, "big"))
        time.sleep(self.RESPONSE_TIME)

    def all_off(self):
        with self.lock:
            print(f"Turning off all relays")
            # self.inst.write_raw((72).to_bytes(1, "big"))
        time.sleep(self.RESPONSE_TIME)
