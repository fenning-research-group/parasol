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
class Easttester:

    # initialize
    def __init__(self):
        self.connect()
        self.delay = 0.3
        self.v_min = 0
        self.v_max = 1
        self.i_min = 0
        self.i_max = 10

    # connect
    def connect(self):
        s = serial.Serial('COM5', baudrate = 115200, timeout = 0.005)


    # setup source voltage and measure I
    def srcV_measI(self, channel):

        # set to external operation
        s.write(("LOAD:TRIGger EXT").encode())
        time.sleep(self.delay)
        
        # set ranges for voltage and current (either low or high)
        s.write(("LOAD:VRAN LOW").encode())
        time.sleep(self.delay)
        s.write(("LOAD:CRAN LOW").encode())
        time.sleep(self.delay)

        # set max/min V 
        s.write(("LOAD:VLOW %f\n" % (self.v_min)).encode())
        time.sleep(self.delay)
        s.write(("LOAD:VHIGH %f\n" % (self.v_max)).encode())
        time.sleep(self.delay)

        # set max/min A
        s.write(("LOAD:CLOW %f\n" % (self.i_min)).encode())
        time.sleep(self.delay)
        s.write(("LOAD:CHIGH %f\n" % (self.i_max)).encode())
        time.sleep(self.delay)

        # set max/min W
        s.write(("LOAD:PLOW %f\n" % (self.i_min*self.v_min)).encode())
        time.sleep(self.delay)
        s.write(("LOAD:PHIGH %f\n" % (self.i_min*self.v_max)).encode())
        time.sleep(self.delay)

        # set turnoff setpoints (1.1* high)
        s.write(("CH"+str(channel)+":MODE CV\n").encode())
        time.sleep(self.delay)
        s.write(("VOLT"+str(channel)+":VMAX %f\n" % (self.v_max*1.1)).encode())
        time.sleep(self.delay)
        s.write(("CURR"+str(channel)+":IMAX %f\n" % (self.i_max*1.1)).encode())
        time.sleep(self.delay)
        s.write(("POWE"+str(channel)+":PMAX %f\n" % (self.v_max*self.i_max*1.1)).encode())
        time.sleep(self.delay)

        # set mode to CV with continuous voltage (not pulse)
        s.write(("CH"+str(channel)+":MODE CV\n").encode())
        time.sleep(self.delay)
        s.write(("TRAN"+str(channel)+":MODE:COUT\n").encode())
        time.sleep(self.delay)

        # close channel
        s.write(("CH"+str(channel)+":SW OFF\n").encode())
        time.sleep(self.delay)


    # turns on output
    def output_on(self,channel):
        s.write(("CH"+str(channel)+":SW ON\n").encode())


    # turns off output
    def output_off(self,channel):
        s.write(("CH"+str(channel)+":SW OFF\n").encode())


    # set voltage
    def set_voltage(self, channel, voltage):
        s.write(("VOLT"+str(channel)+":CV %f\n" % (voltage)).encode())
        time.sleep(self.delay)


    # measure current & average a few
    def measure_current(self,channel,voltage,iterations):

        # set voltage
        s.write(("VOLT"+str(channel)+":CV %f\n" %(voltage)).encode())
        time.sleep(self.delay)

        # read current iterations # of times and average
        i = 0
        curr_tot = 0

        while i < iterations:

            s.write(("MEAS"+str(channel)+":CURR?\n").encode())
            time.sleep(self.delay)
        
            curr = s.readlines()[-1]
            curr = curr.decode("utf-8") 
            curr = re.findall('\d*\.?\d+', curr)
            curr = float(curr[0])
            curr_tot += curr
            i += 1

        curr_tot /= iterations

        return curr_tot


    # track MPP, return numpy arrays of t, v, i, p
    def track_mpp(self,channel,voltage,duration,voltage_step,averagenum)

        # create blank lists
        voltages = []
        currents = []
        powers = []
        time = []

        # turn on output
        self.output_on(channel)

        # set initial voltage, measure current, save to lists
        self.set_voltage(channel,voltage)
        current = self.measure_current(channel,voltage,averagenum)
        voltages.append(voltage)
        currents.append(current)
        powers.append(voltage*current)
        time.append(time.time())

        # perturb voltage
        voltage += voltage_step

        # get time
        startt = time.time()
        endt = time.time()

        # scan for duration
        while (endt-startt<duration):
            
            # set v, measure i, save to lists
            self.set_voltage(channel,voltage)
            current = self.measure_current(channel,voltage,averagenum)
            voltages.append(voltage)
            currents.append(current)
            powers.append(voltage*current)
            time.append(time.time())

            # determine if power increased or decreased, if the latter, change perturb direction
            if(powers[-2]>=powers[-1]):
                voltage_step *= -1
    
            # move by step if within bounds, else move back towards
            if(voltage >= self.v_max):
                voltage -= abs(voltage_step)
            elif(voltage <= self.v_min):
                voltage += abs(voltage_step)
            else:
                voltage += voltage_step

        # turn off output
        self.output_off(channel)

        # return data as arrays
        v = np.asarray(voltages)
        i = np.asarray(currents)
        p = np.asarray(powers)
        t = np.asarray(time)
        return t, v, i, p



