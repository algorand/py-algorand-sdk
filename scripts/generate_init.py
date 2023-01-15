import argparse
from collections import Counter
import difflib
from pathlib import Path
import sys

from algosdk import __all__ as static_all


# Start of the template to be appended to
pyi_template = """## File generated from scripts/generate_init.py.
## DO NOT EDIT DIRECTLY

"""

# Template for __all__ export list
all_template = """__all__ = [
    {},
]"""

# Flags to denote the beginning/end of the __all__ exports in __init__.py
begin_flag = "# begin __all__"
end_flag = "# end __all__"

# Make it safe to run from anywhere
curr_dir = Path.cwd()
orig_dir = curr_dir / "algosdk"

# Path to pyi
pyi_file = "__init__.pyi"
orig_file = orig_dir / pyi_file

# Path to py
py_file = "__init__.py"
init_file = orig_dir / py_file


def generate_init_pyi() -> str:
    with open(init_file, "r") as f:
        init_contents = f.read()

    start_idx = init_contents.index(begin_flag)
    end_idx = init_contents.index(end_flag)

    counts = Counter(static_all)
    dupes = [x for x, n in counts.items() if n > 1]
    BR = "\n"
    assert not dupes, (
        f"Aborting pyi file generation. The following duplicate imports were "
        f"detected:{BR}{BR.join(dupes)}"
    )

    all_imports = ",\n    ".join(
        ['"{}"'.format(s) for s in sorted(static_all)]
    )

    return (
        pyi_template
        + init_contents[:start_idx]
        + all_template.format(all_imports)
        + init_contents[end_idx + len(end_flag) :]
    )


def is_different(regen: str) -> bool:
    if not orig_file.exists():
        return True

    with open(orig_file, "r") as f:
        orig_lines = f.readlines()

    curr_lines = regen.splitlines(keepends=True)

    diff = list(
        difflib.unified_diff(
            orig_lines,
            curr_lines,
            fromfile="original",
            tofile="generated",
            n=3,
        )
    )

    if len(diff) != 0:
        print("".join(diff), end="")
        return True

    return False


def overwrite(regen: str):
    with open(orig_file, "w") as f:
        f.write(regen)


if __name__ == "__main__":

    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--check",
        action="store_true",
        help="Only check if the generated file would change",
    )
    args = parser.parse_args()

    regen = generate_init_pyi()

    if args.check:
        if is_different(regen):
            print(
                "The __init__.pyi needs to be regenerated. "
                "Please run scripts/generate_init.py"
            )
            sys.exit(1)
        print("No changes in __init__.pyi")
        sys.exit(0)

    overwrite(regen)
