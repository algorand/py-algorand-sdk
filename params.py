from os.path import expanduser
home = expanduser("~")

# change these after starting the node and kmd
# algod info is in the algod.net and algod.token files in the data directory
# kmd info is in the kmd.net and kmd.token files in the kmd directory in data
# change these after starting the node and kmd

kmdToken = ""
kmdAddress = "http://localhost:7833"

algodToken = ""
algodAddress = "http://localhost:8080"

# path to the data directory (for example, "/Users/[user_name]/node/data/")
data_dir_path = home + "/node/network/Primary"
kmd_folder_name = "kmd-v0.5"  # name of the kmd folder in the data directory

# get tokens and addresses automatically, if data_dir_path is not empty
if data_dir_path and kmd_folder_name:
    if not data_dir_path[-1].__eq__("/"):
        data_dir_path += "/"
    if not kmd_folder_name[-1].__eq__("/"):
        kmd_folder_name += "/"
    algodToken = open(data_dir_path + "algod.token", "r").read().strip("\n")
    algodAddress = "http://" + open(data_dir_path + "algod.net",
                                    "r").read().strip("\n")
    kmdToken = open(data_dir_path + kmd_folder_name + "kmd.token",
                    "r").read().strip("\n")
    kmdAddress = "http://" + open(data_dir_path + kmd_folder_name + "kmd.net",
                                  "r").read().strip("\n")
