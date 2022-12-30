import sys
from typing import Dict, Optional, Tuple


def get_env(line: str) -> Optional[Tuple[str, str, str]]:
    if line and line[0] not in (" ", "#") and "=" in line:
        key, others = line.split("=", maxsplit=1)
        key = key.strip()
        if "#" in others:
            val, extra = others.split("#", maxsplit=1)
            val = val.strip()
        else:
            val, extra = others.strip(), ""
        return key, val, extra


def manualy_parse(env_file: str) -> Dict[str, str]:
    env = {}
    with open(env_file) as f:
        for line in f.readlines():
            if e := get_env(line):
                key, val, _ = e
                env[key] = val
    return env


def overwrite(env_file: str, new_env: Dict[str, str]) -> None:
    with open(env_file, "r+") as f:
        lines = f.readlines()
        for i, line in enumerate(lines):
            if e := get_env(line):
                key, old_val, extra = e
                if key in new_env and (val := new_env[key]) != old_val:
                    lines[i] = (
                        f"{key}={val} # (previously `{old_val}`)"
                        + (f" # {extra}" if extra else "")
                        + "\n"
                    )

        f.seek(0)
        f.writelines(lines)
        f.truncate()


def get_rewrites(
    env: Dict[str, str], key_filter: Optional[str] = None
) -> Dict[str, str]:
    keys = key_filter.split(",") if key_filter else None
    return {
        k: w
        for k, v in env.items()
        if (not keys or k in keys)
        and (w := input(f"{k} (default `{v}`):").strip())
        and w != v
    }


def get_keys(env: Dict[str, str]) -> Optional[str]:
    print(
        f"""Which of the following env vars do you want to modify?

{",".join(env.keys())}

    (skip for ALL, or provide comma separated)
    
    A typical choice is:
TYPE,ALGOD_URL,ALGOD_BRANCH
"""
    )
    return input("CHOICES:\n").strip()


def go():
    env_file = sys.argv[1]
    env = manualy_parse(env_file)
    print("_" * 50)
    keys = get_keys(env)
    print("_" * 50)
    print("Please provide env variable overrides (skip to keep defaults)")
    new_env = get_rewrites(env, key_filter=keys)

    print("_" * 50)
    print("OVERWRITING")
    for k, v in new_env.items():
        print(f"new_env[{k}]={v} (PREVIOUS: env[{k}]={env[k]})")

    overwrite(env_file, new_env)
    print("_" * 50)


go()
