import numpy as np
import pandas as pd
import matplotlib as mpl
import matplotlib.pyplot as plt
import yaml
import os


# Set yaml name, load controller info
MODULE_DIR = os.path.dirname(__file__)
with open(os.path.join(MODULE_DIR, "..", "hardwareconstants.yaml"), "r") as f:
    constants = yaml.load(f, Loader=yaml.FullLoader)["controller"]


class ParasolGrapher:
    def __init__(self):
        """Opens in root directory (same as parasol)"""

        # Path to general data
        self.rootdir = constants["root_dir"]

        # Variables
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

    def plot_JV(self, jvfolder):
        print("pass")

    def plot_x_v_ys(self, df_dict, x, ys):
        """Plots x vs ys for a dict"""

        # make dataframe for datafolder dictionary
        df = pd.DataFrame.from_dict(df_dict)

        # get x list
        x_vals = df[x]

        # cycle through the multiple y parameters
        for y_param in ys:

            y_vals = df[y_param]

            # for each parameter, plot all data
            for i in range(len(y_vals)):
                plt.scatter(x_vals[i], y_vals[i])

        plt.show()

    def plot_XY_scalars(self, paramfiles, x, y):
        """Plots x vs y for set of paramfiles"""
        print("pass")

    def plot_XYZ_scalar(self, paramfile, x, y, z):
        """Plots x vs y with z colorbar for paramfile"""

        # load datafolder path
        df = pd.read_csv(paramfile)

        # plot preferences
        mpl.rcParams["axes.linewidth"] = 1.75

        for n in range(df.shape[0]):

            # Get values for x and y
            xval = df[self.variable_dict[x]][n]
            yval = df[self.variable_dict[y]][n]

            # Get values for color bar
            zval = df[self.variable_dict[z]].values
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
            label=str(self.variable_dict[z]),
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
        plt.ylabel(self.variable_dict[y], weight="black")
        plt.xlabel(self.variable_dict[x], weight="black")

        # display
        plt.show()
