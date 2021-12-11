import pandas as pd
import numpy as np
import os
import matplotlib.pyplot as plt
import matplotlib as mpl

# File Structure:
# WorkingDirectory:StringName:
# WorkingDirectory:StringName:MPP:
# WorkingDirectory:StringName:JV_{module}:
# WorkingDirectory:StringName:Analyzed:


class Parasol_String:
    def __init__(self, stringpath):
        """Initialize the Parasol_String class"""

        # intiliaze variables for program
        self.NUM_MODULES = 24

        # create folder paths
        self.stringpath = stringpath
        (
            self.mpp_folder,
            self.jv_folders,
            self.analyzed_folder,
        ) = self.create_folder_paths()

        # create dictionary of folder paths: file paths
        self.jv_dict = self.create_file_paths(self.jv_folders)
        self.mpp_dict = self.create_file_paths(self.mpp_folder)

        # analyze jv files
        self.analyze_jv_files()

    def create_folder_paths(self):
        """Create folder paths for analysis including: self.mpp_folder, self.jv_folder, and self.analyzed_folder"""

        # path to mpp folder --> rootfolder:MPP:
        mpp_folder = os.path.join(self.stringpath, "MPP")

        # path to jv folders --> rootfolder:JV_{module}:
        jv_folders = []
        for i in range(1, self.NUM_MODULES + 1):
            jv_folder = os.path.join(self.stringpath, "JV_" + str(int(i)))
            if os.path.exists(jv_folder):
                jv_folders.append(jv_folder)

        # path to analyzed folder --> rootfolder:Analyzed
        analyzed_folder = os.path.join(self.stringpath, "Analyzed")
        if not os.path.exists(analyzed_folder):
            os.makedirs(analyzed_folder)

        return mpp_folder, jv_folders, analyzed_folder

    def create_file_paths(self, folderpath):
        """Create file_dict[folder] = filepaths"""

        # create blank dictionary to hold folder: file_paths
        file_dict = {}

        # cycle through folders
        for folder in folderpath:

            # initialize lists
            files = []
            scan_numbers = []
            paths_chronological = []

            # in each folder, get list of files that end with .csv
            all_files = os.listdir(folder)
            for file in all_files:
                if file.find(".csv") != -1:
                    files.append(file)

            # for each folder, create list of scan numbers
            for file in files:
                scan_numbers.append(file.split("_")[-1]).split(".")[0]

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

            # get list of file paths, create empty lists for important parameters
            jv_file_paths = self.jv_dict[jv_folder]
            all_t = []
            all_v = []
            all_j_fwd = []
            all_p_fwd = []
            all_j_rev = []
            all_p_rev = []

            # get header info from first file --> not used for now
            # with open(jv_file_paths[0], "r") as f:
            #     date = f.readline().split(":")[-1]
            #     time = f.readline().split(":")[-1]
            #     epoch_time = f.readline().split(":")[-1]
            #     string_id = f.readline().split(":")[-1]
            #     module_id = f.readline().split(":")[-1]
            #     area = f.readline().split(":")[-1]

            # cycle through each jv file
            for jv_file_path in jv_file_paths:

                # get time information
                with open(jv_file_path) as f:
                    f.readline()  # date
                    f.readline()  # time
                    all_t.append((f.readline()).split(":")[-1])  # epoch time
                    f.readline()  # string
                    f.readline()  # module
                    f.readline()  # area

                # load rest of dataframe and split
                df = pd.read_csv(jv_file_path, header=None, skiprows=6, index_col=0)
                all_v.append(df.iloc[0])
                all_j_fwd.append(df.iloc[2])
                all_p_fwd.append(df.iloc[3])
                all_j_rev.append(df.iloc[5])
                all_p_rev.append(df.iloc[6])

            # make all data numpy arrays
            all_t = np.array(all_t)
            all_t_elapsed = all_t - all_t[0]
            all_v = np.array(all_v)
            all_j_fwd = np.array(all_j_fwd)
            all_p_fwd = np.array(all_p_fwd)
            all_j_rev = np.array(all_j_rev)
            all_p_rev = np.array(all_p_rev)

            # pass all data to function to calculate parameters
            scalardict_fwd = self._calculate_jv_parameters(
                all_v, all_j_fwd, all_p_fwd, "fwd"
            )
            scalardict_rev = self._calculate_jv_parameters(
                all_v, all_j_rev, all_p_rev, "rev"
            )

            # create dict, append time values and results from each scalardict
            dfdict = {}
            dfdict["epoch"] = [t_epoch for t_epoch in all_t]
            dfdict["time_elapsed"] = [t_ for t_ in all_t_elapsed]
            for k, v in scalardict_rev.items():
                dfdict[k] = v
            for k, v in scalardict_fwd.items():
                dfdict[k] = v

            # create df, filter it, and save in analyzed folder
            df = pd.DataFrame(dfdict)
            df_filtered = self.filter_jv_parameters(df)
            save_loc = os.path.join(self.analyzed_folder, "Parameters.csv")
            df_filtered.to_csv(save_loc, index=False)

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
            "pce_" + direction: pce_vals,
            "jsc_" + direction: jsc_vals,
            "voc_" + direction: voc_vals,
            "ff_" + direction: ff_vals,
            "rsh_" + direction: rsh_vals,
            "rs_" + direction: rs_vals,
            "rch_" + direction: rch_vals,
            "jmp_" + direction: jmp_vals,
            "vmp_" + direction: vmp_vals,
            "pmp_" + direction: pmp_vals,
        }

        return returndict

    def filter_jv_parameters(self, df):
        """Filter parameters dataframe"""

        # Ensure we dont have crazy numbers
        df_filtered = df[
            (df["ff_rev"] < 100)
            & (df["ff_rev"] > 0)
            & (df["voc_rev"] < 10)
            & (df["voc_rev"] > 0)
            & (df["ff_fwd"] < 100)
            & (df["ff_fwd"] > 0)
            & (df["voc_fwd"] < 10)
            & (df["voc_fwd"] > 0)
        ]

        # Drop any rows with NaN values
        df_filtered_2 = df_filtered.reset_index(drop=True)

        return df_filtered_2

        """Plot stats in parameter file"""

        df = pd.read_csv(parameter_path)

        # plot preferences
        mpl.rcParams["axes.linewidth"] = 1.75

        # dictionary to label plots
        LabelDict = {
            "epoch": "Epoch Time",
            "t": "Time Elapsed (hrs)",
            "jsc_fwd": "Short Circut Current Density (mA/cm²)",
            "voc_fwd": "Open Circut Voltage (V)",
            "ff_fwd": "Fill Factor (%)",
            "pce_fwd": "Power Conversion Efficiency (%)",
            "rs_fwd": "Series Resistance (Ω/cm²)",
            "rsh_fwd": "Shunt Resistance (Ω/cm²)",
            "rch_fwd": "Channel Resistance (Ω/cm²)",
            "vmp_fwd": "Maximum Power Point Voltage (V)",
            "jmp_fwd": "Maximum Power Point Current (mA/cm²)",
            "pmp_fwd": "Maximum Power Point Power (mW/cm²)",
            "v_rev": "Voltage (V)",
            "i_rev": "Current (mA)",
            "j_rev": "Current Density (mA/cm²)",
            "p_rev": "Power (mW)",
            "jsc_rev": "Short Circut Current Density (mA/cm²)",
            "voc_rev": "Open Circut Voltage (V)",
            "ff_rev": "Fill Factor (%)",
            "pce_rev": "Power Conversion Efficiency (%)",
            "rs_rev": "Series Resistance (Ω/cm²)",
            "rsh_rev": "Shunt Resistance (Ω/cm²)",
            "rch_rev": "Channel Resistance (Ω/cm²)",
            "vmp_rev": "Maximum Power Point Voltage (V)",
            "jmp_rev": "Maximum Power Point Current (mA/cm²)",
            "pmp_rev": "Maximum Power Point Power (mW/cm²)",
        }

        # plot each value
        for n in range(df.shape[0]):
            xval = df[x][n]
            yval = df[y][n]
            zval = df[z].values
            znorm = np.array(
                (zval - np.nanmin(zval)) / (np.nanmax(zval) - np.nanmin(zval))
            )
            colors = plt.cm.viridis(znorm.astype(float))
            plt.scatter(xval, yval, color=colors[n])

        # manage colorbar
        norm = mpl.colors.Normalize(vmin=np.nanmin(zval), vmax=np.nanmax(zval))
        objs = plt.colorbar(
            mpl.cm.ScalarMappable(norm=norm, cmap=plt.get_cmap("viridis")),
            orientation="vertical",
            label=str(LabelDict[z]),
        )
        plt.setp(
            objs.ax.get_yticklabels(),
            rotation=-10,
            fontsize=9,
            weight="black",
            snap=True,
            position=(1, 0),
        )

        # label axes
        plt.ylabel(LabelDict[y], weight="black")
        plt.xlabel(LabelDict[x], weight="black")

        # show plot
        plt.show()
