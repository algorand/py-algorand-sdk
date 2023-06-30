# This script bumps up the version in setup.py for new releases.
# Usage: python bump_version.py {new_version} (--setup_py_path <path-to setup.py>)

import argparse
import re
import sys


def check_version(new_version):
    if not re.fullmatch(r"[0-9]+\.[0-9]+\.[a-z.0-9]+", new_version):
        sys.exit(
            "The version does not match the regex(major.minor.patch): [0-9]+\.[0-9]+\.[a-z.0-9]+"
        )


def bump_version(new_version, setup_py_path):
    with open(setup_py_path, "r") as file:
        setup_py = file.read()

    new_setup_py = re.sub(
        'version="[0-9]+\.[0-9]+\.[a-z.0-9]+"',
        f'version="{new_version}"',
        setup_py,
    )

    with open(setup_py_path, "w") as file:
        file.write(new_setup_py)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="updates the version for a release",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("new_version", help="New Version as major.minor.patch")
    parser.add_argument(
        "-s", "--setup_py_path", default="setup.py", help="path to setup.py"
    )

    args = parser.parse_args()

    check_version(args.new_version)
    bump_version(args.new_version, args.setup_py_path)
