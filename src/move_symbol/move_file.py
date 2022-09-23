#!/usr/bin/env python

"""
Move Python file and fix all imports.

Usage:
>> python scripts/dev/libcst_codemods/move_file.py OLD_FILE NEW_FILE

Potential bugs:
 - Moving file with relative imports.
 - Moving dir with relative OUTSIDE of the dir
"""

import pathlib
import re
import shutil
import subprocess
import sys

import click

AURELIA_ROOT = pathlib.Path("/src")


def _to_module(path: pathlib.Path) -> str:
    """Convert a Python filename to a Python module name.

    >>> _to_module(benchling/notebook/models/entry.py).
    benchling.notebook.models.entry

    >>> _to_module(benchling/notebook/lib/__init__.py)
    benchling.notebook.lib
    """
    filename = path.resolve().relative_to(AURELIA_ROOT)
    return str(filename).replace(".py", "").replace("__init__", "").replace("/", ".")


def validate(old_path: pathlib.Path, new_path: pathlib.Path) -> None:
    if old_path.is_file() and new_path.is_dir():
        raise click.ClickException(
            f"Cannot move a file ({old_path}) to a directory ({new_path}). Specify the new filename in directory."
        )
    elif old_path.is_dir() and new_path.is_file():
        raise click.ClickException(
            f"Cannot move a directory ({old_path}) to a file ({new_path})."
        )


def codemod_old_exports_to_new_exports(
    old_path: pathlib.Path,
    new_path: pathlib.Path,
) -> None:
    """Execute ReplaceCodemod to renamed old exports to new exports.

    For performance, we only apply the codemod to Python files may possibly have the old exports.
    We look for these Python files by absolute import of the `old_module` ('from a.b.c')
    or relative import of its parts (from .c or from ..b or from ...a).
    """

    old_module = _to_module(old_path)
    new_module = _to_module(new_path)

    regexes = (
        # absolute import - e.g. `from a.b.c`
        f"^\s*from {old_module}",
        # relative import - e.g. `from .c` or `from ..b` or `from ...a`
        *[
            f"^\s*from \.{{{i}}}{part}"
            for i, part in enumerate(reversed(old_module.split(".")), start=1)
        ],
    )
    combined = "(" + "|".join(regexes) + ")"

    grep_for_filenames_command = f"git grep --files-with-matches --extended-regexp '{combined}' {str(AURELIA_ROOT)} | grep -E '\.py$'"
    codemod_command = f"python3 -m libcst.tool codemod replace.ReplaceCodemod --old={old_module} --new={new_module}"
    command = f"{grep_for_filenames_command} | xargs {codemod_command}"
    print(command)

    subprocess.run(
        command,
        shell=True,
        stdin=sys.stdin,
        stdout=sys.stdout,
        stderr=sys.stderr,
        cwd=AURELIA_ROOT,
    )


def codemod_old_strings_to_new_strings(
    old_path: pathlib.Path,
    new_path: pathlib.Path,
) -> None:
    old_filename = old_path.resolve().relative_to(AURELIA_ROOT)
    new_filename = new_path.resolve().relative_to(AURELIA_ROOT)
    old_module = _to_module(old_path)
    new_module = _to_module(new_path)

    sed = "sed -i" if sys.platform == "linux" else "sed -i '' -e"
    command = (
        f"git grep --files-with-matches '{old_filename}' | xargs {sed} 's/{re.escape(old_filename)}/{re.escape(new_filename)}/g'",
    )
    print(command)

    subprocess.run(
        command,
        shell=True,
        stdin=sys.stdin,
        stdout=sys.stdout,
        stderr=sys.stderr,
        cwd=AURELIA_ROOT,
    )

    command2 = (
        f"git grep --files-with-matches '{old_module}' | xargs {sed} 's/{re.escape(old_module)}/{re.escape(new_module)}/g'",
    )
    print(command2)

    subprocess.run(
        command2,
        shell=True,
        stdin=sys.stdin,
        stdout=sys.stdout,
        stderr=sys.stderr,
        cwd=AURELIA_ROOT,
    )


def move(old_path: pathlib.Path, new_path: pathlib.Path) -> None:
    """Copy contents of `old_path` to `new_path`."""
    if old_path.is_file() and (not new_path.exists() or new_path.is_file()):
        old_contents = old_path.read_text()
        new_contents = (
            new_path.read_text() + "\n" if new_path.is_file() else ""
        ) + old_contents

        new_path.parent.mkdir(parents=True, exist_ok=True)
        new_path.write_text(new_contents)
        old_path.unlink()
        # TODO: May need to remove some imports from the new file if they point to self.
    elif old_path.is_dir() and (not new_path.exists() or new_path.is_dir()):
        # May overwrite files in the new directory if they have the same name as files in the old directory.
        shutil.copytree(old_path, new_path, dirs_exist_ok=True)
        shutil.rmtree(old_path)


def move_file(
    old_path: pathlib.Path, new_path: pathlib.Path, include_strings: bool = False
) -> None:
    validate(old_path, new_path)
    move(old_path, new_path)
    codemod_old_exports_to_new_exports(old_path, new_path)

    if include_strings:
        # 1. TODO: FIX CODEMOD TO  ESCAPE '/' STRINGS.
        # 2. TODO: FIX CODEMOD TO ALSO DO MODULES.
        # 3. TODO: Add string renaming to move_symbol.

        codemod_old_strings_to_new_strings(old_path, new_path)


@click.command()
@click.argument("old_path", type=click.Path(exists=True, path_type=pathlib.Path))
@click.argument("new_path", type=click.Path(exists=False, path_type=pathlib.Path))
@click.option("--include-strings", type=click.BOOL, default=False)
def main(
    old_path: pathlib.Path, new_path: pathlib.Path, include_strings: bool = False
) -> None:
    move_file(old_path, new_path, include_strings)


if __name__ == "__main__":
    main()
