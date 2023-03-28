"""
Move Python file and fix all imports.

Potential bugs:
 - Moving file with relative imports.
 - Moving dir with relative OUTSIDE of the dir
"""

import pathlib
import shutil
from typing import List

from refac.replace_str import find_and_replace

from refac.utils import ROOT_DIR, make_py_file, shell, to_module


def validate(old_path: pathlib.Path, new_path: pathlib.Path) -> None:
    if old_path.is_file() and new_path.is_dir():
        raise Exception(
            f"Cannot move a file ({old_path}) to a directory ({new_path}). Specify the new filename in directory."
        )
    elif old_path.is_dir() and new_path.is_file():
        raise Exception(f"Cannot move a directory ({old_path}) to a file ({new_path}).")


def codemod_imports(
    old_path: pathlib.Path,
    new_path: pathlib.Path,
) -> None:
    """Execute ReplaceImportCodemod to renamed old exports to new exports.

    For performance, we only apply the codemod to Python files may possibly have the old exports.
    We look for these Python files by absolute import of the `old_module` ('from a.b.c')
    or relative import of its parts (from .c or from ..b or from ...a).
    """
    old_module = to_module(old_path)
    new_module = to_module(new_path)

    grep_for_filenames_command = f"git grep --files-with-matches --extended-regexp '{old_module.rsplit('.', 1)[1]}' {str(ROOT_DIR)} | grep -E '[.]py$'"
    codemod_command = f"python3 -m libcst.tool codemod __init__.ReplaceImportCodemod --old={old_module} --new={new_module}"
    command = f"{grep_for_filenames_command} | xargs {codemod_command}"
    shell(command)


def move(old_path: pathlib.Path, new_path: pathlib.Path) -> None:
    """Copy contents of `old_path` to `new_path`."""
    make_py_file(new_path)

    if old_path.is_file() and (not new_path.exists() or new_path.is_file()):
        old_contents = old_path.read_text()
        new_contents = (
            new_path.read_text() + "\n" if new_path.is_file() else ""
        ) + old_contents

        new_path.write_text(new_contents)
        old_path.unlink()
        # TODO: May need to remove some imports from the new file if they point to self.
    elif old_path.is_dir() and (not new_path.exists() or new_path.is_dir()):
        # May overwrite files in the new directory if they have the same name as files in the old directory.
        shutil.copytree(old_path, new_path, dirs_exist_ok=True)
        shutil.rmtree(old_path)


def move_file(
    old_paths: List[str], new_paths: List[str], include_strings: bool = False
) -> None:
    # TODO: Support moving multiple files?
    if len(old_paths) != 1 or len(new_paths) != 1:
        raise Exception("Only support moving one file at a time right now :/")
    old_path, new_path = pathlib.Path(old_paths[0]), pathlib.Path(new_paths[0])
    validate(old_path, new_path)
    move(old_path, new_path)
    codemod_imports(old_path, new_path)

    if include_strings:
        old_filename = str(old_path.resolve().relative_to(ROOT_DIR))
        new_filename = str(new_path.resolve().relative_to(ROOT_DIR))
        old_module = to_module(old_path)
        new_module = to_module(new_path)
        find_and_replace(old_filename, new_filename)
        find_and_replace(old_module, new_module)
