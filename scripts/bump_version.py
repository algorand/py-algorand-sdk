import argparse
import re

parser = argparse.ArgumentParser(description="updates the version for a release",
                                 formatter_class=argparse.ArgumentDefaultsHelpFormatter)
parser.add_argument("new_version", help="New Version as major.minor.patch")
parser.add_argument("-s", "--setup_py_path", default="setup.py", help="path to setup.py")

args = parser.parse_args()
new_version = args.new_version
setup_py_path = args.setup_py_path

with open(setup_py_path, "r") as file:
    setup_py = file.read()

new_setup_py = re.sub('version="[0-9]+\.[0-9]+\.[0-9]+"',f"version=\"{new_version}\"", setup_py)

with open(setup_py_path, "w") as file:
    file.write(new_setup_py)
