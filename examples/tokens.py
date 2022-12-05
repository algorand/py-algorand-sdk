# Examples helper file

from os import listdir
from os.path import expanduser

home = expanduser("~")

# These values are initialized for the SDK sandbox harness.
# You can bring the harness up by running `make harness`.
#
# If you are using your own node installation, change these after starting the node and kmd.
# algod info is in the algod.net and algod.token files in the data directory
# kmd info is in the kmd.net and kmd.token files in the kmd directory in data
kmd_token = "a" * 64
kmd_address = "http://localhost:59999"

algod_token = "a" * 64
algod_address = "http://localhost:60000"

# you can also get tokens and addresses automatically
get_automatically = False

# path to the data directory
data_dir_path = home + "/node/network/Node"

if get_automatically:
    if not data_dir_path[-1] == "/":
        data_dir_path += "/"
    for directory in listdir(data_dir_path):
        if "kmd" in directory:
            kmd_folder_name = directory
    if not kmd_folder_name[-1] == "/":
        kmd_folder_name += "/"
    algod_token = open(data_dir_path + "algod.token", "r").read().strip("\n")
    algod_address = "http://" + open(
        data_dir_path + "algod.net", "r"
    ).read().strip("\n")
    kmd_token = (
        open(data_dir_path + kmd_folder_name + "kmd.token", "r")
        .read()
        .strip("\n")
    )
    kmd_address = "http://" + open(
        data_dir_path + kmd_folder_name + "kmd.net", "r"
    ).read().strip("\n")
