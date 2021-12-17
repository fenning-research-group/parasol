# This is just a dummy file for now too look at graphing.
#
# def Plot_JV_Param(self,parameter_path):
#     """Plot stats in parameter file"""

#     df = pd.read_csv(parameter_path)

#     # plot preferences
#     mpl.rcParams["axes.linewidth"] = 1.75

#     # dictionary to label plots
#     LabelDict = {
#         "epoch": "Epoch Time",
#         "t": "Time Elapsed (hrs)",
#         "jsc_fwd": "Short Circut Current Density (mA/cm²)",
#         "voc_fwd": "Open Circut Voltage (V)",
#         "ff_fwd": "Fill Factor (%)",
#         "pce_fwd": "Power Conversion Efficiency (%)",
#         "rs_fwd": "Series Resistance (Ω/cm²)",
#         "rsh_fwd": "Shunt Resistance (Ω/cm²)",
#         "rch_fwd": "Channel Resistance (Ω/cm²)",
#         "vmp_fwd": "Maximum Power Point Voltage (V)",
#         "jmp_fwd": "Maximum Power Point Current (mA/cm²)",
#         "pmp_fwd": "Maximum Power Point Power (mW/cm²)",
#         "v_rev": "Voltage (V)",
#         "i_rev": "Current (mA)",
#         "j_rev": "Current Density (mA/cm²)",
#         "p_rev": "Power (mW)",
#         "jsc_rev": "Short Circut Current Density (mA/cm²)",
#         "voc_rev": "Open Circut Voltage (V)",
#         "ff_rev": "Fill Factor (%)",
#         "pce_rev": "Power Conversion Efficiency (%)",
#         "rs_rev": "Series Resistance (Ω/cm²)",
#         "rsh_rev": "Shunt Resistance (Ω/cm²)",
#         "rch_rev": "Channel Resistance (Ω/cm²)",
#         "vmp_rev": "Maximum Power Point Voltage (V)",
#         "jmp_rev": "Maximum Power Point Current (mA/cm²)",
#         "pmp_rev": "Maximum Power Point Power (mW/cm²)",
#     }

#     # plot each value
#     for n in range(df.shape[0]):
#         xval = df[x][n]
#         yval = df[y][n]
#         zval = df[z].values
#         znorm = np.array(
#             (zval - np.nanmin(zval)) / (np.nanmax(zval) - np.nanmin(zval))
#         )
#         colors = plt.cm.viridis(znorm.astype(float))
#         plt.scatter(xval, yval, color=colors[n])

#     # manage colorbar
#     norm = mpl.colors.Normalize(vmin=np.nanmin(zval), vmax=np.nanmax(zval))
#     objs = plt.colorbar(
#         mpl.cm.ScalarMappable(norm=norm, cmap=plt.get_cmap("viridis")),
#         orientation="vertical",
#         label=str(LabelDict[z]),
#     )
#     plt.setp(
#         objs.ax.get_yticklabels(),
#         rotation=-10,
#         fontsize=9,
#         weight="black",
#         snap=True,
#         position=(1, 0),
#     )

#     # label axes
#     plt.ylabel(LabelDict[y], weight="black")
#     plt.xlabel(LabelDict[x], weight="black")

#     # show plot
#     plt.show()
