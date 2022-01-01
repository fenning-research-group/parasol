import pandas as pd
import numpy as np
import os
import csv

from parasol.filestructure import FileStructure


class Analysis:
    """Analysis package for PARASOL"""

    def __init__(self) -> None:
        """Initializes Analysis class"""
        self.NUM_MODULES = 24
        self.filestructure = FileStructure()

    # Main tests

    def check_test(self, jvfolderpaths: list, mppfolderpaths: list) -> pd.DataFrame:
        """Calcualte FWD and REV Pmp versus time for given JV and MPP folder paths, returns dataframe with data

        Args:
            jvfolderpaths (list[str]): paths to the JV folders for the test
            mppfolderpaths (list[str]): paths to the MPP folders for the test

        Returns:
            pd.DataFrame: ["Time Elapsed (s)", "FWD Pmp (mW/cm2)", "REV Pmp (mW/cm2)"]
        """
        self.jv_folders = jvfolderpaths

        # Get JV & MPP file paths: create dictionary: dict[folderpath] = file_paths
        self.jv_dict = self.filestructure.map_test_files(self.jv_folders)

        # calculate pmpps (1 array per module), stick in dictionary
        t_vals, pmp_fwd_vals, pmp_rev_vals = self.check_pmps()

        col_names = ["Time Elapsed (s)", "FWD Pmp (mW/cm2)", "REV Pmp (mW/cm2)"]
        data = list(zip(t_vals, pmp_fwd_vals, pmp_rev_vals))
        plot_df = pd.DataFrame(columns=col_names, data=data)

        return plot_df

    def analyze_from_savepath(self, stringpath: str) -> list:
        """Analyze data for given test path, create output x<date>_<name>_<string>_<module>_Scalar_1.csv file in Analysis folder

        Args:
            stringpath (str): path to test folder

        Returns:
            list[str]: path to output file
        """

        # Get folder paths: create self.mpp_folder, self.jv_folders, and self.analyzed_folder
        self.stringpath = stringpath
        (
            self.mpp_folder,
            self.jv_folders,
            self.analyzed_folder,
        ) = self.filestructure.get_test_subfolders(stringpath)
        os.mkdir(self.analyzed_folder)

        # Get JV & MPP file paths: create dictionary: dict[folderpath] = file_paths
        self.jv_dict = self.filestructure.map_test_files(self.jv_folders)

        # Analyze JV files: For each module export scalars_{module}.csv
        analyzed_waves = self.analyze_jv_files()

        return analyzed_waves

    # Workhorse functions for check_test and analyze_from_savepath

    # TODO: EDIT NO JVDICT
    def check_pmps(self) -> float:
        """Loads the JV files, calculates and returns time, FWD Pmp, and REV Pmp

        Returns:
            numpy: time values for each scan
            list[np.array]: forward pmp values for each scan
            list[np.array]: reverse pmp values for each scan
        """

        t_vals = []
        pmp_fwd_vals = []
        pmp_rev_vals = []

        # cycle through each folder/module
        for jv_folder in self.jv_folders:
            jv_file_paths = self.jv_dict[jv_folder]

            # load jv files
            (
                all_t,
                all_v,
                all_j_fwd,
                all_p_fwd,
                all_j_rev,
                all_p_rev,
            ) = self.analysis.load_jv_files(jv_file_paths)

            # make time data numpy array, calc time elapsed
            all_t = np.array(all_t)
            all_t_elapsed = all_t - all_t[0]

            # calc pmp
            pmp_fwd = []
            pmp_rev = []

            for index in range(len(all_p_fwd)):
                pmp_fwd.append(np.max(all_p_fwd[index]))
                pmp_rev.append(np.max(all_p_rev[index]))

            # append to list
            t_vals.append(all_t_elapsed)
            pmp_fwd_vals.append(pmp_fwd)
            pmp_rev_vals.append(pmp_rev)

        return t_vals, pmp_fwd_vals, pmp_rev_vals

    # TODO: should take in jv_folders and jv_dict
    def analyze_jv_files(self) -> list:
        """Cycle through JV files, analyze, and make output file for parameters

        Returns:
            list[str]: path to analyzed files
        """

        # Make blank array to keep save locations
        save_locations = []

        # cycle through every module/folder in jv dict
        for jv_folder in self.jv_folders:
            # Get Module Number
            module_num = jv_folder.split("_")[-1]

            jv_file_paths = self.jv_dict[jv_folder]
            (
                all_t,
                all_v,
                all_j_fwd,
                all_p_fwd,
                all_j_rev,
                all_p_rev,
            ) = self.load_jv_files(jv_file_paths)

            # make time data numpy array, calc time elapsed
            all_t = np.array(all_t)
            all_t_elapsed = all_t - all_t[0]

            # pass all vectors to function to calculate scalars
            scalardict_fwd = self._calculate_jv_parameters(
                all_v, all_j_fwd, all_p_fwd, "FWD"
            )
            scalardict_rev = self._calculate_jv_parameters(
                all_v, all_j_rev, all_p_rev, "REV"
            )
            # create scalardict, append time values and results from each scalardict
            scalardict = {}
            scalardict["Time (Epoch)"] = [t_epoch for t_epoch in all_t]
            scalardict["Time Elapsed (s)"] = [t_ for t_ in all_t_elapsed]
            for k, v in scalardict_rev.items():
                scalardict[k] = v
            for k, v in scalardict_fwd.items():
                scalardict[k] = v

            # get info from jv file name
            d = self.filestructure.filepath_to_runinfo(jv_file_paths[-1])
            # create scalar dataframe, filter it, and save it in analyzed folder
            scalar_df = pd.DataFrame(scalardict)
            scalar_df_filtered = self.filter_jv_parameters(scalar_df)

            analysis_file = self.filestructure.get_analyzed_file_name(
                d["date"], d["name"], d["string_id"]
            )
            save_loc = os.path.join(self.analyzed_folder, analysis_file)
            scalar_df_filtered.to_csv(save_loc, index=False)
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

        # create lists to hold data
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

        # cycle through v, j, p values
        for v, j, p in zip(all_v, all_j, all_p):

            # try to calculate scalars
            try:

                # calculate jsc and rsh using J(v=0) to J(v=0.05)
                wherevis0 = np.nanargmin(np.abs(v))
                wherevis0_1 = np.nanargmin(np.abs(v - 0.05))
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

                # calculate voc and rs from J(J=0) to 0.05 V before
                v_iter = max(int(0.05 / (v[2] - v[1])), 1)
                wherejis0 = np.nanargmin(np.abs(j))
                wherejis0_1 = wherejis0 - int(v_iter)
                j1 = j[wherejis0]
                j2 = j[wherejis0_1]
                v1 = v[wherejis0]
                v2 = v[wherejis0_1]
                m = (j2 - j1) / (v2 - v1)
                b = j1 - m * v1
                rs = float(abs(1 / m))
                voc = float(-b / m)

                # calculate Pmp, Vmp, Jmp
                pmp = np.nanmax(p)
                pmaxloc = np.nanargmax(p)
                vmp = v[pmaxloc]
                jmp = j[pmaxloc]

                # calculate Rch using vmpp-0.05V to vmpp+0.05V
                j1 = j[pmaxloc - v_iter]
                j2 = j[pmaxloc + v_iter]
                v1 = v[pmaxloc - v_iter]
                v2 = v[pmaxloc + v_iter]
                if j1 != j2 and v1 != v2:
                    m = (j2 - j1) / (v2 - v1)
                    rch = float(abs(1 / m))
                else:
                    rch = np.nan

                # calculate FF and PCE if its not going to throw an error, else flag FF as NaN
                if pmp > 0 and voc > 0 and jsc > 0:
                    ff = 100 * pmp / (voc * jsc)
                    pce = ff * jsc * voc / 100
                else:
                    ff = np.nan

            # if we run into any issues, just make values for time NaN
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

            # append values to lists
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

        # create dict to hold data
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

    def filter_jv_parameters(self, df: pd.DataFrame) -> pd.DataFrame:
        """Lightly filters input Scalars dataframe to ensure values are reslistic

        Args:
            df (pd.DataFrame): dataframe of JV scalars over time

        Returns:
            pd.DataFrame: filtered dataframe with 0<FF<100 and 0<Voc<10
        """

        # Ensure we dont have crazy numbers
        df_filtered = df[
            (df["REV FF (%)"] < 100)
            & (df["REV FF (%)"] > 0)
            & (df["REV Voc (V)"] < 10)
            & (df["REV Voc (V)"] > 0)
            & (df["FWD FF (%)"] < 100)
            & (df["FWD FF (%)"] > 0)
            & (df["FWD Voc (V)"] < 10)
            & (df["FWD Voc (V)"] > 0)
        ]

        # Drop any rows with NaN values
        df_filtered_2 = df_filtered.reset_index(drop=True)

        return df_filtered_2

    # Loads jv files

    def load_jv_files(self, jv_file_paths: list) -> list:
        """Loads JV files contained in jv_file_paths, returns data

        Args:
            jv_file_paths (list[str]): list of paths to jv files

        Returns:
            list[np.ndarray]: list of time vectors
            list[np.ndarray]: list of voltage vectors
            list[np.ndarray]: list of FWD current vectors
            list[np.ndarray]: list of FWD power vectors
            list[np.ndarray]: list of REV current vectors
            list[np.ndarray]: list of REV power vectors
        """

        all_t = []
        all_v = []
        all_j_fwd = []
        all_p_fwd = []
        all_j_rev = []
        all_p_rev = []

        for jv_file_path in jv_file_paths:

            t, v, j_fwd, p_fwd, j_rev, p_rev = self.load_jv_file(jv_file_path)
            all_t.append(t)
            all_v.append(v)
            all_j_fwd.append(j_fwd)
            all_p_fwd.append(p_fwd)
            all_j_rev.append(j_rev)
            all_p_rev.append(p_rev)

        return all_t, all_v, all_j_fwd, all_p_fwd, all_j_rev, all_p_rev

    def load_jv_file(self, jv_file_path: str) -> np.ndarray:
        """Loads data for a single JV file given by jv_file_path, returns data

        Args:
            jv_file_path (string): path to JV file

        Returns:
           np.ndarray: time vector
           np.ndarray: voltage vector
           np.ndarray: FWD current vector
           np.ndarray: FWD power vector
           np.ndarray: REV current vector
           np.ndarray: REV power vector
        """

        # get time information
        with open(jv_file_path) as f:
            reader = csv.reader(f)
            _ = next(reader)  # date
            _ = next(reader)  # time
            t = float(next(reader)[-1])  # epoch time
            _ = next(reader)  # string
            _ = next(reader)  # module
            _ = next(reader)  # area

        # load rest of dataframe and split
        all_data = np.loadtxt(jv_file_path, delimiter=",", skiprows=8)
        all_data = np.transpose(all_data)
        v = all_data[0]
        j_fwd = all_data[2]
        p_fwd = all_data[3]
        j_rev = all_data[5]
        p_rev = all_data[6]

        return t, v, j_fwd, p_fwd, j_rev, p_rev

    def load_mpp_file(self, mpp_file_path: str) -> np.ndarray:
        """Loads data for a single MPP file given by mpp_file_path, returns values

        Args:
            mpp_file_path (string): path to MPP file

        Returns:
            np.ndarray: time vector
            np.ndarray: voltage vector
            np.ndarray: current vector
            np.ndarray: current denisty vector
            np.ndarray: power denisty vector
        """

        with open(mpp_file_path) as f:
            reader = csv.reader(f)
            _ = next(reader)  # date
            _ = next(reader)  # time
            t_start = float(next(reader)[-1])  # epoch time
            _ = next(reader)  # string
            _ = next(reader)  # module
            _ = next(reader)  # area

        # load rest of dataframe and split
        all_data = np.loadtxt(mpp_file_path, delimiter=",", skiprows=8)
        all_data = np.transpose(all_data)
        t = all_data[0]
        v = all_data[1]
        i = all_data[2]
        j = all_data[3]
        p = all_data[4]

        return t, v, i, j, p
