# examples helper file

from os import listdir
from os.path import expanduser

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
