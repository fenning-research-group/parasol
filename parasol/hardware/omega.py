import serial
# from matplotlib.pyplot import hot
from threading import Lock


from parasol.configuration.configuration import Configuration
config = Configuration()
constants = config.get_config()['hotplate']



class Omega:
    """Omega class for PARASOL"""
    
    def __init__(self, id):
        """Initliazes the Omega class for Omega"""
        
        self.id = id
        self.hpconstants = constants[f'hp{id}']
        
        # get constants from hardwareconstants
        self.port = constants['port'] #get_port(constants["device_identifiers"])
        self.address = constants['address']  # this is 1 despite the hotplate ID!
        
        # create lock
        self.lock = Lock()
        
        # connect
        self.connect()

    # some properties below --> these may not be needed

    @property
    def setpoint(self):
        """Setpoint property
        
        Returns:
            float: setpoint in C
        """
        self.__setpoint = self.get_setpoint()
        return self.__setpoint

    @setpoint.setter
    def setpoint(self, x):
        """Sets setpoint to input set point or previously set setpoint

        Args:
            x (float): setpoint
        """
        if self.set_setpoint(setpoint=x):
            self.__setpoint = x
        else:
            self.__setpoint = self.get_setpoint()
            print(
                "Error changing set point - set point is still {0} C".format(
                    self.__setpoint
                )
            )

    @property
    def temperature(self) -> float:
        """Temperature property
        
        Returns:
            float: temperature in C
        """
        return self.get_temperature()


    def query(self, payload):
        """Communicates with Omega PID

        Args:
            payload (byte): package to write

        Returns:
            str: response
        """
        with self.lock:
            self.__handle.write(payload)
            response = self.__handle.readline()
        return response


    def connect(self) -> bool:
        """Connects to the hotplates via modbus protocol

        Returns:
            bool: True if connected
        """
        self.__handle = serial.Serial()
        self.__handle.port = self.port
        self.__handle.timeout = 2
        self.__handle.parity = "E"
        self.__handle.bytesize = 7
        self.__handle.baudrate = 9600
        self.__handle.open()

        # configure communication bits
        self.__end = b"\r\n"  # end bit <etx>

        # read current setpoint
        # self.__setpoint = self.__setpoint_get()
        # self.__setpoint = None

        return True


    def disconnect(self) -> bool:
        """Disconnect from the hotplates via modbus protocol

        Returns:
            bool: True if connected
        """
        
        self.__handle.close()
        return True


    def get_temperature(self) -> float:
        """Gets current hotplate temperature

        Returns:
            float: temperature in C
        """
        
        numWords = 1

        payload = self.__build_payload(
            address=self.address, command=3, dataAddress=1000, content=numWords
        )
        response = self.query(payload)

        data = int(response[7:-4], 16) * 0.1  # response given in 0.1 C

        return round(data, 2)


    def get_setpoint(self) -> float:
        """Gets current hotplate setpoint

        Returns:
            float: temperature in C
        """
        
        numWords = 1

        payload = self.__build_payload(
            address=self.address, command=3, dataAddress=1001, content=numWords
        )
        response = self.query(payload)
        print(response)

        data = int(response[7:-4], 16) * 0.1  # response given in 0.1 C

        return data


    def set_setpoint(self, setpoint) -> bool:
        """Sets current hotplate setpoint
        
        Args:
            setpoint (float): temperature in C

        Returns:
            bool: True if setpoint is current temperature
        """
        
        setpoint = round(setpoint * 10)  # need to give integer values of 0.1 C

        payload = self.__build_payload(
            address=self.address, command=6, dataAddress=1001, content=setpoint
        )
        response = self.query(payload)

        if response == payload:
            print(response, payload)
            return True
        else:
            print(response, payload)
            return False



    ### helper methods
    def __numtohex(self, num) -> bytes:
        """Converts decimal to hecadecimal

        Args:
            num (float): number in decimal format

        Returns:
            bytes: hexidecimal oacket
        """
        # return codecs.encode(str.encode('{0:02d}'.format(num)), 'hex_codec')
        return "{0:02X}".format(num).encode()

    # builds
    def __build_payload(self, address: int, command: int , dataAddress: str, content):
        """Builds payload to send via 

        Args:
            address (int): PID address (1 to 32)
            command (int): command type 
            dataAddress (str): _description_
            content (_type_): _description_
        """
        def calculateChecksum(payload):
            numHexValues = int(len(payload) / 2)
            hexValues = [
                int(payload[2 * i : (2 * i) + 2], 16) for i in range(numHexValues)
            ]
            checksum_int = (
                256 - sum(hexValues) % 256
            )  # drop the 0x convention at front, we only want the last two characters
            checksum = "{0:02X}".format(checksum_int)

            return str.upper(checksum).encode()

        payload = self.__numtohex(address)
        payload = payload + self.__numtohex(command)
        payload = payload + str.encode(str(dataAddress))
        payload = payload + "{0:04X}".format(content).encode()

        # calculate checksum from current payload
        chksum = calculateChecksum(payload)

        # complete the payload
        payload = payload + chksum
        payload = payload + self.__end
        payload = (
            b":" + payload
        )  # should start with ":", just held til the end to not interfere with checksum calculation

        return payload
    
    
    # def autotune(self, setpoint: float, pid_channel: int):
    #     self.set_setpoint(setpoint)

    #     # set PID channel

    #     # turn on autotuning
    #     payload = self.__build_payload(
    #         address=self.address, command=5, dataAddress="0813", content=0xFF00
    #     )
    #     response = self.query(payload)

    #     if response == payload:
    #         return True
    #     else:
    #         return False

    # def _autotune_in_progress(self):
    #     payload = self.__build_payload(
    #         address=self.address, command=2, dataAddress="0813", content=1
    #     )
    #     response = self.query(payload)
    #     if response.decode().strip()[-3] == "1":
    #         return True
    #     else:
    #         return False

    # def _set_PIDchannel(self, pid_channel: int):
    #     if pid_channel not in [0, 1, 2, 3, 4]:
    #         raise ValueError("Only 0, 1, 2, 3, and 4 (auto) are valid PID channels!")

    #     payload = self.__build_payload(
    #         address=self.address, command=6, dataAddress="101C", content=pid_channel
    #     )
    #     response = self.query(payload)

    #     if response == payload:
    #         return True
    #     else:
    #         return False


