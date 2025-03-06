import time

from parasol.hardware.labjack import LabJack

from parasol.hardware.omega import Omega
# from parasol.hardware.light import Light()
# from parasol.hardware.ambient import Ambient()

from parasol.configuration.configuration import Configuration
config = Configuration()
constants = config.get_config()['environmental']

class Environmental():
    """Class for controllinig environmental stressors"""
    
    def __init__(self, mode, monitor_stations):
        """Initializes Environmental class for control and monitoring.

        Args:
            mode (str): indoor or outdoor
            monitor_stations (list(int)): list of monitoring stations
                0 : reserved for common outdoor stations using labjack
                1+ : currently all treated as indoor stations
        """
        
        # indoor or outdoor
        self.mode = mode
        
        # create dictionaries to handle what monitors and what controls for each monitoring station
        self.temp_c ={}
        self.temp_m = {}
        self.rh_c = {}
        self.rh_m = {}
        self.int_c = {}
        self.int_m = {}

        # setup monitoring for monitor stations = 0 --> note here we have no env control and just use labjack
        # if 0 in monitor_stations:
        if mode == 'outdoor':
            labjack = LabJack()
            self.temp_m[0] = labjack
            self.rh_m[0] = labjack
            self.int_m[0] = labjack
        
        # setup monitoring for other monitoring stations -> note here we have env control coupled
        if mode == 'indoor':
            temp_lst = [value for value in monitor_stations if value > 0]
            for value in temp_lst:
                omega = Omega(value)
                self.temp_m[value] = omega
                self.temp_c[value] = omega
                # self.rh_c = {}
                # self.rh_m = {}
                # self.int_c = {}
                # self.int_m = {}
                

    
    def monitor_environment(self,  monitor_station: int) -> float:
        """Monitors the environment
        Args:
            monitor_station (int): index of station to utilize (allows multiple monitoring stations)
        Returns:
            float: time (epoch)
            float: temperature (C)
            float: humidity (%)
            flaot: intensity (# suns)
        """

        # Set all varaibles to None
        t, temp_dark, temp_light, rh, intensity = [time.time(), -1, -1, -1, -1]
        
        # handles labjack
        if self.mode == 'outdoor':
            if len(self.temp_m)>0:
                temp_dark = self.temp_m[monitor_station].get_temp_rtd(1)
                temp_light = self.temp_m[monitor_station].get_temp_rtd(2)
            if len(self.rh_m)>0:
                rh = self.rh_m[monitor_station].get_rh(temp_dark)
            if len(self.int_m)>0:
                intensity = self.int_m[monitor_station].get_intensity(temp_light)
        
        #TODO: will need to expand for new monitoring setup, use above diction with extra stuff from below
        # temp_dark = self.get_temp_rtd(1)
        # temp_light = self.get_temp_rtd(2)
        # rh = self.get_rh(temp_light)
        # intensity = self.get_intensity(temp_dark)
        
        # handles standard 
        if self.mode == 'indoor':
            if len(self.temp_m)>0:
                temp_light = self.temp_m[monitor_station].get_temperature()
            if len(self.rh_m)>0:
                rh = self.rh_m[monitor_station].get_rh(temp_light)
            if len(self.int_m)>0:
                intensity = self.int_m[monitor_station].get_intensity(temp_light)
            
        return t,  temp_dark, temp_light, rh, intensity


    def set_temperature(self, id: int, setpoint: float):
        """ Set temperature

        Args:
            id (int): string number
            setpoint (float): desired setpoint
        """
        if len(self.temp_c)>0:
            self.temp_c[id].set_setpoint(setpoint)
        else:
            print("Add code to control temperature in parasol.environmental")


    def set_rh(self, id: int, setpoint: float):
        """ Set relative humidity

        Args:
            id (int): string number
            setpoint (float): desired setpoint
        """
        if len(self.rh_c)>0:
            self.rh_c[id].set_setpoint(setpoint)
        else:
            print("Add code to control relatiuve humdity in parasol.environmental")


    def set_intensity(self, id: int, setpoint: float):
        """ Set light intensity

        Args:
            id (int): string number
            setpoint (float): desired setpoint
        """
        if len(self.int_c)>0:
            self.int_c[id].set_setpoint(setpoint)
        else:
            print("Add code to control light intensity in parasol.environmental")


    def temperature_off(self, id: int):
        """ Turn off temperature control

        Args:
            id (int): string number
        """
        if len(self.temp_c)>0:
            self.temp_c[id].set_setpoint(0)
        else:
            print("Add code to control temperature in parasol.environmental")


    def rh_off(self, id: int):
        """ Turn off relative humidity control

        Args:
            id (int): string number
        """
        if len(self.rh_c)>0:
            self.rh_c[id].set_setpoint(0)
        else:
            print("Add code to control relative humidity in parasol.environmental")


    def intensity_off(self, id: int):
        """ Turn off light intensity control

        Args:
            id (int): string number
        """
        if len(self.int_c)>0:
            self.int_c[id].set_setpoint(0)
        else:
            print("Add code to control relative humidity in parasol.environmental")