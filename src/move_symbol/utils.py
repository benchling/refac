import os
import pathlib
import subprocess
import sys


ROOT_DIR = pathlib.Path(os.environ.get("ROOT_DIR", os.getcwd()))


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


def make_py_file(path: pathlib.Path) -> None:
    """Make a Python file at `path` if it doesn't exist.

    Also make any missing directories and add __init__.py files.

    >>> make_py_file(pathlib.Path("src/models/user.py"))
    """
    if path.exists():
        return
    parent = path.parent.resolve()
    parent.mkdir(parents=True, exist_ok=True)
    path.touch()

    while parent != ROOT_DIR:
        if not (parent / "__init__.py").exists():
            (parent / "__init__.py").touch()
        parent = parent.parent
        print(parent, ROOT_DIR)
