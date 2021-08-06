# examples helper file

from os import listdir, getenv
from os.path import expanduser, exists

home = expanduser("~")

# change these after starting the node and kmd
# algod info is in the algod.net and algod.token files in the data directory
# kmd info is in the kmd.net and kmd.token files in the kmd directory in data

kmd_token = ""
kmd_address = ""

algod_token = ""
algod_address = ""

# you can also get tokens and addresses automatically
get_automatically = True

# path to the data directory
data_dir_path = home + "/node/network/Node"

# check if ALGORAND_DATA environment variable is set to replace data_dir_path
ALGORAND_DATA_ENV = getenv('ALGORAND_DATA')
if ALGORAND_DATA_ENV:
    data_dir_path = ALGORAND_DATA_ENV

# path to the kmd data (in Debian/RPM versions of installations of Algorand Node)
kmd_parent_dir_path = home + "/.algorand"


if get_automatically:
    if not data_dir_path[-1] == "/":
        data_dir_path += "/"

    kmd_folder_name = None
    for directory in listdir(data_dir_path):
        if "kmd" in directory:
            kmd_folder_name = directory

    if kmd_folder_name:
        kmd_dir_path = data_dir_path + kmd_folder_name
    elif exists(kmd_parent_dir_path):
        for directory in listdir(kmd_parent_dir_path):
            if "mainnet" in directory:
                for sub_directory in listdir(kmd_parent_dir_path + "/" + directory):
                    if "kmd" in sub_directory:
                        kmd_dir_path = kmd_parent_dir_path + "/" + directory + "/" + sub_directory

    if not kmd_dir_path[-1] == "/":
        kmd_dir_path += "/"

    algod_token = open(data_dir_path + "algod.token", "r").read().strip("\n")
    algod_address = "http://" + open(data_dir_path + "algod.net", "r").read().strip("\n")

    kmd_token = open(kmd_dir_path + "kmd.token",
                     "r").read().strip("\n")
    kmd_address = "http://" + open(kmd_dir_path + "kmd.net", "r").read().strip("\n")
