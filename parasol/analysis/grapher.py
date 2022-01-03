import numpy as np
import pandas as pd
import matplotlib as mpl
import matplotlib.pyplot as plt

from parasol.filestructure import FileStructure


class Grapher:
    """Grapher package for PARASOL"""

    def __init__(self) -> None:
        """Initializes Grapher class"""

        # Load filstructure package to manage JV files
        self.filestructure = FileStructure()

        # Get path to root directory (test folder)
        self.rootdir = self.filestructure.get_root_dir()

        # Define dictionaries for plotting
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

    def plot_x_v_ys(self, df: pd.DataFrame, x: str, ys: list) -> None:
        """Plots x vs. y for a set of ys (1 graph)

        Args:
            df (pd.DataFrame): dataframe containing x and y values to plot
            x (str): x header name
            ys (list[str]): y header names
        """

        # Get x values
        x_vals = df[x]

        # Get y labels
        y_label = ""

        # Cycle through y labels
        for y_param in ys:

            # for each parameter, plot all data
            y_vals = df[y_param]
            for i in range(len(y_vals)):
                plt.scatter(x_vals[i], y_vals[i])
                y_label += str(y_param) + " / "

        # label axes, show plot
        y_label = y_label[:-3]
        plt.ylabel(y_label, weight="black")
        plt.xlabel(x, weight="black")
        plt.show()

    # Plot JV scans for a single module

    def plot_module_jvs(self, jvfolder: str) -> None:
        """Plot JVs in given JV folder

        Args:
            jvfolder (str): path to JV folder
        """
        # create dictionary where dict[testfolder] = list of jv files
        jv_dict = self.filestructure.map_test_files([jvfolder])

        # Feed file into the dictionary to get a list of JV files
        jv_file_paths = jv_dict[jvfolder]

        # Plot JVs for each module
        self.plot_jvs(jv_file_paths)

    def plot_jvs(self, jvfiles: list) -> None:
        """Plot JVs for input JV files

        Args:
            jvfiles (list[str]): paths to JV files
        """

        # Load JV files
        (
            all_t,
            all_v,
            all_j_fwd,
            all_p_fwd,
            all_j_rev,
            all_p_rev,
        ) = self.analysis.load_jv_files(jvfiles)

        # Create linear colormap that spans the number of files
        colors = plt.cm.viridis(np.linspace(0, 1, len(jvfiles)))

        # Make time data numpy array, calc time elapsed
        all_t = np.array(all_t)
        all_t_elapsed = all_t - all_t[0]

        # Plot FWD and REV curves, REV with --
        for jvpair in range(len(all_t_elapsed)):
            plt.plot(all_v[jvpair], all_j_fwd[jvpair], color=colors[jvpair])
            plt.plot(all_v[jvpair], all_j_rev[jvpair], "--", color=colors[jvpair])

        # Label axes and show plot
        plt.ylabel("J (mA/cm2)", weight="black")
        plt.xlabel("V (V)", weight="black")
        plt.show()

    # Plot x v y with color axis as different devices
    # Plot x v y with color axis another parameter (z)

    def plot_xy_scalars(self, paramfiles: list, x: str, y: str) -> None:
        """Plot x vs. y for a set of scalar files

        Args:
            paramfiles (list[str]): path to file containing x and y values (scalars)
            x (str): x header name
            y (str): y header name
        """

        # mpl.rcParams["axes.linewidth"] = 1.75

        # Cycle through paramfiles
        for paramfile in paramfiles:

            # Read in dataframe
            df = pd.read_csv(paramfile)

            # Get x and y values, add to plot
            x_vals = df[x]
            y_vals = df[y]
            plt.scatter(x_vals, y_vals)

        # Label axes and show plot
        plt.ylabel(y, weight="black")
        plt.xlabel(x, weight="black")
        plt.show()

    def plot_xy2_scalars(self, paramfiles: list, x: str, ys: list) -> None:
        """Plots x vs. y for a set of scalar files

        Args:
            paramfiles (list[str]): paths to file containing x and y values (scalars)
            x (str): x header name
            ys (list[str]): y header names
        """

        # mpl.rcParams["axes.linewidth"] = 1.75

        # Cycle through paramfiles
        for paramfile in paramfiles:

            # Read in dataframe
            df = pd.read_csv(paramfile)

            # Get x values
            x_vals = df[x]

            # Cycle through y values, and add (x,y) to plot
            for idx, y in enumerate(ys):
                y_vals = df[y]
                plt.scatter(x_vals, y_vals, marker=self.fwd_rev_cursor_dict[idx])

        # Label axes and show plot
        ylab = ""
        for y in ys:
            ylab += str(y) + " / "
        ylab = ylab[:-3]
        plt.ylabel(ylab, weight="black")
        plt.xlabel(x, weight="black")
        plt.show()

    def plot_xyz_scalar(self, paramfile: str, x: str, y: str, z: str) -> None:
        """Plots x vs. y with z colorbar for a set of scalar files

        Args:
            paramfile (str): path to file containing x, y, and z values (scalars)
            x (str): x header name
            y (str): y header name
            z (str): z header name
        """

        # Load datafolder path
        df = pd.read_csv(paramfile)

        # mpl.rcParams["axes.linewidth"] = 1.75

        # cycle through # of points in each array
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

            # Plot (x,y) with colorbar
            plt.scatter(xval, yval, color=colors[n])

        # Manage colorbar
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

        # Label axes and show plot
        plt.ylabel(y, weight="black")
        plt.xlabel(x, weight="black")
        plt.show()
