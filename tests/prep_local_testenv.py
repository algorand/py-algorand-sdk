import os
import sys

ENV_VARS = [
    "TYPE_OVERRIDE",
    "TESTING_URL",
    "TESTING_BRANCH",
    "ALGOD_URL",
    "ALGOD_BRANCH",
    "INDEXER_URL",
    "INDEXER_BRANCH",
]

if __name__ == "__main__":
    assert (
        len(sys.argv) == 2
    ), f"expected 1 argument but provided {len(sys.argv) - 1}"
    local_env_filename = sys.argv[1]
    print(f"prepping '{local_env_filename}'")

    with open(local_env_filename, "w") as f:
        lines = []
        for ev in ENV_VARS:
            lines.append(f"{ev}={os.environ.get(ev)}" + "\n")
        f.writelines(lines)

else:
    print(f"NO-OP when non main: __name__={__name__}")
