import numpy as np
import pandas as pd
import matplotlib as mpl
import matplotlib.pyplot as plt
import yaml
import os

# from parasol.analysis.analysis import Analysis
from parasol.analysis.filestructure import FileStructure


class Grapher:
    def __init__(self):
        """Opens in root directory (same as parasol)"""

        # Load filstructure package to manage JV files
        self.filestructure = FileStructure()

        # Path to general data
        self.rootdir = self.filestructure.get_root_dir()

        self.variable_dict = {
            "Time": "Time (Epoch)",
            "Time Elapsed": "Time Elapsed (s)",
            "FWD Jsc": "FWD Jsc (mA/cm2)",
            "FWD Voc": "FWD Voc (V)",
            "FWD FF": "FWD FF (%)",
            "FWD Pce": "FWD PCE (%)",
            "FWD Rs": "FWD Rs (Ohm/cm2)",
            "FWD Rsh": "FWD Rsh (Ohm/cm2)",
            "FWD Rch": "FWD Rch (Ohm/cm2)",
            "FWD Vmp": "FWD Vmp (V)",
            "FWD Jmp": "FWD Jmp (mA/cm2)",
            "FWD Pmp": "FWD Pmp (mW/cm2)",
            "REV Jsc": "REV Jsc (mA/cm2)",
            "REV Voc": "REV Voc (V)",
            "REV FF": "REV FF (%)",
            "REV PCE": "REV PCE (%)",
            "REV Rs": "REV Rs (Ohm/cm2)",
            "REV Rsh": "REV Rsh (Ohm/cm2)",
            "REV Rch": "REV Rch (Ohm/cm2)",
            "REV Vmp": "REV Vmp (V)",
            "REV Jmp": "REV Jmp (mA/cm2)",
            "REV Pmp": "REV Pmp (mW/cm2)",
        }

        self.fwd_rev_cursor_dict = {
            0: ">",
            1: "<",
        }

        self.cursor_dict = {
            1: "o",
            2: "s",
            3: "^",
            4: "v",
            5: "D",
            6: "*",
            7: "p",
            8: "h",
            9: "P",
            10: "X",
        }

    def plot_x_v_ys(self, df, x, ys):
        """Plots x vs multiple ys for one dataframe"""

        # make dataframe for datafolder dictionary
        # df = pd.DataFrame.from_dict(df_dict)

        # get x list
        x_vals = df[x]

        # get y labels
        y_label = ""

        # cycle through the multiple y parameters
        for y_param in ys:

            y_vals = df[y_param]

            # for each parameter, plot all data
            for i in range(len(y_vals)):
                plt.scatter(x_vals[i], y_vals[i])
                y_label += str(y_param) + " / "

        # label axes
        y_label = y_label[:-3]
        plt.ylabel(y_label, weight="black")
        plt.xlabel(x, weight="black")

        plt.show()

    # Plot JV scans for a single module

    def plot_module_jvs(self, jvfolder):
        jv_dict = self.filestructure.map_test_files([jvfolder])
        jv_file_paths = jv_dict[jvfolder]
        self.plot_jvs(jv_file_paths)

    def plot_jvs(self, jvfiles):

        # load jv files
        (
            all_t,
            all_v,
            all_j_fwd,
            all_p_fwd,
            all_j_rev,
            all_p_rev,
        ) = self.analysis.load_jv_files(jvfiles)

        colors = plt.cm.viridis(np.linspace(0, 1, len(jvfiles)))

        # make time data numpy array, calc time elapsed
        all_t = np.array(all_t)
        all_t_elapsed = all_t - all_t[0]

        for jvpair in range(len(all_t_elapsed)):
            plt.plot(all_v[jvpair], all_j_fwd[jvpair], color=colors[jvpair])
            plt.plot(all_v[jvpair], all_j_rev[jvpair], "--", color=colors[jvpair])

        # label axes
        plt.ylabel("J (mA/cm2)", weight="black")
        plt.xlabel("V (V)", weight="black")
        plt.show()

    # Plot x v y with color axis as different devices
    # Plot x v y with color axis another parameter (z)

    def plot_xy_scalars(self, paramfiles, x, y):
        """Plots x vs y for set of paramfiles"""

        mpl.rcParams["axes.linewidth"] = 1.75

        for paramfile in paramfiles:

            # read in dataframe
            df = pd.read_csv(paramfile)

            # get x and y vals, add to plot
            x_vals = df[x]
            y_vals = df[y]
            plt.scatter(x_vals, y_vals)

        # label axes
        plt.ylabel(y, weight="black")
        plt.xlabel(x, weight="black")

        # display
        plt.show()

    def plot_xy2_scalars(self, paramfiles, x, ys):
        """Plots x vs ys (assumed to be fwd/rev) for set of paramfiles"""

        mpl.rcParams["axes.linewidth"] = 1.75

        for paramfile in paramfiles:

            # read in dataframe
            df = pd.read_csv(paramfile)

            # get x and y vals, add to plot
            x_vals = df[x]

            for idx, y in enumerate(ys):
                y_vals = df[y]
                plt.scatter(x_vals, y_vals, marker=self.fwd_rev_cursor_dict[idx])

        # label axes
        ylab = ""
        for y in ys:
            ylab += str(y) + " / "
        ylab = ylab[:-3]

        plt.ylabel(ylab, weight="black")
        plt.xlabel(x, weight="black")

        # display
        plt.show()

    def plot_xyz_scalar(self, paramfile, x, y, z):
        """Plots x vs y with z colorbar for paramfile"""

        # load datafolder path
        df = pd.read_csv(paramfile)

        # plot preferences
        mpl.rcParams["axes.linewidth"] = 1.75

        for n in range(df.shape[0]):

            # Get values for x and y
            xval = df[x][n]
            yval = df[y][n]

            # Get values for color bar
            zval = df[z].values
            znorm = np.array(
                (zval - np.nanmin(zval)) / (np.nanmax(zval) - np.nanmin(zval))
            )
            colors = plt.cm.viridis(znorm.astype(float))

            # Plot
            plt.scatter(xval, yval, color=colors[n])

        # manage colorbar
        norm = mpl.colors.Normalize(vmin=np.nanmin(zval), vmax=np.nanmax(zval))
        objs = plt.colorbar(
            mpl.cm.ScalarMappable(norm=norm, cmap=plt.get_cmap("viridis")),
            orientation="vertical",
            label=str(z),
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
        plt.ylabel(y, weight="black")
        plt.xlabel(x, weight="black")

        # display
        plt.show()
