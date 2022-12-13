import os
import yaml
import datetime

# Set module directory, import constants from yaml file
MODULE_DIR = os.path.dirname(__file__)
with open(os.path.join(MODULE_DIR, "hardwareconstants.yaml"), "r") as f:
    constants = yaml.safe_load(f)["filestructure"]


class FileStructure:
    """FileStructure package for PARASOL"""

    def __init__(self) -> None:
        """Initializes the FileStructure class"""

        # Load constants
        self.root_folder = constants["root_dir"]
        self.analysis_folder = constants["analysis_dir"]
        self.NUM_MODULES = constants["num_modules"]

        if not os.path.exists(self.root_folder):
            os.mkdir(self.root_folder)

        # Create paths to cell characterization, environment monitoring, and logging folders
        self.characterization_folder = os.path.join(
            self.root_folder, "Characterization"
        )
        self.environment_folder = os.path.join(self.root_folder, "Environment")
        self.log_folder = os.path.join(self.root_folder, "Logs")

    # Get base folder directories given inputs, make paths

    def get_root_dir(self) -> str:
        """Returns the root directory

        Returns:
            str: path to root directory
        """

        return self.root_folder

    def get_characterization_dir(self) -> str:
        """Returns the path to the characterization directory

        Returns:
            str: path to characterization directory
        """

        return self.characterization_folder

    def get_environment_dir(self) -> str:
        """Returns the path to the monitor directory

        Returns:
            str: path to monitor directory
        """

        return self.environment_folder

    def get_log_dir(self) -> str:
        """Returns the path to the log directory

        Returns:
            str: path to log directory
        """

        return self.log_folder

    def get_analysis_dir(self) -> str:
        """Returns the path to the analysis directory

        Returns:
            str: path to analysis directory
        """

        return self.analysis_folder

    # Get filepaths for folders
    # ROOT:DATE:TEST:MPP:
    #               :JV:
    #               :Analyzed:
    # ROOT:ENVIRONMENT:xYYYY:

    def get_date_folder(self, startdate: str) -> str:
        """Returns the path to the date folder

        Args:
            startdate (str): startdate in xYYYYMMDD format

        Returns:
            str: path to date folder
        """

        date_folder = os.path.join(self.characterization_folder, startdate)

        return date_folder

    def get_test_folder(self, startdate: str, name: str) -> str:
        """Returns the path to the test folder

        Args:
            startdate (str): startdate in xYYYYMMDD format
            name (str): name of test

        Returns:
            str: path to test folder
        """

        test_folder = os.path.join(
            self.characterization_folder, startdate, f"{startdate}_{name}"
        )

        return test_folder

    def get_mpp_folder(self, startdate: str, name: str) -> str:
        """Returns the path to the MPP folder

        Args:
            startdate (str): startdate in xYYYYMMDD format
            name (str): name of test

        Returns:
            str: path to MPP folder
        """

        mpp_folder = os.path.join(self.get_test_folder(startdate, name), "MPP")

        return mpp_folder

    def get_jv_folder(self, startdate: str, name: str, module_channel: int) -> str:
        """Returns the path to the JV folder

        Args:
            startdate (str): startdate in xYYYYMMDD format
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
            startdate (str): startdate in xYYYYMMDD format
            name (str): name of test

        Returns:
            str: path to Analyzed folder
        """

        analyzed_folder = os.path.join(
            self.get_test_folder(startdate, name), "Analyzed"
        )

        return analyzed_folder

    def get_environment_folder(self, cdate: str) -> str:
        """Returns the path to the environment date folder

        Args:
            sdate (str): date in xYYYYMMDD format

        Returns:
            str: path to date folder
        """

        env_dir = self.get_environment_dir()
        env_folder = cdate[0:5]

        folder_path = os.path.join(env_dir, env_folder)

        return folder_path

    # Make MPP, JV, and Analyed folders given inputs

    def make_module_subdir(
        self, name: str, module_channels: list, startdate: str
    ) -> str:
        """Makes JV, MPP, and Analyzed subdirectories for a given test

        Args:
            name (str): name of test
            module_channels (list[int]): module channels
            startdate (str): startdate in xYYYYMMDD format

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

    # Get filepaths to files given inputs (for saving)

    def get_jv_file_name(
        self, startdate: str, name: str, id: int, module_channel: int, scan_count: int
    ) -> str:
        """Returns the JV file name

        Args:
            startdate (str): startdate in xYYYYMMDD format
            name (str): name of test
            id (int): test id
            module_channel (int): module channel
            scan_count (int): scan count

        Returns:
            str: name of JV file
        """

        # Build filename
        jv_file_name = f"{startdate}_{name}_{id}_{module_channel}_JV_{scan_count}.csv"

        return jv_file_name

    def get_mpp_file_name(
        self, startdate: str, name: str, id: int, scan_count: int
    ) -> str:
        """Returns the JV file name

        Args:
            startdate (str): startdate in xYYYYMMDD format
            name (str): name of test
            id (int): test id
            scan_count (int): scan count

        Returns:
            str: name of MPP file
        """

        # Build filename
        mpp_file_name = f"{startdate}_{name}_{id}_all_MPP_{scan_count}.csv"

        return mpp_file_name

    def get_analyzed_file_name(
        self, startdate: str, name: str, id: int, module_channel: int
    ) -> str:
        """Returns the Analyzed file name

        Args:
            startdate (str): startdate in xYYYYMMDD format
            name (str): name of test
            id (int): test id
            module_channel (int): module channel

        Returns:
            str: name of Analyed file
        """

        # Build filename
        analyzed_file_name = f"{startdate}_{name}_{id}_{module_channel}_Scalars_1.csv"

        return analyzed_file_name

    def get_environment_file_name(self, cdate: str) -> str:
        """Returns the environment file name xYYYYMMDD_epochtime.csv

        Args:
            cdate (str): date in xYYYYMMDD format

        Returns:
            str: name of environment file
        """

        # Create prefix for file name (xYYYYMMDD)
        dtyear = int(cdate[1:5])
        dtmonth = int(cdate[5:7])
        dtday = int(cdate[7:9])

        # Create epoch pointer to this date
        epoch = int(datetime.datetime(dtyear, dtmonth, dtday, 0, 0).timestamp())

        # Build filename
        env_file_name = f"{cdate}_{epoch}.csv"

        return env_file_name

    # Get useful save information from the file name, make runinfo dict

    def filepath_to_runinfo(self, file_path: str) -> dict:
        """Returns runinfo from filepath using filename standardization

        Args:
            file_path (str): filepath to file

        Returns:
            dict: runinfo ["module_id", "string_id", "name", "date"]
        """

        # Get file name, pull out name of file (account for _#)
        file_name = os.path.basename(file_path)
        name_len = (file_name.count("_") + 1) - 5
        name = ""
        i = 1
        while i <= name_len:
            name += file_name.split("_")[i] + "_"
            i += 1
        name = name[:-1]

        # Get other run info
        run_info = {
            # "scan_number" : file_name.split("_")[-1],  skip scan number
            # "scan_type" : file_name.split("_")[-2],   skip scan type
            "module_id": file_name.split("_")[-3],  # module id
            "string_id": file_name.split("_")[-4],  # string id
            "name": name,  # name
            "date": file_name.split("_")[0],  # date
        }

        return run_info

    # Get Folders in any file and files in any file 

    def get_subfolders(self, folder: str, partial = None) -> list:
        """Returns list of subfolders in folder

        Args:
            folder (str): path to folder
            partial (str = None): parial name requirement

        Returns:
            list[str]: paths to subfolders
        """
        list1 = [f.path for f in os.scandir(folder) if f.is_dir()]

        if partial is None:
            return_list = list1
        else:
            return_list = [folder for folder in list1 if partial in folder]

        return return_list

    def get_subfiles(self, folder: str, partial = None) -> list:
        """Returns list of subfiles in folder

        Args:
            folder (str): path to folder
            partial (str = None): parial name requirement

        Returns:
            list[str]: paths to subfiles
        """
        list1 = [f.path for f in os.scandir(folder) if f.is_file()]
        
        if partial is None:
            return_list = list1
        else:
            return_list = [file for file in list1 if partial in file]

        return return_list

    # Get test folders and subfolders (MPP, Analyzed, JV), Get env monitoring folders

    def get_tests(self, rootdir=None) -> list:
        """Returns a list of all test paths in root directory

        Args:
            rootdir[str]: path to root directory

        Returns:
            list[str]: paths to all test folders
        """

        # If no root directory specified, use default
        if rootdir is None:
            characterization_folder = self.characterization_folder
        else:
            characterization_folder = rootdir

        # Get date folders
        self.date_folders = self.get_subfolders(characterization_folder)

        # Make blank list for folders
        test_folders = []

        # Cycle through each date folder
        for date_folder in self.date_folders:

            # Get a list of tests in the date folder
            test_folders_for_date = self.get_subfolders(date_folder)

            # Append to list
            for test_folder_for_date in test_folders_for_date:
                test_folders.append(test_folder_for_date)

        return test_folders

    def get_test_subfolders(self, stringpath: str) -> list:
        """Returns list of subfolders in test folder

        Args:
            stringpath (str): path to test folder

        Returns:
            list[str]: path to MPP folder
            list[str]: paths to JV folders
            list[str]: path to analyzed folder
        """

        # Get path to MPP folder
        mpp_folder = [os.path.join(stringpath, "MPP")]

        # Get path to JV folders
        jv_folders = []
        for i in range(1, self.NUM_MODULES + 1):
            jv_folder = os.path.join(stringpath, "JV_" + str(int(i)))
            if os.path.exists(jv_folder):
                jv_folders.append(jv_folder)

        # Get path to analyzed folder
        analyzed_folder = [os.path.join(stringpath, "Analyzed")]

        return mpp_folder, jv_folders, analyzed_folder

    def get_env_folders(self, envdir=None) -> list:
        """Returns a list of all test paths in root directory

        Args:
            envdir[str]: path to root directory

        Returns:
            list[str]: paths to all test folders
        """

        # Get path to enviornment root directory
        if envdir is None:
            env_folder = self.environment_folder
        else:
            env_folder = envdir

        # Get path to enviroment folders inside it
        folders = self.get_subfolders(env_folder)

        return folders

    # Map folders and files in test subdirectory and files in env subdirectory

    def map_test_folders(self, test_paths: list) -> dict:
        """Creates a dictionary mapping test folders to their subfolders

        Args:
            test_paths (list[str]): paths to test folders

        Returns:
            dict: test_dict[test_path] = [mpp_path, jv_paths, analyzed_path]
        """

        # Create dictionary mapping MPP, JV, and Anlayzed folders to test folder
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
        """Creates a dictionary mapping test subfolders to their subfiles

        Args:
            test_folders (list[str]): path to a given subfolder (e.g. JV)

        Returns:
            dict: file_dict[folder] = [file_paths]
        """

        # Create blank dictionary to hold folder: file_paths
        file_dict = {}

        # Cycle through folders
        for folder in test_folders:

            # Initialize lists
            scan_numbers = []
            paths_chronological = []

            # Grab list of files in folder
            files = self.get_subfiles(folder)

            # For each file, create list of scan numbers
            for file in files:
                scan_numbers.append(int((file.split("_")[-1]).split(".")[0]))

            # Sort files by scan number, create paths to files
            files_chronological = [x for _, x in sorted(zip(scan_numbers, files))]
            for file in files_chronological:
                paths_chronological.append(os.path.join(folder, file))

            # Create dictionary basefolder : file_paths
            file_dict[folder] = paths_chronological

        return file_dict

    def map_env_files(self, env_folders: list, startdate: str, enddate: str) -> dict:
        """Creates a dictionary maping test folders to their subfolders

        Args:
            env_folders (list[str]): paths to env folders
            startdate (str): start date in xYYYYMMDD format
            enddate (str): end date in xYYYYMMDD format
        Returns:
            dict: file_dict[folder] = [file_paths]
        """

        # Create dictionary
        env_dict = {}

        # Grab start and end date
        start_date = float(startdate[1:9])
        end_date = float(enddate[1:9])

        # Cycle through enviroment folders (dates)
        for env_folder in env_folders:

            # Initialize lists
            dates = []
            paths_chronological = []

            # Grab list of files in folder
            files = self.get_subfiles(env_folder)

            # Sort files by date, create paths to files
            for file in files:
                filename = os.path.basename(file)
                dates.append(int(filename[1:9]))
            files_chronological = [x for _, x in sorted(zip(dates, files))]

            # Check if its between dates
            for idx, file in enumerate(files_chronological):
                if start_date <= dates[idx] <= end_date:
                    paths_chronological.append(os.path.join(env_folder, file))

            # Set entry in dictionary where key is folder and value is list of files
            env_dict[env_folder] = paths_chronological

        return env_dict

    # Use previous commands to get files for given test

    def get_files(self, test_folders: str, filetype="Analyzed") -> str:
        """Returns a list of all files in test folders

        Args:
            test_folders (list[str]): list of test folders
            filetype (string): either "Analyzed", "JV", or "MPP"

        Returns:
            list[list[str]]: list of file paths seperated by test
        """

        # Create dictionary holding test folders (MPP, JV, Analyzed)
        folder_map = self.map_test_folders(test_folders)
        # Create list of Analyzed folders
        analyzed_folders = []
        for select_test in test_folders:
            sub_folders = folder_map[select_test][filetype]
            for sub_folder in sub_folders:
                analyzed_folders.append(sub_folder)
        # Create dictionary holding files in each analyzedfolder
        file_map = self.map_test_files(analyzed_folders)
        # Create list of analyzed files
        analyzed_files = []
        for select_analyzed_folder in analyzed_folders:
            analyzed_files.append(file_map[select_analyzed_folder])

        return analyzed_files

    def get_env_files(self, startdate: str, enddate: str) -> str:
        """Returns a list of all files in test folders

        Args:
            startdate (str): start date of test in xYYYYMMDD format
            enddate (str): end date of test in xYYYYMMDD format

        Returns:
            list[list[str]]: list of file paths seperated by env folder
        """

        # Get start year and end year from dates
        start_year = int(startdate[1:5])
        end_year = int(enddate[1:5])

        # Create list of env folders in directory
        all_env_folders = self.get_env_folders()

        # Get list of folders in date range
        used_env_folders = []
        for folder in all_env_folders:
            foldername = os.path.basename(folder)

            if start_year <= float(foldername[1:5]) <= end_year:
                used_env_folders.append(folder)

        # Create map of folders (gets all files in a folder (max 365 per folder))
        folder_map = self.map_env_files(used_env_folders, startdate, enddate)
        env_files = []
        for folder in used_env_folders:
            env_files.append(folder_map[folder])

        return env_files