# class HotPlate(Workspace):
#     def __init__(
#         self,
#         name,
#         version,
#         gantry: Gantry = None,
#         gripper: Gripper = None,
#         id: int = None,
#         p0=[None, None, None],
#     ):
#         constants, workspace_kwargs = self._load_version(version)
#         super().__init__(
#             name=name,
#             gantry=gantry,
#             gripper=gripper,
#             p0=p0,
#             **workspace_kwargs,
#         )
#         if id is not None:
#             self.controller = Omega(id=id)
#             self.controller._set_PIDchannel(
#                 4
#             )  # auto select PID settings based on setpoint

#         xmean = np.mean([p[0] for p in self._coordinates.values()])
#         ymean = np.mean([p[1] for p in self._coordinates.values()])
#         self._centerproximity = {
#             slot: np.linalg.norm([p[0] - xmean, p[1] - ymean])
#             for slot, p in self._coordinates.items()
#         }

#         # self.TLIM = (constants["temperature_min"], constants["temperature_max"])
#         # only consider slots with blanks loaded
#         self.slots = {
#             slotname: {"coordinates": coord, "payload": None}
#             for slotname, coord in self._coordinates.items()
#         }
#         self.emptyslots = list(self.slots.keys())
#         self.filledslots = []
#         self._capacity = len(self.slots)
#         self.full = False

#         xmean = np.mean([p[0] for p in self._coordinates.values()])
#         ymean = np.mean([p[1] for p in self._coordinates.values()])
#         self._centerproximity = {
#             slot: np.linalg.norm([p[0] - xmean, p[1] - ymean])
#             for slot, p in self._coordinates.items()
#         }

#     def get_open_slot(self):
#         if len(self.emptyslots) == 0:
#             raise ValueError("No empty slots!")

#         centerproximity = [self._centerproximity[slot] for slot in self.emptyslots]
#         closest_slot_to_center = [
#             slot for _, slot in sorted(zip(centerproximity, self.emptyslots))
#         ][0]
#         return closest_slot_to_center

#     def load(self, slot, sample):
#         if slot not in self.slots:
#             raise ValueError(f"{slot} is an invalid slot!")
#         elif slot in self.filledslots:
#             raise ValueError(f"{slot} is already filled!")
#         else:
#             self.slots[slot]["payload"] = sample
#             self.emptyslots.remove(slot)
#             self.filledslots.append(slot)

#     def unload(self, slot=None, sample=None):
#         if sample is not None:
#             found_sample = False
#             for k, v in self.slots.items():
#                 if v["payload"] == sample:
#                     found_sample = True
#                     slot = k
#             if not found_sample:
#                 raise ValueError(
#                     f"Sample {sample.name} is not currently on the hotplate!"
#                 )
#         else:
#             if slot is None:
#                 raise ValueError("No slot defined?")
#             if slot not in self.slots:
#                 raise ValueError(f"{slot} is an invalid slot!")
#             elif slot in self.emptyslots:
#                 raise ValueError(f"{slot} is already empty!")

#         self.slots[slot]["payload"] = None
#         self.filledslots.remove(slot)
#         self.emptyslots.append(slot)
#         return sample

#     def _load_version(self, version):
#         if version not in AVAILABLE_VERSIONS:
#             raise Exception(
#                 f'Invalid tray version "{version}".\n Available versions are: {list(AVAILABLE_VERSIONS.keys())}.'
#             )
#         with open(AVAILABLE_VERSIONS[version], "r") as f:
#             constants = yaml.load(f, Loader=yaml.FullLoader)
#         workspace_kwargs = {
#             "pitch": (constants["xpitch"], constants["ypitch"]),
#             "gridsize": (constants["numx"], constants["numy"]),
#             "z_clearance": constants["z_clearance"],
#         }
#         if "testslots" in constants:  # override 4 corner default
#             workspace_kwargs["testslots"] = constants["testslots"]
#         return constants, workspace_kwargs

#     def export(self, fpath):
#         """
#         routine to export tray data to save file. used to keep track of experimental conditions in certain tray.
#         """
#         return None
