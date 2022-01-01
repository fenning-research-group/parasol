import os
import yaml

# Set yaml name, load controller info
MODULE_DIR = os.path.dirname(__file__)
with open(os.path.join(MODULE_DIR, "hardwareconstants.yaml"), "r") as f:
    constants = yaml.load(f, Loader=yaml.FullLoader)["filestructure"]


class FileStructure:
    """FileStructure package for PARASOL"""

    def __init__(self) -> None:
        """Initializes the FileStructure class"""

        self.root_folder = constants["root_dir"]
        self.NUM_MODULES = 24

    # Get folder paths given inputs, make paths

    def get_root_dir(self) -> str:
        """Returns the root directory

        Returns:
            str: path to root directory
        """
        return self.root_folder

    def get_date_folder(self, startdate: str) -> str:
        """Returns the path to the date folder

        Args:
            startdate (str): startdate in YYYYMMDD format

        Returns:
            str: path to date folder
        """

        date_folder = os.path.join(self.root_folder, startdate)
        return date_folder

    def get_test_folder(self, startdate: str, name: str) -> str:
        """Returns the path to the test folder

        Args:
            startdate (str): startdate in YYYYMMDD format
            name (str): name of test

        Returns:
            str: path to test folder
        """

        test_folder = os.path.join(self.root_folder, startdate, f"{startdate}_{name}")
        return test_folder

    def get_mpp_folder(self, startdate: str, name: str) -> str:
        """Returns the path to the MPP folder

        Args:
            startdate (str): startdate in YYYYMMDD format
            name (str): name of test

        Returns:
            str: path to MPP folder
        """

        mpp_folder = os.path.join(self.get_test_folder(startdate, name), "MPP")
        return mpp_folder

    def get_jv_folder(self, startdate: str, name: str, module_channel: int) -> str:
        """Returns the path to the JV folder

        Args:
            startdate (str): startdate in YYYYMMDD format
            name (str): name of test
            module_channel (int): module channel

        Returns:
            str: path to JV folder
        """
        jv_folder = os.path.join(
            self.get_test_folder(startdate, name), "JV_" + str(module_channel)
        )
        return jv_folder

    def get_analyzed_folder(self, startdate: str, name: str) -> str:
        """Returns the path to the Analyzed folder

        Args:
            startdate (str): startdate in YYYYMMDD format
            name (str): name of test

        Returns:
            str: path to Analyzed folder
        """
        analyzed_folder = os.path.join(
            self.get_test_folder(startdate, name), "Analyzed"
        )
        return analyzed_folder

    # Make test folders given inputs

    def make_module_subdir(
        self, name: str, module_channels: list, startdate: str
    ) -> str:
        """Makes JV, MPP, and Analyzed subdirectories for a given test

        Args:
            startdate (str): startdate in YYYYMMDD format
            name (str): name of test
            module_channels (list[int]): module channels

        Returns:
            list[str]: paths to JV folders
        """

        # Add date folder
        datefpath = self.get_date_folder(startdate)
        if not os.path.exists(datefpath):
            os.mkdir(datefpath)

        # Make base file path for saving
        idx = 0
        basefpath = self.get_test_folder(startdate, name)
        while os.path.exists(basefpath):
            idx += 1
            basefpath = self.get_test_folder(startdate, name) + f"_{idx}"
        if idx != 0:
            name += f"_{idx}"
        os.mkdir(basefpath)

        # Make subdirectory for MMP
        mppfpath = self.get_mpp_folder(startdate, name)
        os.mkdir(mppfpath)

        # Make subdirectory for each module
        for module in module_channels:
            jvpath = self.get_jv_folder(startdate, name, module)
            os.mkdir(jvpath)

        return basefpath, name

    # Get filenames given inputs, make paths

    def get_jv_file_name(
        self, startdate: str, name: str, id: int, module_channel: int, scan_count: int
    ) -> str:
        """Returns the JV file name

        Args:
            startdate (str): startdate in YYYYMMDD format
            name (str): name of test
            id (int): test id
            module_channel (int): module channel
            scan_count (int): scan count

        Returns:
            str: name of JV file
        """

        jv_file_path = f"{startdate}_{name}_{id}_{module_channel}_JV_{scan_count}.csv"
        return jv_file_path

    def get_mpp_file_name(
        self, startdate: str, name: str, id: int, scan_count: int
    ) -> str:
        """Returns the JV file name

        Args:
            startdate (str): startdate in YYYYMMDD format
            name (str): name of test
            id (int): test id
            scan_count (int): scan count

        Returns:
            str: name of MPP file
        """

        mpp_file_path = f"{startdate}_{name}_{id}_all_MPP_1.csv"
        return mpp_file_path

    def get_analyzed_file_name(self, startdate: str, name: str, id: int) -> str:
        """Returns the Analyzed file name

        Args:
            startdate (str): startdate in YYYYMMDD format
            name (str): name of test
            id (int): test id

        Returns:
            str: name of Analyed file
        """
        analyzed_file_path = f"{startdate}_{name}_{id}_all_Analyzed_1.csv"
        return analyzed_file_path

    # Get useful save information from the file name, make runinfo dict

    def filepath_to_runinfo(self, file_path: str) -> dict:
        """Returns runinfo from filepath using filename standardization

        Args:
            file_path (str): filepath to file

        Returns:
            dict: runinfo ["module_id", "string_id", "name", "date"]
        """

        file_name = os.path.basename(file_path)
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

    # Map files and folders in root directory, make file_dict and folder_dict

    def get_subfolders(self, folder: str) -> list:
        """Returns list of subfolders in folder

        Args:
            folder (str): path to folder

        Returns:
            list[str]: paths to subfolders
        """
        return [f.path for f in os.scandir(folder) if f.is_dir()]

    def get_subfiles(self, folder: str) -> list:
        """Returns list of subfiles in folder

        Args:
            folder (str): path to folder

        Returns:
            list[str]: paths to subfiles
        """
        return [f.path for f in os.scandir(folder) if f.is_file()]

    def get_tests(self) -> list:
        """Returns a list of all test paths in root directory

        Returns:
            list[str]: paths to all test folders
        """
        # get date folders
        self.date_folders = self.get_subfolders(self.root_folder)

        # get test folders
        test_folders = []
        for date_folder in self.date_folders:
            test_folders.append(self.get_subfolders(date_folder))

        return test_folders

    def get_test_subfolders(self, stringpath: str) -> str:
        """Returns list of subfolders in test folder

        Args:
            stringpath (str): path to test folder

        Returns:
            str: path to MPP folder
            list[str]: paths to JV folders
            str: path to analyzed folder
        """
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

    def map_test_folders(self, test_paths: list) -> dict:
        """Creates a dictionary maping test folders to their subfolders

        Args:
            test_paths (list[str]): paths to test folders

        Returns:
            dict: test_dict[test_path] = [mpp_path, jv_paths, analyzed_path]
        """

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

    def map_test_files(self, test_folders: list) -> dict:
        """Creates a dictionary maping test subfolders to their subfiles

        Args:
            test_folders (list[str]): path to a given subfolder (e.g. JV)

        Returns:
            dict: file_dict[folder] = [file_paths]
        """

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
