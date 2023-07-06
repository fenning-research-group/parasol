import numpy as np
import pandas as pd
import matplotlib as mpl
import matplotlib.pyplot as plt
import math

from parasol.filestructure import FileStructure
from parasol.analysis.analysis import Analysis


class Grapher:
    """Grapher package for PARASOL"""

    def __init__(self) -> None:
        """Initializes Grapher class"""

        # Load packages
        self.filestructure = FileStructure()
        self.analysis = Analysis()

        # Define dictionaries for plotting
        self.variable_dict = {
            "Time": "Time (Epoch)",
            "Time Elapsed": "Time Elapsed (s)",
            "FWD Jsc": "FWD Jsc (mA/cm2)",
            "FWD Voc": "FWD Voc (V)",
            "FWD FF": "FWD FF (%)",
            "FWD PCE": "FWD PCE (%)",
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
            "MPPT MPP": "MPPT MPP (mW/cm2)",
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

    # Plot Statistics for a single dataframe with x and y labels --> used in check test

    def plot_x_v_ys(self, df: pd.DataFrame, x: str, ys: list, **plt_kwargs) -> None:
        """Plots x vs. ys in a singular dataframe on one graph

        Args:
            df (pd.DataFrame): dataframe containing x and y values to plot
            x (str): x header name
            ys (list[str]): y header names
        """

        # Get x values
        x_vals = df[x]

        # Create blank string to append y labels
        y_label = ""

        # Cycle through y labels
        for y_param in ys:
            # For each parameter, plot x versus y
            y_vals = df[y_param]
            for i in range(len(y_vals)):
                # If FWD/REV data plot using fwd/rev arrows, otherwise plot using dots
                if "FWD" in y_param:
                    plt.scatter(
                        x_vals[i],
                        y_vals[i],
                        marker=self.fwd_rev_cursor_dict[0],
                        **plt_kwargs,
                    )
                elif "REV" in y_param:
                    plt.scatter(
                        x_vals[i],
                        y_vals[i],
                        marker=self.fwd_rev_cursor_dict[1],
                        **plt_kwargs,
                    )
                else:
                    plt.scatter(x_vals[i], y_vals[i], **plt_kwargs)

                # Append y label to string
                y_label += str(y_param) + " / "

        # Remove ending of y label
        y_label = y_label[:-3]

        # Set labels
        plt.ylabel(y_label, weight="black")
        plt.xlabel(x, weight="black")
        plt.show()

    # Plot JV/MPPT scans for a single module folder

    def plot_module_jvs(self, jvfolder: str, **plt_kwargs) -> None:
        """Plot JVs in given JV folder

        Args:
            jvfolder (str): path to JV folder
        """

        # Create dictionary where dict[testfolder] = list of JV files
        jv_dict = self.filestructure.map_test_files([jvfolder])

        # Feed file into the dictionary to get a list of JV files
        jv_file_paths = jv_dict[jvfolder]

        # Plot JVs for each module
        self.plot_jvs(jv_file_paths, **plt_kwargs)

    def plot_string_mpp(self, mppfolder: str, **plt_kwargs) -> None:
        """Plot MPP information in given MPP folder

        Args:
            mppfolder (str): path to MPP folder
        """

        # Create dictionary where dict[testfolder] = list of mpp files
        mpp_dict = self.filestructure.map_test_files([mppfolder])

        # Feed file into the dictionary to get a list of MPP files
        mpp_file_paths = mpp_dict[mppfolder]

        # Plot MPPs for each module
        self.plot_mpps(self, mpp_file_paths, None, **plt_kwargs)

    def plot_jvs(self, jvfiles: list, **plt_kwargs) -> None:
        """Plot JVs for input JV files

        Args:
            jvfiles (list[str]): paths to JV files
        """

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
        ) = self.analysis.load_jv_files(jvfiles)

        # Make time data numpy array, calc time elapsed
        all_t = np.array(all_t)
        all_t_elapsed = all_t - all_t[0]

        # Create linear colormap that spans the number of files
        colors = plt.cm.viridis(np.linspace(0, 1, len(jvfiles)))

        # Get testname for title
        testname = self.filestructure.filepath_to_runinfo(jvfiles[0])["name"]
        testdate = self.filestructure.filepath_to_runinfo(jvfiles[0])["date"]
        titlestr = testname + "( " + testdate + " )"

        # Plot FWD and REV curves, REV with --
        for jvpair in range(len(all_t_elapsed)):
            plt.plot(
                all_vm_fwd[jvpair],
                all_j_fwd[jvpair],
                color=colors[jvpair],
                **plt_kwargs,
            )
            plt.plot(
                all_vm_rev[jvpair],
                all_j_rev[jvpair],
                "--",
                color=colors[jvpair],
                **plt_kwargs,
            )

        # Create legend for 4 files to show change over time
        if len(jvfiles) >= 4:
            l1 = 0
            l2 = math.floor((1 / 3) * (len(all_j_fwd) - 1))
            l3 = math.ceil((2 / 3) * (len(all_j_fwd) - 1))
            l4 = len(all_j_fwd) - 1
            plt.legend(
                [all_j_fwd[l1], all_j_fwd[l2], all_j_fwd[l3], all_j_fwd[l4]],
                [
                    all_t_elapsed[l1],
                    all_t_elapsed[l2],
                    all_t_elapsed[l3],
                    all_t_elapsed[l4],
                ],
                loc="upper left",
            )

        # Customize plot and show
        plt.ylabel("J (mA/cm2)", weight="black")
        plt.xlabel("V (V)", weight="black")
        plt.title(titlestr)
        plt.show()

    # These functions take axes and plot on them

    def plot_mpps(self, mppfiles: list, ax: plt.axes = None, **plt_kwargs) -> plt.axes:
        """Plots MPPs for input MPP files

        Args:
            mppfiles (list[str]): list of MPP files (same device)
            ax (plt.axes): axes
            **plt_kwargs : additional plot options

        Returns:
            plt.ax: plotted axes
        """

        # If not passed axes, use last set
        if ax is None:
            ax = plt.gca()

        if len(mppfiles) == 0:
            return ax

        # Load MPP files
        (
            all_t,
            all_vm,
            all_v,
            all_i,
            all_j,
            all_p,
        ) = self.analysis.load_mpp_files(mppfiles)

        # Calculate time elapsed
        t1 = all_t
        t_elapsed = t1 - t1[0]

        # Plot
        ax.plot(
            t_elapsed,
            all_p,
            **plt_kwargs,
        )

        # Customize plot and show
        ax.set_ylabel("MPPT MPP (mW/cm2)", weight="black")
        ax.set_xlabel("Time Elapsed (sec)", weight="black")

        return ax

    def plot_xy_scalars(
        self, paramfiles: list, x: str, y: str, ax: plt.axes = None, **plt_kwargs
    ) -> plt.axes:
        """Plot x vs. y for a set of scalar files

        Args:
            paramfiles (list[str]): path to file containing x and y values (scalars)
            x (str): x header name
            y (str): y header name
            ax (plt.axes): axes
            **plt_kwargs : additional plot options

        Returns:
            plt.ax: plotted axes
        """

        # If not passed axes, use last set
        if ax is None:
            ax = plt.gca()

        if len(paramfiles) == 0:
            return ax

        # Cycle through paramfiles
        for paramfile in paramfiles:
            # Read in dataframe
            df = pd.read_csv(paramfile)

            # Get x and y values, add to plot
            x_vals = df[x]
            y_vals = df[y]
            ax.scatter(x_vals, y_vals, **plt_kwargs)

        # Label axes, no title
        ax.set_ylabel(y, weight="black")
        ax.set_xlabel(x, weight="black")

        return ax

    def plot_xy2_scalars(
        self, paramfiles: list, x: str, ys: list, ax: plt.axes = None, **plt_kwargs
    ) -> plt.axes:
        """Plots x vs. y for a set of scalar files

        Args:
            paramfiles (list[str]): paths to file containing x and y values (scalars)
            x (str): x header name
            ys (list[str]): y header names
            ax (plt.axes): axes
            **plt_kwargs : additional plot options

        Returns:
            plt.ax: plotted axes
        """

        # If not passed axes, use last set
        if ax is None:
            ax = plt.gca()

        if len(paramfiles) == 0:
            return ax

        # Cycle through paramfiles
        for paramfile in paramfiles:
            # Read in dataframe
            df = pd.read_csv(paramfile)

            # Get x values
            x_vals = df[x]

            # Cycle through y values, and add (x,y) to plot
            for idx, y in enumerate(ys):
                y_vals = df[y]
                ax.scatter(
                    x_vals, y_vals, marker=self.fwd_rev_cursor_dict[idx], **plt_kwargs
                )

        # Label axes, no title
        ylab = ""
        for y in ys:
            ylab += str(y) + " / "
        ylab = ylab[:-3]
        ax.set_ylabel(ylab, weight="black")
        ax.set_xlabel(x, weight="black")

        return ax

    def plot_xyz_scalar(
        self, paramfile: str, x: str, y: str, z: str, ax: plt.axes = None, **plt_kwargs
    ) -> plt.axes:
        """Plots x vs. y with z colorbar for a set of scalar files

        Args:
            paramfile (str): path to file containing x, y, and z values (scalars)
            x (str): x header name
            y (str): y header name
            z (str): z header name
            ax (plt.axes): axes
            **plt_kwargs : additional plot options

        Returns:
            plt.ax: plotted axes
        """

        # If not passed axes, use last set
        if ax is None:
            ax = plt.gca()

        # Load datafolder path
        df = pd.read_csv(paramfile)

        # Cycle through # of points in each array
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
            ax.scatter(xval, yval, color=colors[n], **plt_kwargs)

        # Manage colorbar
        norm = mpl.colors.Normalize(vmin=np.nanmin(zval), vmax=np.nanmax(zval))
        objs = plt.colorbar(
            mpl.cm.ScalarMappable(norm=norm, cmap=plt.get_cmap("viridis")),
            ax=ax,
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
        ax.set_ylabel(y, weight="black")
        ax.set_xlabel(x, weight="black")

        return ax


# TODO: plot_mpps take plot axes, plot_jvs should as well. make things function better on either axes or figure