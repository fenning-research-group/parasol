import u6
import time
import math
import yaml
import os
import numpy as np

# Set module directory, import constants from yaml file
MODULE_DIR = os.path.dirname(__file__)
with open(os.path.join(MODULE_DIR, "..", "hardwareconstants.yaml"), "r") as f:
    constants = yaml.safe_load(f)["labjack"]


class ExtendedList(list):
    def __init__(self):
        list.__init__(self)
        self.extended = None


class LabJack:
    """General LabJack U6-PRO class for monitoring environmental data"""

    def __init__(self) -> None:
        """Initialize the labjack package for monitoring"""

        # Setup u6 amd calibration data
        self.d = u6.U6() #
        self.d.getCalibrationData() #

        # AIN ports for measurements
        self.tc_port = constants["thermocouple1_port"]
        self.pd_port = constants["photodiode_port"]
        self.hg_port = constants["hygrometer_port"]
        self.ground_port = constants["ground_port"]

        # Set # to average in measurement, and delay between readings
        self.avgnum = constants["average_num"]
        self.delay = constants["delay_time"]

        # Setup nested functions for analysis
        self.tc = self.Thermocouple()
        self.rtd = self.RTD()
        self.pd = self.Photodiode()
        self.hm = self.Hygrometer()


    # Base functions

    def read_AIN(self, idx: int, resolutionindex: int = 13, gainindex: int = 0) -> float:
        """Reads the analog input channel

        Args:
            idx (int): anolog input channel index
            resolutionindex (int): resolution index for labjack
            gainindex (int): gain index for labjack
            
            idx: 14 is the internal temperature sensor and 15 is internal GND.
            ResolutionIndex: 0=default, 1-8 for high-speed ADC, 9-13 for high-res ADC on U6-Pro. Value in the response is the actual resolution setting used for the reading. 
            GainIndex: 0=x1, 1=x10, 2=x100, 3=x1000, 15=autorange. Value in the response is the actual gain setting used for the reading

        Returns:
            float: value read
        """

        return self.d.getAIN(idx, resolutionindex, gainindex)

    def read_CJT(self) -> float:
        """Reads the cold junction temperature (internal temperature sensor)

        Returns:
            float: value read
        """

        # read, add 2.5 C as screw clams generally ~2.5 C higher than ambient, convert to C
        cjt_offset = self.tc.get_cjt_offset()

        return self.d.getTemperature() + cjt_offset - 273.15

    def set_DAC(self, idx: int, v: float) -> None:
        """Sets the analogue out voltage of the labjack

        Args:
            idx (int): port index
            v (float): voltage to set
        """

        DAC_REGISTER = 5000 + idx * 1
        self.d.writeRegister(DAC_REGISTER, v)

    # Monitor Env and supporting Functions

    def monitor_env(self) -> float:
        """Monitors the environment and returns the temperature, relative humidity, and intensity"""

        temp = self.get_temp_rtd()
        rh = self.get_rh(temp)
        intensity = self.get_intensity(temp)

        return temp, rh, intensity


    def get_temp_rtd(self)-> float:
        """Measures the temperature using the labjack and PT1000 RTD

        Returns:
            float: temperature of thermocouple in degrees C
        """
        
        # Get calibrated current output in amps
        RTD_A = self.d.calInfo.currentOutput1 

        # average over n readings
        temp = 0
        for i in range(self.avgnum):
            
            # Read voltage before RTD
            RTD_V = self.read_AIN(idx = self.tc_port) - self.read_AIN(idx = self.ground_port)
            
            # Caluclate resistance via Ohms law
            RTD_Ohm = RTD_V/RTD_A
            
            # Convert to temp
            RTD_T = self.rtd.ohmToTempC(RTD_Ohm)
            
            # Iterate
            temp += RTD_T
            time.sleep(self.delay)
            
        temp /= self.avgnum 
        return temp


    def get_temp_tc(self) -> float:
        """Measures the temperature using the labjack and type K thermocouple.

        Returns:
            float: temperature of thermocouple in degrees C
        """

        # average over n readings
        temp = 0
        for i in range(self.avgnum):

            # Read cold junction temperature (C)
            CJTEMPinC = self.read_CJT()

            # Read thermocouple's analog voltage (mV)
            TCmVolts = self.read_AIN(idx=self.tc_port, gainindex=1) - self.read_AIN(idx=self.ground_port, gainindex=1)
            TCmVolts *= 1000
            
            # Get total mV, convert to C
            totalMVolts = TCmVolts + self.tc.tempCToMVolts(CJTEMPinC)
            
            # Iterate
            temp += self.tc.mVoltsToTempC(totalMVolts)
            time.sleep(self.delay)

        temp /= self.avgnum
        return temp

    def get_intensity(self, temp: float) -> float:
        """Measures the intensity of the photodiode using the labjack and Hamamatsu S1133-01 detector

        Arg:
            temp (float): temperature of thermocouple in degrees C

        Returns:
            float: intensity of the photodiode in # suns

        """

        # average over n readings
        intensity = 0
        for i in range(self.avgnum):

            # Read  analog voltage (mV)
            PDmVolts = self.read_AIN(idx=self.pd_port, gainindex = 1) - self.read_AIN(idx=self.ground_port, gainindex=1)
            PDmVolts *= 1000
            
            # V drop is across resistor due to current, calc using Ohms Law
            PDmAmps = self.pd.mVoltsTomAmps(PDmVolts)
            
            # Compare mA to expected 1 sun illumination (as function of T) to convert to # of suns
            PDsuns = self.pd.mAmpsToSuns(PDmAmps, temp)
            
            # Iterate
            intensity += PDsuns
            time.sleep(self.delay)

        intensity /= self.avgnum
        return intensity

    def get_rh(self, temp: float) -> float:
        """Measures the RH of the hygrometer using the labjack and Honeywell HIH-4000

        Arg:
            temp (float): temperature of thermocouple in degrees C

        Returns:
            float: RH in %

        """

        # Get applied voltage
        vapplied = 4.75 #estimate at end of cable. self.hm.get_hg_vapplied()  # 5V 

        # iterate over n readinds
        rh = 0
        for i in range(self.avgnum):

            # Read hygrometers analogue voltage (mv)
            HMVolts = self.read_AIN(idx=self.hg_port) - self.read_AIN(idx=self.ground_port)

            # Convert input and output voltages to relative humidity
            HM_RHs = self.hm.VoltsToRHs(HMVolts, vapplied)

            # Convert sensor RH to real RH
            HM_RHr = self.hm.RHsToRHr(HM_RHs, temp)

            # Iterate
            rh += HM_RHr
            time.sleep(self.delay)

        rh /= self.avgnum
        return rh

    # Nested Functions for each monitoring task

    class Hygrometer:
        """
        General Hygrometer nested class for reading the Honeywell HIH-4000 series in RH
        Functions by applying a source voltage to the hygrometer and reading its output voltage
        Hygrometer should have + to Vs (5V), output to AIN#, and ground to ground. Connect ground and out by 1Mohm resistor. Max output for V in 5V is 3.26V.
        Specs: https://sps.honeywell.com/us/en/products/advanced-sensing-technologies/healthcare-sensing/humidity-with-temperature-sensors/hih-4000-series
        """

        def __init__(self) -> None:
            """Initializes the hygrometer class and neccisary constants"""

            # grab constants
            self.vmult = 0.030 # RH/V, provided for each sensor
            self.voffset = 0.804 # V, provided for each sensor
            self.rhmult = 0.00216 # provided for HIH series
            self.rhoffset = 1.0546 # provided for HIH series
            self.vapplied = 4.75 #5  # Voltage applied by DAC port

        def get_hg_vapplied(self) -> float:
            """Returns ideal applied voltage to run the hygrometer"""

            return self.vapplied

        def VoltsToRHs(self, v_meas: float, v_app: float) -> float:
            """Converts the voltage reading to RH sensor using the coefficients

            Args:
                v_meas (float): voltage reading in mV
                v_app (float): voltage applied in mV

            Returns:
                float: relative humidity in RH
            """

            # Voltage to RH equation given for each calibrated sensor
            return (v_meas - self.voffset) / self.vmult

        def RHsToRHr(self, RH_meas: float, temp: float) -> float:
            """Concerts RH sensor reading to real RH reading (temp correction)

            Args:
                RH_meas (float): RH sensor reading in %
                temp (float): temperature in degrees C

            Returns:
                float: real relative humidity in %
            """

            # Temp correction given in Installation Instructions manual
            # https://sps.honeywell.com/us/en/products/advanced-sensing-technologies/healthcare-sensing/humidity-with-temperature-sensors/hih-4000-series
            return (RH_meas) / (self.rhoffset - self.rhmult * temp)

    class Photodiode:
        """
        General photodiode nested class for reading the Hamamatsu S1133-01 photodiode in suns
        Functions by dropping the current of the photodiode across a resistor and measuring voltage loss
        Photodioide should have + to ground, - to resitor to AIN#.
        Resistor = (max V sense / Isc) / gain = (10.1 V)/(5.4E-6 A) / 1 = 1870 kOhm @ gain 1 or  187 kOhm @ gain 10
        Specs: https://www.hamamatsu.com/us/en/product/optical-sensors/photodiodes/si-photodiodes/S1133-01.html
        """

        def __init__(self) -> None:
            """Initializes the Photodiode class and neccisary constants"""

            # grab constants
            self.resistor = 1500  # ohms, resistor on board
            self.onesun_isc = 0.672 # mA, measure under solar simulator
            self.tempmult = 0.1  # %/C off 25 C, +C inc Isc
            self.tempoffset = 25  # C

        def mVoltsTomAmps(self, volts: float) -> float:
            """Converts the voltage reading to mA using Ohms Law

            Args:
                volts (float): voltage reading in mV

            Returns:
                float: illumination intensity in mA
            """
            # V = I*R --> I = V/R
            return volts / self.resistor

        def mAmpsToSuns(self, amps: float, temp: float) -> float:
            """Converts mA reading to # suns using the photodiode's Isc and temp coef

            Args:
                amps (float): sun count
                temp (float): temperature in degrees C

            Returns:
                float: illumination intensity in # suns
            """

            # adjust 1 sun for temperature
            temp_adj = (
                self.onesun_isc * (temp - self.tempoffset) * (self.tempmult / 100)
            )
            adj_1sun = self.onesun_isc + temp_adj

            # get # suns using : #suns = mA / (mA/sun)
            numsuns = amps / adj_1sun

            return numsuns

    class Thermocouple:
        """
        General thermocouple nested class for reading the K-type thermocouple in C
        Thermocouiple should have - to ground, + to AIN#
        Tables: https://srdata.nist.gov/its90/type_k/kcoefficients.html
        """

        def __init__(self) -> None:
            """Initializes the thermocouple class and neccisary constants"""

            # grab constants
            self.create_temp_to_volts_coefs()
            self.create_volts_to_temp_coefs()

            self.cjt_offset = 2.5  # C

        def get_cjt_offset(self) -> float:
            """Returns the ideal offset between the internal temp sensor and the extenrnal connection in C"""

            return self.cjt_offset

        def create_volts_to_temp_coefs(self) -> None:
            """
            Calculates the coefficients for the voltage to temperature conversion -- specific type k thermocouple
            These are the K inverse coefficients
            """

            # -200 C to 0 C and -5.891 mV to 0 mV
            self.voltsToTemp1 = (
                0.0e0,
                2.5173462e1,
                -1.1662878e0,
                -1.0833638e0,
                -8.977354e-1,
                -3.7342377e-1,
                -8.6632643e-2,
                -1.0450598e-2,
                -5.1920577e-4,
            )

            # 0 C to 500 C and 0 mV to 20.644 mV
            self.voltsToTemp2 = (
                0.0e0,
                2.508355e1,
                7.860106e-2,
                -2.503131e-1,
                8.31527e-2,
                -1.228034e-2,
                9.804036e-4,
                -4.41303e-5,
                1.057734e-6,
                -1.052755e-8,
            )

            # 500 C to 1372 C and 20.644 mV to 54.886 mV
            self.voltsToTemp3 = (
                -1.318058e2,
                4.830222e1,
                -1.646031e0,
                5.464731e-2,
                -9.650715e-4,
                8.802193e-6,
                -3.11081e-8,
            )

        def create_temp_to_volts_coefs(self) -> None:
            """
            Calculates the coefficients for the temperature to voltage conversion -- specific to internal thermocouple
            These are the K coefficients
            """

            # -270 C to 0 C
            self.tempToVolts1 = (
                0.0e0,
                0.39450128e-1,
                0.236223736e-4,
                -0.328589068e-6,
                -0.499048288e-8,
                -0.675090592e-10,
                -0.574103274e-12,
                -0.310888729e-14,
                -0.104516094e-16,
                -0.198892669e-19,
                -0.163226975e-22,
            )

            # 0 C to 1372 C + regular and extended correction (put 0 C in correct form)
            self.tempToVolts2 = ExtendedList()
            self.tempToVolts2.append(-0.176004137e-1)
            self.tempToVolts2.append(0.38921205e-1)
            self.tempToVolts2.append(0.1855877e-4)
            self.tempToVolts2.append(-0.994575929e-7)
            self.tempToVolts2.append(0.318409457e-9)
            self.tempToVolts2.append(-0.560728449e-12)
            self.tempToVolts2.append(0.560750591e-15)
            self.tempToVolts2.append(-0.3202072e-18)
            self.tempToVolts2.append(0.971511472e-22)
            self.tempToVolts2.append(-0.121047213e-25)
            self.tempToVolts2.extended = (0.1185976e0, -0.1183432e-3, 0.1269686e3)

        def voltsToTempConstants(self, mVolts: float) -> float:
            """Returns the constants for the voltage to temperature conversion

            Args:
                mVolts (float): The voltage in mV

            Returns:
                list(float): The constants for the conversion
            """

            # Return coefficients for correct range
            if mVolts < -5.891 or mVolts > 54.886:
                raise Exception("Invalid range")
            if mVolts < 0:
                return self.voltsToTemp1
            elif mVolts < 20.644:
                return self.voltsToTemp2
            else:
                return self.voltsToTemp3

        def tempToVoltsConstants(self, tempC: float) -> float:
            """Returns the constants for the temperature to voltage conversion

            Args:
                tempC (float): The temperature in C

            Returns:
                list(float): The constants for the conversion
            """

            # Return coefficients for correct range
            if tempC < -270 or tempC > 1372:
                raise Exception("Invalid range")
            if tempC < 0:
                return self.tempToVolts1
            else:
                return self.tempToVolts2

        def evaluatePolynomial(self, coeffs: list, x: float) -> float:
            """uses polynomial expansion to calculate the value of a polynomial at a given point

            Args:
                coeffs (list[float]): coefficients of the polynomial
                x (float): location to evaluate the function

            Returns:
                float: calculated y value for given x and coefficients
            """

            # for each coefficient, add (x^i * ci) to the sum
            tot = 0
            y = 1
            for a in coeffs:
                tot += y * a
                y *= x
            return tot

        def tempCToMVolts(self, tempC: float) -> float:
            """Converts a temperature in C to voltage in mV

            Args:
                tempC (float): temperature in C

            Returns:
                float: voltage in mV
            """

            # get correct coefficients for temperature range
            coeffs = self.tempToVoltsConstants(tempC)

            # if from range 0 < tempC < 1372 C, calculate voltage regular + extended correction
            if hasattr(coeffs, "extended"):
                a0, a1, a2 = coeffs.extended
                extendedCalc = a0 * math.exp(a1 * (tempC - a2) * (tempC - a2))
                return self.evaluatePolynomial(coeffs, tempC) + extendedCalc
            # else, calculate voltage regular
            else:
                return self.evaluatePolynomial(coeffs, tempC)

        def mVoltsToTempC(self, mVolts: float) -> float:
            """Converts a voltage in mV to temperature in C

            Args:
                mVolts (float): voltage in mV

            Returns:
                float: temperature in C
            """
            # get correct coefficients for voltage range
            coeffs = self.voltsToTempConstants(mVolts)
            # calculate temp regular
            return self.evaluatePolynomial(coeffs, mVolts)
        
    
    
    class RTD:
        """
        General thermocouple nested class for reading the K-type thermocouple in C
        Thermocouiple should have - to ground, + to AIN#
        Tables: https://srdata.nist.gov/its90/type_k/kcoefficients.html
        """

        def __init__(self) -> None:
            """Initializes the thermocouple class and neccisary constants"""
            
            self.make_coefs()
        
        
        def make_coefs(self):
            
            self.temps = np.linspace(-50,110,33)
            self.ohms = [803.1, 822.9, 842.7, 862.5, 882.2, 901.9, 921.6, 941.2, 960.9, 980.4, 1000, 1019.5, 1039, 1058.5, 
                1077.9, 1097.3, 1116.7, 1136.1, 1155.4, 1174.7, 1194, 1213.2, 1232.4, 1251.6, 1270.7, 1289.8, 1308.9, 1328,
                1347, 1366, 1385, 1403.9, 1422.9]
            
        
        def ohmToTempC(self,ohm) ->float:
            
            return np.interp(ohm, self.ohms, self.temps)
            


