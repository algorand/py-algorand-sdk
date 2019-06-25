# change these after starting the node and kmd
# algod info is in the algod.net and algod.token files in the node's data directory
# kmd info is in the kmd.net and kmd.token files in the kmd directory which is in data
# change these after starting the node and kmd

kmdToken = "ddf94bd098816efcd2e47e12b5fe20285f48257201ca1fe4067000a15f3fbd69"
kmdAddress = "http://localhost:59987"

algodToken = "d05db6ecec87954e747bd66668ec6dd3c3cef86d99ea88e8ca42a20f93f6be01"
algodAddress = "http://localhost:c61186"

# get tokens and addresses automatically, if data_dir_path is not empty
data_dir_path = "/Users/Michelle/node/network/Primary/"
kmd_folder_name = "kmd-v0.5/"

if data_dir_path:
    if not data_dir_path[-1].__eq__("/"):
        data_dir_path += "/"
    algodToken = open(data_dir_path + "algod.token", "r").read().strip("\n")
    algodAddress = "http://" + open(data_dir_path + "algod.net", "r").read().strip("\n")
    kmdToken = open(data_dir_path + kmd_folder_name + "kmd.token", "r").read().strip("\n")
    kmdAddress = "http://" + open(data_dir_path + kmd_folder_name + "kmd.net", "r").read().strip("\n")

