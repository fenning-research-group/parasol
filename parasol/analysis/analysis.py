import pandas as pd
import numpy as np
import os
import csv
from datetime import datetime
from csv import reader
import math

from parasol.filestructure import FileStructure

# Set module directory, import constants from yaml file
# MODULE_DIR = os.path.dirname(__file__)
# with open(os.path.join(MODULE_DIR, "..", "hardwareconstants.yaml"), "r") as f:
#     constants = yaml.safe_load(f)["analysis"]
    
from parasol.configuration.configuration import Configuration
config = Configuration()
constants = config.get_config()['analysis']


class Analysis:
    """Analysis package for PARASOL"""

    def __init__(self) -> None:
        """Initializes Analysis class"""

        # Load packages
        self.filestructure = FileStructure()

        # Load constants
        self.derivative_v_percent = constants["derivative_v_percent"]

    # Main analysis --> check_test runs from RUN_UI and analyze_from_savepath on string unload

    def check_test(self, jv_folders: list, mppfolderpaths: list) -> pd.DataFrame:
        """Calcualte FWD and REV Pmp versus time for given JV and MPP folder paths, returns dataframe with data

        Args:
            jvfolderpaths (list[str]): paths to the JV folders for the test
            mppfolderpaths (list[str]): paths to the MPP folders for the test

        Returns:
            pd.DataFrame: ["Time Elapsed (s)", "FWD Pmp (mW/cm2)", "REV Pmp (mW/cm2)"]
        """

        # Get JV & MPP file paths: create dictionary: dict[folderpath] = file_paths
        jv_dict = self.filestructure.map_test_files(jv_folders)

        # Calculate Pmpps, create dataframe and return to plot
        t_vals, pmp_fwd_vals, pmp_rev_vals = self.check_pmps(jv_folders, jv_dict)
        col_names = ["Time Elapsed (s)", "FWD Pmp (mW/cm2)", "REV Pmp (mW/cm2)"]
        data = list(zip(t_vals, pmp_fwd_vals, pmp_rev_vals))
        plot_df = pd.DataFrame(columns=col_names, data=data)        

        # return datafolder for plotting
        return plot_df

    def analyze_from_savepath(self, stringpath: str) -> list:
        """Analyze data for given test path, create output x<date>_<name>_<string>_<module>_Scalar_1.csv file in Analysis folder

        Args:
            stringpath (str): path to test folder

        Returns:
            list[str]: path to output file
        """

        # Get folder paths: create mpp_folder, jv_folders, and analyzed_folder (all lists)
        (
            mpp_folder,
            jv_folders,
            analyzed_folder,
            env_folders,
        ) = self.filestructure.get_test_subfolders(stringpath)

        if not os.path.exists(analyzed_folder[0]):
            os.mkdir(analyzed_folder[0])

        # Get JV, MPP, ENV file paths: create dictionary: dict[folderpath] = file_paths
        jv_dict = self.filestructure.map_test_files(jv_folders)
        mpp_dict = self.filestructure.map_test_files(mpp_folder)
        env_dict = self.filestructure.map_test_files(env_folders)

        # Analyze JV files: for each module export scalars_{module}.csv
        analyzed_waves = self.analyze_files(
            jv_folders, jv_dict, mpp_folder, mpp_dict, env_folders, env_dict, analyzed_folder[0],
        )

        return analyzed_waves

    # Workhorse functions for check_test

    def check_pmps(self, jv_folders: list, jv_dict: dict) -> list:
        """Loads the JV files, calculates and returns time, FWD Pmp, and REV Pmp

        Args:
            jv_folders (list[str]): list of jv folders
            jv_dict (dict): dictionary mapping jv folders to file paths

        Returns:
            list[np.array]: time values for each scan
            list[np.array]: forward pmp values for each scan
            list[np.array]: reverse pmp values for each scan
        """

        # Initialize empty lists to fill with numpy arrays
        t_vals = []
        pmp_fwd_vals = []
        pmp_rev_vals = []

        # Cycle through each folder/module
        for jv_folder in jv_folders:
            jv_file_paths = jv_dict[jv_folder]

            # Load JV files
            (
                all_t,
                all_v,
                all_vm_fwd,
                all_i_fwd,
                all_j_fwd,
                all_p_fwd,
                all_vm_rev,
                all_i_rev,
                all_j_rev,
                all_p_rev,
            ) = self.load_jv_files(jv_file_paths)

            # Make time data numpy array, calculate time elapsed
            all_t = np.array(all_t)
            all_t_elapsed = all_t - all_t[0]

            # Calculate Pmps for forward and reverse scans
            pmp_fwd = []
            pmp_rev = []
            for index in range(len(all_p_fwd)):
                pmp_fwd.append(np.max(all_p_fwd[index]))
                pmp_rev.append(np.max(all_p_rev[index]))

            # Append to list
            t_vals.append(all_t_elapsed)
            pmp_fwd_vals.append(pmp_fwd)
            pmp_rev_vals.append(pmp_rev)

        return t_vals, pmp_fwd_vals, pmp_rev_vals

    # Workhorse functions for analyze_from_savepath

    def analyze_files(
        self,
        jv_folders: list,
        jv_dict: dict,
        mpp_folder: list,
        mpp_dict: dict,
        env_folder:list,
        env_dict: dict,
        analyzed_folder: str,
    ) -> list:

        """Cycle through JV files, analyze, and make output file for parameters

        Args:
            jv_folders (list[str]): list of jv folders
            jv_dict (dict): dictionary mapping jv folders to file paths
            mpp_folders (list[str]): list of mpp folders
            mpp_dict (dict): dictionary mapping mpp folders to file paths
            analyzed_folder (str): analyzed folder path
            env_dict (dict): dictionary mapping env folders to file paths
            env_folder (str): env folder path
        Returns:
            list[str]: path to analyzed files
        """

        # Make blank array to keep save locations
        save_locations = []

        # Cycle through every module/folder in JV dict
        for idx, jv_folder in enumerate(jv_folders):

            # Load data from JV files
            jv_file_paths = jv_dict[jv_folder]
            (
                all_t,
                all_v,
                all_vm_fwd,
                all_i_fwd,
                all_j_fwd,
                all_p_fwd,
                all_vm_rev,
                all_i_rev,
                all_j_rev,
                all_p_rev,
            ) = self.load_jv_files(jv_file_paths)

            # Get info from JV file name
            d = self.filestructure.filepath_to_runinfo(jv_file_paths[idx])

            # Make time data numpy array, calc time elapsed
            all_t = np.array(all_t)
            all_t_elapsed = all_t - all_t[0]

            # Pass all vectors to function to calculate scalars
            scalardict_fwd = self._calculate_jv_parameters(
                all_vm_fwd, all_j_fwd, all_p_fwd, "FWD"
            )
            scalardict_rev = self._calculate_jv_parameters(
                all_vm_rev, all_j_rev, all_p_rev, "REV"
            )

            # Create scalardict, append time values and results from each scalardict
            scalardict = {}
            scalardict["Time (Epoch)"] = [t_epoch for t_epoch in all_t]
            scalardict["Time Elapsed (s)"] = [t_ for t_ in all_t_elapsed]
            for k, v in scalardict_rev.items():
                scalardict[k] = v
            for k, v in scalardict_fwd.items():
                scalardict[k] = v

            # Interpolate environmental data for each set of JV curves
            t = np.asarray([t_epoch for t_epoch in all_t])
            env_headers, env_data = self.interp_env_data(t, env_dict[env_folder[0]])
            for idx in range(1, len(env_headers)):
                scalardict[env_headers[idx]] = env_data[idx]
            
            # TODO: Check verify off Photodiode reading
            scalardict["REV PCE Norm (%)"] = np.asarray(scalardict["REV PCE (%)"])*np.asarray(scalardict["Intensity (# Suns)"])
            scalardict["FWD PCE Norm (%)"] = np.asarray(scalardict["FWD PCE (%)"])*np.asarray(scalardict["Intensity (# Suns)"])

            # Create dataframe from dictionary
            scalar_df = pd.DataFrame(scalardict)

            # Filter dataframe
            scalar_df_filtered = self.filter_parameters(scalar_df)

            # Save dataframe to csv
            analysis_file = self.filestructure.get_analyzed_file_name(
                d["date"], d["name"], d["string_id"], d["module_id"]
            )
            save_loc = os.path.join(analyzed_folder, analysis_file)
            scalar_df_filtered.to_csv(save_loc, index=False, mode = 'w+')
            save_locations.append(save_loc)

        return save_locations

    def _calculate_jv_parameters(
        self, all_v: list, all_j: list, all_p: list, direction: str
    ) -> dict:
        """Takes in voltage, current, and power vectors, calculates scalars and returns a dictionary of scalars

        Args:
            all_v (list[np.ndarray]): list of voltage vectors
            all_j (list[np.ndarray]): list of current vectors
            all_p (list[np.ndarray]): list of power vectors
            direction (str): direction -- either FWD or REV

        Returns:
            dict: dictionary of parameter values over time
        """

        # Create lists to hold data
        jsc_vals = []
        rsh_vals = []
        voc_vals = []
        rs_vals = []
        vmp_vals = []
        jmp_vals = []
        pmp_vals = []
        rch_vals = []
        ff_vals = []
        pce_vals = []

        # Cycle through v, j, p values
        for v, j, p in zip(all_v, all_j, all_p):

            # Try to calculate scalars
            try:
                
                v_iter = np.ceil(len(all_v[0])*self.derivative_v_percent)
                
                # Calculate Jsc and Rsh using J(v=0) to J(v = v_dir)
                wherevis0 = np.nanargmin(np.abs(v))
                wherevis0_1 = int(wherevis0 + v_iter)                

                j1 = j[wherevis0]
                j2 = j[wherevis0_1]
                v1 = v[wherevis0]
                v2 = v[wherevis0_1]
                m = (j2 - j1) / (v2 - v1)
                b = j1 - m * v1
                if m != 0:
                    rsh = float(abs(1 / m))
                    jsc = float(b)
                else:
                    rsh = np.inf
                    jsc = float(b)

                # Calculate Voc and Rs from J(J=0) to derivative_v_step V before
                wherejis0 = np.nanargmin(np.abs(j))
                wherejis0_1 = int(wherejis0 - v_iter)
                j1 = j[wherejis0]
                j2 = j[wherejis0_1]
                v1 = v[wherejis0]
                v2 = v[wherejis0_1]
                m = (j2 - j1) / (v2 - v1)
                b = j1 - m * v1
                rs = float(abs(1 / m))
                voc = float(-b / m)

                # Calculate Pmp, Vmp, Jmp
                pmp = np.nanmax(p)
                pmaxloc = np.nanargmax(p)
                vmp = v[pmaxloc]
                jmp = j[pmaxloc]

                # Calculate Rch using Vmpp-(derivative_v_step/2) V to vmpp+(derivative_v_step/2) V
                j1 = j[pmaxloc - math.floor(v_iter / 2)]
                j2 = j[pmaxloc + math.floor(v_iter / 2)]
                v1 = v[pmaxloc - math.floor(v_iter / 2)]
                v2 = v[pmaxloc + math.floor(v_iter / 2)]
                if j1 != j2 and v1 != v2:
                    m = (j2 - j1) / (v2 - v1)
                    rch = float(abs(1 / m))
                else:
                    rch = np.nan

                # Calculate FF and PCE if its not going to throw an error, else flag FF as NaN
                if pmp > 0 and voc > 0 and jsc > 0:
                    ff = 100 * pmp / (voc * jsc)
                    pce = ff * jsc * voc / 100
                else:
                    jsc = np.nan
                    rsh = np.nan
                    voc = np.nan
                    rs = np.nan
                    vmp = np.nan
                    jmp = np.nan
                    pmp = np.nan
                    rch = np.nan
                    ff = np.nan
                    pce = np.nan

            # If we run into any issues, just make values for time NaN
            except:
                jsc = np.nan
                rsh = np.nan
                voc = np.nan
                rs = np.nan
                vmp = np.nan
                jmp = np.nan
                pmp = np.nan
                rch = np.nan
                ff = np.nan
                pce = np.nan

            # Append values to lists
            finally:
                jsc_vals.append(jsc)
                rsh_vals.append(rsh)
                voc_vals.append(voc)
                rs_vals.append(rs)
                vmp_vals.append(vmp)
                jmp_vals.append(jmp)
                pmp_vals.append(pmp)
                rch_vals.append(rch)
                ff_vals.append(ff)
                pce_vals.append(pce)

        # Create dictionary to hold data
        returndict = {
            direction + " PCE (%)": pce_vals,
            direction + " Jsc (mA/cm2)": jsc_vals,
            direction + " Voc (V)": voc_vals,
            direction + " FF (%)": ff_vals,
            direction + " Rsh (Ohm/cm2)": rsh_vals,
            direction + " Rs (Ohm/cm2)": rs_vals,
            direction + " Rch (Ohm/cm2)": rch_vals,
            direction + " Jmp (mA/cm2)": jmp_vals,
            direction + " Vmp (V)": vmp_vals,
            direction + " Pmp (mW/cm2)": pmp_vals,
        }
        
        return returndict

    def interp_env_data(self, epochstamps: np.ndarray, files:list) -> list:
        """Interpolates the env matrix to the timestamps

        Args:
            epochstamps (np.ndarray): list of timestamps to interpolate to
            files (list(str)): list of filepaths to env data

        Returns:
            list(str): headers for interpolated dataframe
            list(float): data for interpolated dataframe
        """
        
        # NEWNEW Pass list, get numpy arrays of all the data
        t, temp, rh, intensity = self.load_env_files(files)
        df_data = [t, temp, rh, intensity]
        df_headers = ["Time (Epoch)", "Temperature (C)", "RH (%)", "Intensity (# Suns)"]

        # Create seccond list to start interpolating data. Start data with start time
        df2_data = [epochstamps]

        # Grab monitoring_time, interpolate monitoring data to epochstamps
        monitoring_times = df_data[0]
        for idx in range(1, len(df_data)):

            interp_data = np.interp(epochstamps, monitoring_times, df_data[idx])
            df2_data.append(interp_data)

        return df_headers, df2_data

    def filter_parameters(self, df: pd.DataFrame) -> pd.DataFrame:
        """Lightly filters input Scalars dataframe to ensure values are realistic

        Args:
            df (pd.DataFrame): dataframe of JV scalars over time

        Returns:
            pd.DataFrame: filtered dataframe with 0 < FF < 100 and 0 < Voc < 10
        """

        # Ensure we dont have crazy numbers
        df_filtered = df[
            (df["REV FF (%)"] < 100)
            & (df["REV FF (%)"] > 0)
            # & (df["REV Voc (V)"] < 10)
            # & (df["REV Voc (V)"] > 0)
            & (df["FWD FF (%)"] < 100)
            & (df["FWD FF (%)"] > 0)
            # & (df["FWD Voc (V)"] < 10)
            # & (df["FWD Voc (V)"] > 0)
        ]

        # Drop any rows with NaN values
        df_filtered_2 = df_filtered.reset_index(drop=True)

        return df_filtered_2

    # Load various files into program

    def load_jv_files(self, jv_file_paths: list) -> list:
        """Loads JV files contained in jv_file_paths, returns data

        Args:
            jv_file_paths (list[str]): list of paths to jv files

        Returns:
            list[np.ndarray]: list of time vectors
            list[np.ndarray]: list of voltage applied vectors
            list[np.ndarray]: list of FWD voltage measured vectors
            list[np.ndarray]: list of FWD current vectors
            list[np.ndarray]: list of FWD current density vectors
            list[np.ndarray]: list of FWD power vectors
            list[np.ndarray]: list of REV voltage measured vectors
            list[np.ndarray]: list of REV current vectors
            list[np.ndarray]: list of REV current density vectors
            list[np.ndarray]: list of REV power vectors
        """

        # Create blank lists to fill with numpy arrays
        all_t = []
        all_v = []
        all_vm_fwd = []
        all_i_fwd = []
        all_j_fwd = []
        all_p_fwd = []
        all_vm_rev = []
        all_i_rev = []
        all_j_rev = []
        all_p_rev = []

        # Cycle through all files, append values
        for jv_file_path in jv_file_paths:

            t, v, vm_fwd, i_fwd, j_fwd, p_fwd, vm_rev, i_rev, j_rev, p_rev = self.load_jv_file(jv_file_path)
            all_t.append(t)
            all_v.append(v)
            all_vm_fwd.append(vm_fwd)
            all_i_fwd.append(i_fwd)
            all_j_fwd.append(j_fwd)
            all_p_fwd.append(p_fwd)
            all_vm_rev.append(vm_rev)
            all_i_rev.append(i_rev)
            all_j_rev.append(j_rev)
            all_p_rev.append(p_rev)

        return all_t, all_v, all_vm_fwd, all_i_fwd, all_j_fwd, all_p_fwd, all_vm_rev, all_i_rev, all_j_rev, all_p_rev

    def load_jv_file(self, jv_file_path: str) -> np.ndarray:
        """Loads data for a single JV file given by jv_file_path, returns data

        Args:
            jv_file_path (string): path to JV file

        Returns:
            np.ndarray: time vector
            np.ndarray: voltage applied vector
            np.ndarray: FWD voltage measured vector
            np.ndarray: FWD current vector
            np.ndarray: FWD current density vector
            np.ndarray: FWD power density vector
            np.ndarray: REV voltage measured vector
            np.ndarray: REV current vector
            np.mdarray: REV current density vector
            np.ndarray: REV power vector
        """

        # Get time information
        with open(jv_file_path) as f:
            reader = csv.reader(f)
            _ = next(reader)  # date
            _ = next(reader)  # time
            t = float(next(reader)[-1])  # epoch time
            _ = next(reader)  # string
            _ = next(reader)  # module
            _ = next(reader)  # area

        # Load rest of dataframe, split into paramters, and return
        all_data = np.loadtxt(jv_file_path, delimiter=",", skiprows=8)
        all_data = np.transpose(all_data)
        if len(all_data)>0:
            v = all_data[0]
            vm_fwd = all_data[1]
            i_fwd = all_data[2]
            j_fwd = all_data[3]
            p_fwd = all_data[4]
            vm_rev = all_data[5]
            i_rev = all_data[6]
            j_rev = all_data[7]
            p_rev = all_data[8]
        else:
            v = []
            vm_fwd = []
            i_fwd = []
            j_fwd = []
            p_fwd = []
            vm_rev = []
            i_rev = []
            j_rev = []
            p_rev = []

        return t, v, vm_fwd, i_fwd, j_fwd, p_fwd, vm_rev, i_rev, j_rev, p_rev

    def load_mpp_files(self, mpp_file_paths: list) -> np.ndarray:
        """Loads MPP files contained in mpp_file_paths, returns data

        Args:
            mpp_file_paths (list[str]): list of paths to mpp files

        Returns:
            np.ndarray: list of time vectors
            np.ndarray: list of voltage measured vectors
            np.ndarray: list of voltage applied vectors
            np.ndarray: list of current vectors
            np.ndarray: list of current density vectors
            np.ndarray: list of power density vectors
        """

        # Create blank lists to fill with numpy arrays
        all_t = []
        all_vm = []
        all_v = []
        all_i = []
        all_j = []
        all_p = []

        # Extend the lists [a1,a2] +[b1,b2] = [a1,a2,b1,b2]
        for mpp_file_path in mpp_file_paths:
            t, vm, v, i, j, p = self.load_mpp_file(mpp_file_path)
            all_t.extend(t)
            all_vm.extend(vm)
            all_v.extend(v)
            all_i.extend(i)
            all_j.extend(j)
            all_p.extend(p)

        # Turn into numpy arrays
        t_s = np.asarray(all_t)
        vm_s = np.asarray(all_vm)
        v_s = np.asarray(all_v)
        i_s = np.asarray(all_i)
        j_s = np.asarray(all_j)
        p_s = np.asarray(all_p)

        return t_s, vm_s, v_s, i_s, j_s, p_s

    def load_mpp_file(self, mpp_file_path: str) -> list:
        """Loads data for a single MPP file given by mpp_file_path, returns values

        Args:
            mpp_file_path (string): path to MPP file

        Returns:
            list[float]: time vector
            list[float]: voltage measured vector
            list[float]: voltage applied vector
            list[float]: current vector
            list[float]: current denisty vector
            list[float]: power denisty vector
        """

        # Initialize lists
        t = []
        vm = []
        v = []
        i = []
        j = []
        p = []

        # Fill with data
        with open(mpp_file_path) as f:
            csvreader = reader(f, delimiter=",")
            for _ in range(7):
                next(csvreader)
            for line in csvreader:
                t.append(float(line[0]))
                vm.append(float(line[1]))
                v.append(float(line[2]))
                i.append(float(line[3]))
                j.append(float(line[4]))
                p.append(float(line[5]))

        # Convert to lists if not already a list (floats throw errors in sequential code)
        if type(t) is not list:
            t2 = [t]
        else:
            t2 = t
        if type(vm) is not list:
            vm2 = [vm]
        else:
            vm2 = vm
        if type(v) is not list:
            v2 = [v]
        else:
            v2 = v
        if type(i) is not list:
            i2 = [i]
        else:
            i2 = i
        if type(j) is not list:
            j2 = [j]
        else:
            j2 = j
        if type(p) is not list:
            p2 = [p]
        else:
            p2 = p

        return t2, vm2, v2, i2, j2, p2

    def load_env_files(self, env_file_paths: list) -> np.ndarray:
        """Loads env files contained in env_file_paths, returns data

        Args:
            env_file_paths (list[str]): list of paths to env files

        Returns:
            np.ndarray: list of epoch time vectors
            np.ndarray: list of temperature vectors
            np.ndarray: list of relative humidity vectors
            np.ndarray: list of intensity vectors
        """

        # Create blank lists to fill with numpy arrays
        all_t = []
        all_temp = []
        all_rh = []
        all_int = []

        # Extend the lists [a1,a2] +[b1,b2] = [a1,a2,b1,b2]
        for env_file_path in env_file_paths:
            t, temp, rh, intensity = self.load_env_file(env_file_path)
            all_t.extend(t)
            all_temp.extend(temp)
            all_rh.extend(rh)
            all_int.extend(intensity)

        # Turn into numpy arrays
        t_s = np.asarray(all_t)
        temp_s = np.asarray(all_temp)
        rh_s = np.asarray(all_rh)
        int_s = np.asarray(all_int)

        return t_s, temp_s, rh_s, int_s

    def load_env_file(self, env_file_path: str) -> list:
        """Loads Environmental File

        Args:

        Returns:
            list[float]: epoch time
            list[float]: temperature
            list[float]: relative humidity
            list[float]: intensity
        """

        # Create blank lists to fill with float variables
        t = []
        temp = []
        rh = []
        intensity = []

        # Append to the lists
        with open(env_file_path) as f:
            csvreader = reader(f, delimiter=",")
            next(csvreader)  # skip header
            for line in csvreader:
                t.append(float(line[0]))
                temp.append(float(line[1]))
                rh.append(float(line[2]))
                intensity.append(float(line[3]))
        return t, temp, rh, intensity

