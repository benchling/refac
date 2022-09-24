import os
import pathlib
import subprocess
import sys


ROOT_DIR = pathlib.Path(os.environ.get("ROOT_DIR", "."))


def shell(command: str, **kwargs) -> subprocess.CompletedProcess:
    """Run a shell command.

    >>> shell("echo hello")
    """
    print(f"Running: {command!r}\n")
    return subprocess.run(
        command,
        shell=True,
        stdin=sys.stdin,
        stdout=sys.stdout,
        stderr=sys.stderr,
        cwd=ROOT_DIR,
        **kwargs,
    )


def to_module(path: pathlib.Path) -> str:
    """Convert a Python filename to a Python module name.

    Assumes modules is relatve to $ROOT_DIR or the current working directory.

    >>> _to_module(src/models/user.py).
    src.models.user

    >>> _to_module(tests/unit/lib/__init__.py)
    tests.unit.lib
    """
    filename = path.resolve().relative_to(ROOT_DIR)
    return str(filename).replace(".py", "").replace("__init__", "").replace("/", ".")


def to_file(module: str) -> str:
    """Convert a Python module to a Python filename.

    >>> to_file("src.models.user")
    src/models/user.py
    """
    filename = module.replace(".", "/") + ".py"
    return filename
