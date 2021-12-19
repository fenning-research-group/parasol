import pandas as pd
import numpy as np
import os
import matplotlib.pyplot as plt
import matplotlib as mpl
import csv

# File Structure:
# WorkingDirectory:StringName:
# WorkingDirectory:StringName:MPP:
# WorkingDirectory:StringName:JV_{module}:
# WorkingDirectory:StringName:Analyzed:


class Parasol_String:
    def __init__(self, stringpath):
        """Initialize the Parasol_String class"""

        # Intiliaze variables for program
        self.NUM_MODULES = 24

        # Get folder paths: create self.mpp_folder, self.jv_folders, and self.analyzed_folder
        self.stringpath = stringpath
        self.create_folder_paths()

        # Get JV & MPP file paths: create dictionary: dict[folderpath] = file_paths
        self.jv_dict = self.create_file_paths(self.jv_folders)
        self.mpp_dict = self.create_file_paths(self.mpp_folder)

        # Analyze JV files: For each module export scalars_{module}.csv
        self.analyze_jv_files()

    def create_folder_paths(self):
        """Create folder paths for analysis including: self.mpp_folder, self.jv_folder, and self.analyzed_folder"""

        # path to mpp folder --> rootfolder:MPP:
        self.mpp_folder = [os.path.join(self.stringpath, "MPP")]

        # path to jv folders --> rootfolder:JV_{module}:
        self.jv_folders = []
        for i in range(1, self.NUM_MODULES + 1):
            jv_folder = os.path.join(self.stringpath, "JV_" + str(int(i)))
            if os.path.exists(jv_folder):
                self.jv_folders.append(jv_folder)

        # path to analyzed folder --> rootfolder:Analyzed
        self.analyzed_folder = os.path.join(self.stringpath, "Analyzed")
        if not os.path.exists(self.analyzed_folder):
            os.makedirs(self.analyzed_folder)

    def create_file_paths(self, folderpath):
        """Create file_dict[folderpath] = filepaths"""

        # create blank dictionary to hold folder: file_paths
        file_dict = {}

        # cycle through folders
        for folder in folderpath:

            # initialize lists
            scan_numbers = []
            paths_chronological = []

            # Grab list of files in folder
            files = os.listdir(folder)

            # for each file, create list of scan numbers
            for file in files:
                scan_numbers.append(file.split("_")[-1])

            # sort files by scan number, create paths to files
            files_chronological = [x for _, x in sorted(zip(scan_numbers, files))]
            for file in files_chronological:
                paths_chronological.append(os.path.join(folder, file))

            # create dictionary basefolder : file_paths
            file_dict[folder] = paths_chronological

        return file_dict

    def analyze_jv_files(self):
        """Cycle through JV files, analyze, and make output file for parameters"""

        # cyle through every module/folder in jv dict
        for jv_folder in self.jv_folders:

            # Get Module Number
            module_num = jv_folder.split("_")[-1]

            # get list of file paths, create empty lists for parameters
            jv_file_paths = self.jv_dict[jv_folder]
            all_t = []
            all_v = []
            all_j_fwd = []
            all_p_fwd = []
            all_j_rev = []
            all_p_rev = []

            # cycle through each jv file
            for jv_file_path in jv_file_paths:

                # get time information
                with open(jv_file_path) as f:
                    reader = csv.reader(f)
                    _ = next(reader)  # date
                    _ = next(reader)  # time
                    all_t.append(float(next(reader)[-1]))  # epoch time
                    _ = next(reader)  # string
                    _ = next(reader)  # module
                    _ = next(reader)  # area

                # load rest of dataframe and split
                all_data = np.loadtxt(jv_file_path, delimiter=",", skiprows=8)
                all_data = np.transpose(all_data)
                all_v.append(all_data[0])
                all_j_fwd.append(all_data[2])
                all_p_fwd.append(all_data[3])
                all_j_rev.append(all_data[5])
                all_p_rev.append(all_data[6])

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

            # create scalar dataframe, filter it, and save it in analyzed folder
            scalar_df = pd.DataFrame(scalardict)
            scalar_df_filtered = self.filter_jv_parameters(scalar_df)
            save_loc = os.path.join(self.analyzed_folder, f"Scalars_{module_num}.csv")
            scalar_df_filtered.to_csv(save_loc, index=False)

    def _calculate_jv_parameters(self, all_v, all_j, all_p, direction):
        """Calculate parameters for each jv file"""

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

    def filter_jv_parameters(self, df):
        """Filter parameters dataframe"""

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
