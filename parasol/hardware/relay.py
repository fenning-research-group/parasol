import serial
import time
import yaml
import os
from threading import Lock

from parasol.hardware.port_finder import get_port


# Set module directory, import constants from yaml file
MODULE_DIR = os.path.dirname(__file__)
with open(os.path.join(MODULE_DIR, "..", "hardwareconstants.yaml"), "r") as f:
    constants = yaml.safe_load(f)["relay"]


def relay_lock(f):
    """Locks relay

    Args:
        f (function): any function that needs to be locked
    """

    def inner(self, *args, **kwargs):
        with self.lock:
            f(self, *args, **kwargs)

    return inner


class Relay:
    """Relay package for PARASOL"""

    def __init__(self) -> None:
        """Initliazes the Relay class"""

        # Get lock and constants
        self.lock = Lock()
        self.RESPONSE_TIME = constants["response_time"]
        self.SETTLE_TIME = constants["settle_time"]

        # Relay commands: [device id] = command to open relay
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

        # Connect to relayboard
        self.connect()

    def connect(self) -> None:
        """Connect to the relay"""

        # Get port information
        port = get_port(constants["device_identifiers"])

        # Connect to relay using serial
        self.inst = serial.Serial(port)

    @relay_lock
    def on(self, id: int) -> None:
        """Turn the relay on

        Args:
            id (int): relay ID (1-24)

        Raises:
            ValueError: ID is not valid
        """

        # If relay ID does not exist, raise error
        if id not in self.relay_commands:
            raise ValueError(f"Invalid relay id")

        # If it does, open it
        cmd0, cmd1 = self.relay_commands[id]
        self.inst.write((cmd0).to_bytes(1, "big"))
        time.sleep(self.RESPONSE_TIME)
        self.inst.write((cmd1).to_bytes(1, "big"))
        time.sleep(self.RESPONSE_TIME)
        time.sleep(self.SETTLE_TIME)

    @relay_lock
    def all_off(self) -> None:
        """Turn all relays off"""

        # Close all relay IDs
        self.inst.write((71).to_bytes(1, "big"))
        time.sleep(self.RESPONSE_TIME)
        time.sleep(self.SETTLE_TIME)