#TODO: COMPLETE & VERIFY
    def combine_tests(self, tests: list):
        
        # Create test dictionary
        tests = ['C:\\Users\\seand\OneDrive - UC San Diego\\Documents\\PARASOL\\Characterization\\x20230710\\x20230710_A12D80852_2' ,
                'C:\\Users\\seand\OneDrive - UC San Diego\\Documents\\PARASOL\\Characterization\\x20230717\\x20230717_A12D80852_2']
        test_folders_dict = self.filestructure.map_test_folders(tests)
        
        # Cycle through scan type folders
        for scan_type in test_folders_dict[tests[0]].keys():
            
            # list of list of files for all scans [[],[]]
            files = self.filestructure.get_files(tests, scan_type)
            
            # get last file and last index for first set of files
            last_file = (files[0])[-1]
            directory = os.path.dirname(last_file)
            current_index = int((last_file.split('_')[-1]).split('.')[0])
            last_index = current_index

            # interate through all but first file
            for scan_set in files[1::]:
                for scan in scan_set:
                    current_index += 1
                    

                    scan_name = os.path.basename(scan)
                    scan_prefix = scan_name.removesuffix(scan_name.split('_')[-1])
                    new_name = os.path.join(directory, scan_prefix + f'{current_index}.csv')
                    os.rename(scan,new_name)
        
        test_folders_dict = self.filestructure.map_test_folders(tests)
        
        files = self.filestructure.get_files(tests,'Analyzed')
        for scan_set in files:
            for scan in scan_set:
                os.remove(scan)
        
        self.analyze_from_savepath(tests[0])
        

        for test in tests[1::]:
            for folder in test:
                os.rmdir(folder)
            os.rmdir(test)
        