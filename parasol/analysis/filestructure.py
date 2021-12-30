from datetime import date
import pandas as pd
import numpy as np
import os
import csv
import yaml

# Set yaml name, load controller info
MODULE_DIR = os.path.dirname(__file__)
with open(os.path.join(MODULE_DIR, "..", "hardwareconstants.yaml"), "r") as f:
    constants = yaml.load(f, Loader=yaml.FullLoader)["filestructure"]


class FileStructure:
    def __init__(self):
        self.root_folder = constants["root_dir"]
        self.NUM_MODULES = 24

    def get_subfolders(self, folder):
        return [f.path for f in os.scandir(folder) if f.is_dir()]

    def get_subfiles(self, folder):
        return [f.path for f in os.scandir(folder) if f.is_file()]

    def get_tests(self):

        # get date folders
        self.date_folders = self.get_subfolders(self.root_folder)

        # get test folders
        test_folders = []
        for date_folder in self.date_folders:
            test_folders.append(self.get_subfolders(date_folder))

        return test_folders

    def get_test_subfolders(self, stringpath):
        mpp_folder = [os.path.join(stringpath, "MPP")]

        # path to jv folders --> rootfolder:JV_{module}:
        jv_folders = []
        for i in range(1, self.NUM_MODULES + 1):
            jv_folder = os.path.join(stringpath, "JV_" + str(int(i)))
            if os.path.exists(jv_folder):
                jv_folders.append(jv_folder)

        # path to analyzed folder --> rootfolder:Analyzed
        analyzed_folder = os.path.join(stringpath, "Analyzed")

        return mpp_folder, jv_folders, analyzed_folder

    def map_test_folders(self, test_paths):

        test_dict = {}

        for test_path in test_paths:
            mpp_folder, jv_folders, analyzed_folder = self.get_test_subfolders(
                test_path
            )
            test_dict[test_path] = {
                "MPP": mpp_folder,
                "JV": jv_folders,
                "Analyzed": analyzed_folder,
            }

        return test_dict

    def map_test_files(self, test_folders):

        # create blank dictionary to hold folder: file_paths
        file_dict = {}

        # cycle through folders
        for folder in test_folders:

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

        #    def get_folder_path(self, stringpath):
        """Does it"""

        # xdate_name_index

    def filepath_to_runinfo(self, file_path):
        """Returns runinfo from filepath using filename standardization"""
        file_name = os.path.basename(file_path)
        print("I HAVE ARIVED")
        name_len = (file_name.count("_") + 1) - 5
        name = ""
        i = 1
        while i <= name_len:
            name += file_name.split("_")[i] + "_"
            i += 1
        name = name[:-1]

        run_info = {
            # "scan_number" : file_name.split("_")[-1],  scan number
            # "scan_type" : file_name.split("_")[-2],   scan type
            "module_id": file_name.split("_")[-3],  # module id
            "string_id": file_name.split("_")[-4],  # string id
            "name": name,  # name
            "date": file_name.split("_")[0],  # date
        }

        return run_info

    # Get folder paths

    def get_root_dir(self):
        return self.root_folder

    def get_date_folder(self, startdate):
        """Returns the path to the date folders"""
        date_folder = os.path.join(self.root_folder, startdate)
        return date_folder

    def get_test_folder(self, startdate, name):
        """Returns the path to the test folder"""
        test_folder = os.path.join(self.root_folder, startdate, f"{startdate}_{name}")
        return test_folder

    def get_mpp_folder(self, startdate, name):
        """Returns the path to the MPP folder"""
        mpp_folder = os.path.join(self.get_test_folder(startdate, name), "MPP")
        return mpp_folder

    def get_jv_folders(self, startdate, name, module_channels):
        """Returns the path to the JV folders"""
        jv_folders = []
        for i in module_channels:
            jv_folders.append(
                os.path.join(self.get_test_folder(startdate, name), "JV_" + str(i))
            )
        return jv_folders

    def get_analyzed_folder(self, startdate, name):
        """Returns the path to the analyzed folder"""
        analyzed_folder = os.path.join(
            self.get_test_folder(startdate, name), "Analyzed"
        )
        return analyzed_folder

    # MAY HAVE AN ISSUE BELOW
    def make_module_subdir(self, name, module_channels, startdate):
        """Make subdirectory for saving"""

        # Add date folder
        datefpath = self.get_date_folder(self, startdate)
        if not os.path.exists(datefpath):
            os.mkdir(datefpath)

        # Make base file path for saving
        idx = 0
        basefpath = self.get_test_folder(startdate, name)
        while os.path.exists(basefpath):
            idx += 1
            # basefpath = os.path.join(datefpath, f"{startdate}_{name}_{idx}")
            # not sure if this works
            basefpath += f"_{idx}"
        if idx != 0:
            name += f"_{idx}"
        os.mkdir(basefpath)

        # Make subdirectory for MMP
        mppfpath = self.get_mpp_folder(startdate, name)
        os.mkdir(mppfpath)

        # Make subdirectory for each module
        jvpaths = self.get_jv_folders(startdate, name, module_channels)
        for jvpath in jvpaths:
            os.mkdir(jvpath)

        return basefpath, name

    # Get filenames

    def get_jv_file_name(self, startdate, name, id, module_channel, scan_count):
        """Returns the path to the JV file"""
        jv_file_path = f"{startdate}_{name}_{id}_{module_channel}_JV_{scan_count}.csv"
        return jv_file_path

    def get_mpp_file_name(self, startdate, name, id, scan_count):
        """Returns the path to the MPP file"""
        mpp_file_path = f"{startdate}_{name}_{id}_all_MPP_{scan_count}.csv"
        return mpp_file_path

    def get_analyzed_file_name(self, startdate, name, id, scan_count):
        """Returns the path to the analyzed file"""
        analyzed_file_path = f"{startdate}_{name}_{id}_all_Analyzed_{scan_count}.csv"
        return analyzed_file_path

    # # returns JV folder, MPP folder, and filepaths for creating data

    # def get_jv_folder_runtime(self, d, id, module):
    #     jvfolder = os.path.join(d["_savedir"], f"JV_{module}")
    #     return jvfolder

    # def get_jv_file_runtime(self, d, id, module):
    #     jvfolder = os.path.join(d["_savedir"], f"JV_{module}")
    #     fpath = os.path.join(
    #         jvfolder,
    #         f"{d['start_date']}_{d['name']}_{id}_{module}_JV_{d['jv']['scan_count']}.csv",
    #     )
    #     return fpath

    # def get_mpp_folder_runtime(self, d, id):
    #     mppfolder = os.path.join(d["_savedir"], "MPP")
    #     return mppfolder

    # def get_mpp_file_runtime(self, d, id):
    #     mppfolder = os.path.join(d["_savedir"], "MPP")
    #     fpath = os.path.join(
    #         mppfolder,
    #         f"{d['start_date']}_{d['name']}_{id}_all_MPP_1.csv",
    #     )
    #     return fpath


# root
# root:dates
# root:dates:xdate_name:
# root:dates:xdate_name:JV_strid:<date>_<Name>_<strid>_<modid>_JV_<scannum>.csv
# root:dates:xdate_name:MPP:<date>_<Name>_<strid>_MPP_1.csv
# root:dates:xdate_name:Analyzed:
