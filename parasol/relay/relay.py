import yaml
import os

from .modbus import Modbus
from .R421B16 import R421B16
from threading import Lock

import time

## Build ontop of existing package for relay board
## Original package built in 2018 Erriez
## Source: https://github.com/Erriez/R421A08-rs485-8ch-relay-board

## DRIVER: https://ftdichip.com/drivers/vcp-drivers/

from parasol.hardware.port_finder import get_port

# Set module directory, import constants from yaml file
MODULE_DIR = os.path.dirname(__file__)
with open(os.path.join(MODULE_DIR, "..", "hardwareconstants.yaml"), "r") as f:
    constants = yaml.safe_load(f)["relay"]

# lock for relays
def relay_lock(f):
    """Locks relay

    Args:
        f (function): any function that needs to be locked
    """

    def inner(self, *args, **kwargs):
        with self.lock:
            f(self, *args, **kwargs)

    return inner


class Relay():
    
    def __init__(self):
        # 1 board runs 2 cells so 12 boards will handle 6 strings of 4 cells
        # general rule: (NUM_STRINGS * NUM_DEVS * NUM_WIRES <= NUM_BOARDS * NUM_RELAYS / 2)
        self.lock = Lock()
        self.SERIAL_PORT = constants['port']#'COM4' #get_port(constants["device_identifiers"])
        # self.DELAY = 0.15 # delay between commands 
        
        self.NUM_DEVS = 4 # number of devices per load string
        self.NUM_WIRES = 4 # number of wires used per device (4 or 2)
        self.NUM_RELAYS = 16 # number of relays per load board
        
        self.NUM_STRINGS = constants["num_strings"] # number of load strings
        self.NUM_BOARDS = self.NUM_STRINGS*2 # number of installed load boards

        self.create_relay_tables() # create useful relay tables  
        self.relay_open = [False] * (self.NUM_RELAYS*self.NUM_BOARDS+1)  # create list[relay #] = Open boolean
        
        self.modbus = self.connect_modbus() # open modbus get object
        self.relayboards = self.connect_R421B16() # open relay board and get dict[id] = object

        self.reset_relays()



    def create_relay_tables(self):
        """
            Creates:
                1. self.relay_library[cell_number]=[relays to scan cell]
                2. self.string_library[cell_number]=[relays to add/remove string]
                3. self.dev_library[cell_number]=[relays to add/remove cell]
        """
        
        # ---------------------------------- RELAY CONFIGURATION # 1 ---------------------------------------
        # Utilizes 2nd relay to pull string off load (leaving open circut) while scanning cells indivisually
        # --------------------------------------------------------------------------------------------------
        
        # # create library of string relays, ignore # per board
        # self.string_library = {}
        # index = 1
        # index += self.NUM_WIRES
        # string_no = 0
        # for idx in range(self.NUM_STRINGS):
        #     string_no += 1
        #     temp = []
        #     for idx2 in range(int(self.NUM_DEVS/2)):
        #         for idx3 in range(self.NUM_WIRES*2):
        #             temp.append(index)
        #             index += 1
        #         index += self.NUM_WIRES*2
        #     self.string_library[string_no]= temp
        
        # # create library of cell relays, ignore # per board
        # self.dev_library = {}
        # index = 1
        # dev_no = 0
        # for idx in range(self.NUM_STRINGS):
        #     for idx2 in range(self.NUM_DEVS):
        #         dev_no += 1
        #         temp = []
        #         for idx3 in range(self.NUM_WIRES): # appends 4x
        #             temp.append(index)
        #             index +=1
        #         if idx2 % 2 == 0: # acts every other so groups by 8
        #             index += self.NUM_WIRES*2
        #         else:
        #             index += 0
        #         self.dev_library[dev_no]=temp
        
        # # combine the two so we have a list of relays needed for each cell
        # self.relay_library = {}
        # for dev_num in range(self.NUM_STRINGS*self.NUM_DEVS):
        #     temp1 = self.string_library[(dev_num//self.NUM_DEVS)+1]
        #     temp2 = self.dev_library[dev_num+1]
        #     self.relay_library[dev_num+1] = temp1+temp2

            
        # ---------------------------------- RELAY CONFIGURATION # 2 ---------------------------------------
        # Turns off 2nd relay that pull strings off load (leaving open circut) while scanning cells indivisually
        # This means that cells not being JV scanned will have the same load applied when not scanned 
        # --------------------------------------------------------------------------------------------------
        
        self.relay_library = {}
        index = 1
        dev_no = 0
        for idx in range(self.NUM_STRINGS):
            for idx2 in range(int(self.NUM_DEVS)):
                dev_no += 1
                temp = []
                for idx3 in range(self.NUM_WIRES*2):
                    temp.append(index)
                    index += 1
                self.relay_library[dev_no]= temp
        
        # ---------------------------------- RELAY CONFIGURATION # 3 ---------------------------------------
        # Eliminates 2nd relay that pull strings off load (leaving open circut) while scanning cells indivisually
        # This means that cells not being JV scanned will have the same load applied when not scanned 
        # --------------------------------------------------------------------------------------------------
        
        # self.relay_library = {}
        # index = 1
        # dev_no = 0
        # for idx in range(self.NUM_STRINGS):
        #     for idx2 in range(int(self.NUM_DEVS)):
        #         dev_no += 1
        #         temp = []
        #         for idx3 in range(self.NUM_WIRES):
        #             temp.append(index)
        #             index += 1
        #         self.relay_library[dev_no]= temp
        


    def connect_modbus(self):
        """
            Connect to the modbus, return object
        """
        modbus = Modbus(serial_port=self.SERIAL_PORT, verbose=False)
        modbus.open()
        
        return modbus


    def connect_R421B16(self):
        """
            Connect to the R421B16 relay boards, return dict[id#] = object
        """
        
        # Connect and create a dictionary[board #] = relay_obj
        relay_boards = {}
        for board_id in range(self.NUM_BOARDS):
            relay_boards[board_id+1] =  R421B16(modbus_obj = self.modbus, address = (board_id+1))
        return relay_boards


    def relay_to_boardspecifics(self,id):
        """
            Converts from generic number to describe relay to relay board and specific relay number
        """
        relayboard_no = (id // self.NUM_RELAYS) + 1 # relayboard 1 to number of relayboards
        relay_no = id % self.NUM_RELAYS # relay number cycles to max number and back up again, starts at 1
        
        # handle that relays will start at 1 and go to 16, boards start at 1 as well
        if relay_no == 0:
            relay_no += 16
            relayboard_no -= 1
        board = self.relayboards[relayboard_no]
        
        return board, relay_no
    
    @relay_lock
    def _open(self,relay):
        """Workhorse function to open relays based on internal id"""
        if self.relay_open[relay] == False: # check if closed 
            board, relay_no = self.relay_to_boardspecifics(relay) # grab board and relay number
            board.on(relay_no) # turn on 
            self.relay_open[relay] = True
            # time.sleep(self.DELAY)

    @relay_lock
    def _close(self,relay):
        """Workhorse function to close relays based on internal id"""
        if self.relay_open[relay] == True: # check if open 
            board, relay_no = self.relay_to_boardspecifics(relay) # grab board and relay number
            board.off(relay_no) # turn off
            self.relay_open[relay] = False
            # time.sleep(self.DELAY)
    
    @relay_lock
    def _hard_close(self,relay):
        """Workhorse function to close relays based on internal id"""
        board, relay_no = self.relay_to_boardspecifics(relay) # grab board and relay number
        board.off(relay_no) # turn off
        self.relay_open[relay] = False
        # time.sleep(self.DELAY)

    
    def on(self,cell_no):
        """Open the neccisary ports to scan specified cell"""
        for relay in self.relay_library[cell_no]:
            self._open(relay)

    def off(self,cell_no):
        """Close the neccisary ports to return the specified cell to its load"""
        for relay in self.relay_library[cell_no]:
            self._close(relay)

    def all_on(self):
        """Open all relays"""
        for relay in range(1,len(self.relay_open)):
            self._open(relay)

    def all_off(self):
        """Close all relays"""
        for relay in range(1,len(self.relay_open)):
            self._close(relay)

    def open_string(self,string_no):
        """Opens relays for given string"""
        for relay in self.string_library[string_no]:
            self._open(relay)

    def close_string(self,string_no):
        """Closes relays for given string"""
        for relay in self.string_library[string_no]:
            self._close(relay)

    def open_cell(self,string_no):
        """Opens relays for given cell"""
        for relay in self.dev_library[string_no]:
            self._open(relay)

    def close_cell(self,string_no):
        """Closes relays for given cell"""
        for relay in self.dev_library[string_no]:
            self._close(relay)
    
    def reset_relays(self):
        """Closes all relays regarldess of status -- useful for reset"""
        for relay in range(1,len(self.relay_open)):
            self._hard_close(relay)