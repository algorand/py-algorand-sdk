import argparse
import re

parser = argparse.ArgumentParser(description="updates the version for a release",
                                 formatter_class=argparse.ArgumentDefaultsHelpFormatter)
parser.add_argument("--new_version", help="New Version")
# parser.add_argument("-b", "--bump", help="version section to bump")

args = parser.parse_args()
new_version = args.new_version

with open("setup.py", "r") as file:
    setup_py = file.read()

new_setup_py = re.sub('version="[0-9]+\.[0-9]+\.[0-9]+"',f"version=\"{new_version}\"", setup_py)

with open("setup.py", "w") as file:
    file.write(new_setup_py)
