# Import
import yaml
import os
import numpy as np

from serial.tools import list_ports
import serial
import time


# Set yaml name, load yokogawa info
MODULE_DIR = os.path.dirname(__file__)
with open(os.path.join(MODULE_DIR, "..", "hardwareconstants.yaml"), "r") as f:
    constants = yaml.load(f, Loader=yaml.FullLoader)["easttester"]


# used for MPP tracking
class EastTester:

    # initialize and set bounds for measurement (see srcV_measI for bounds)
    def __init__(self):
        self.connect()
        self.et_delay = constants["et_delay"]
        self.et_v_min = constants["et_v_min"]
        self.et_v_max = constants["et_v_max"]
        self.et_i_max = constants["et_i_max"]
        self.et_avg_num = constants5["et_avg_num"]
        self.et_voltage_step = constants["et_voltage_step"]


    # connect
    def connect(self):

        # connect using serial, use highest transferrate and shortest timeout
        s = serial.Serial('COM5', baudrate = 115200, timeout = 0.005) # generally 1 or 5


    # setup source voltage and measure I
    def srcV_measI(self, channel):

        # set to external operation, constant voltage, and continuous operation
        s.write(("LOAD:TRIGger EXT").encode())
        time.sleep(self.et_delay)
        s.write(("CH"+str(channel)+":MODE CV\n").encode())
        time.sleep(self.et_delay)
        s.write(("TRAN"+str(channel)+":MODE COUT\n").encode())
        time.sleep(self.et_delay)
        
        # set ranges for voltage, as well as max and min
        # "NAME" : RANGE (MAX/SHUTOFF)
        # "LOW": 0.1 -> 19.999 (21.000)
        # "HIGH": 0.1 -> 150.000 (155.000)
        s.write(("LOAD:VRAN LOW").encode())
        time.sleep(self.et_delay)
        s.write(("VOLT"+str(channel)+":VMIN %f\n" % (self.et_v_min)).encode())
        time.sleep(self.et_delay)
        s.write(("VOLT"+str(channel)+":VMAX %f\n" % (self.et_v_max)).encode())
        time.sleep(self.et_delay)
        

        # set range for current, as well as max current (no min feature)
        # "NAME" : RANGE (MAX/SHUTOFF)
        # "LOW": 0 -> 3.000 (3.3)
        # "HIGH": 0 -> 20.000 (22.0)
        s.write(("LOAD:CRAN LOW").encode())
        time.sleep(self.et_delay)
        s.write(("CURR"+str(channel)+":IMAX %f\n" % (self.et_i_max)).encode())
        time.sleep(self.et_delay)


        # set max power output
        # "NAME" : RANGE (MAX/SHUTOFF)
        # ALL: 0 --> 200 (220)
        s.write(("POWE"+str(channel)+":PMAX %f\n" % (self.et_v_max*self.et_i_max)).encode())
        time.sleep(self.et_delay)


        # close channel
        s.write(("CH"+str(channel)+":SW OFF\n").encode())
        time.sleep(self.et_delay)


    # turns on output
    def output_on(self,channel):
        s.write(("CH"+str(channel)+":SW ON\n").encode())
        time.sleep(self.et_delay)


    # turns off output
    def output_off(self,channel):
        s.write(("CH"+str(channel)+":SW OFF\n").encode())
        time.sleep(self.et_delay)


    # set voltage
    def set_voltage(self, channel, voltage):
        s.write(("VOLT"+str(channel)+":CV %f\n" % (voltage)).encode())
        time.sleep(self.et_delay)


    # measure current several times and average
    def measure_current(self,channel):

        # read current iterations # of times and average
        i = 0
        curr_tot = 0

        while i < self.et_avg_num:

            s.write(("MEAS"+str(channel)+":CURR?\n").encode())
            time.sleep(self.et_delay)
        
            curr = s.readlines()[-1]
            curr = curr.decode("utf-8") 
            curr = re.findall('\d*\.?\d+', curr)
            curr = float(curr[0])
            curr_tot += curr
            i += 1

        curr_tot /= self.et_avg_num

        return curr_tot


    # could add back in v min and v max so that it is array dependent. 
    # track MPP, return numpy arrays of t, v, i, p
    def track_mpp(self,channel,voltage)

         # use self.lock to ensure only 1 thread is talking to harware
        with self.lock:

            #change settings of tester
            self.srcV_measI()

            # create blank lists
            voltages = []
            currents = []
            powers = []
            time = []

            # turn on output
            self.output_on(channel)

            # set initial voltage, measure current, save to lists
            self.set_voltage(channel,voltage)
            current = self.measure_current(channel)
            voltages.append(voltage)
            currents.append(current)
            powers.append(voltage*current)
            time.append(time.time())

            # perturb voltage
            voltage_step = self.et_voltage_step
            voltage += voltage_step

            # scan until break
            tracking = True
            while tracking:
                
                # set v, measure i, save to lists
                self.set_voltage(channel,voltage)
                current = self.measure_current(channel)
                voltages.append(voltage)
                currents.append(current)
                powers.append(voltage*current)
                times.append(time.time())

                # determine if power increased or decreased, if the latter, change perturb direction
                if(powers[-2]>=powers[-1]):
                    voltage_step *= -1
        
                # move by step if within bounds, else move back towards
                if(voltage + voltage_step >= self.et_v_max):
                    voltage -= abs(voltage_step)
                elif(voltage + voltage_step <= self.et_v_min):
                    voltage += abs(voltage_step)
                else:
                    voltage += voltage_step

            # turn off output --> not sure this is needed/wanted. We want V to stay on but not neccsiary measurement
            self.output_off(channel)

            # return data as arrays
            v = np.asarray(voltages)
            i = np.asarray(currents)
            p = np.asarray(powers)
            t = np.asarray(times)

        return t, v, i, p



