import os
import yaml


MODULE_DIR = os.path.dirname(__file__)
DEFAULT_USER_CONFIG = os.path.join(MODULE_DIR, "hardwareconstants.yaml")
CUSTOM_USER_CONFIG = os.path.join(MODULE_DIR, "userconstants.yaml")

class Configuration:
    
    def __init__(self):
        pass
    
    def create_custom_config(self):

        # open default file
        with open(DEFAULT_USER_CONFIG, "r") as f:
            default_constants = yaml.safe_load(f)
        
        # copy contents to desired location
        with open(CUSTOM_USER_CONFIG, 'w') as file:
            user_constants = yaml.dump(default_constants, file)
        
        print(f"We started a custom user config file for you at {CUSTOM_USER_CONFIG}. Please edit this file to point parasol to your directories.")

    def get_config(self):
        if os.path.exists(CUSTOM_USER_CONFIG):
            with open(CUSTOM_USER_CONFIG, "r") as f:
                constants = yaml.safe_load(f)
        else:
            with open(DEFAULT_USER_CONFIG, "r") as f:
                constants = yaml.safe_load(f)        
        return constants