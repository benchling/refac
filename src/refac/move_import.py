"""
Move Python imports.
"""
from typing import List

from refac.utils import ROOT_DIR, shell


def codemod_imports(srcs: List[str], dsts: List[str]) -> None:
    """Execute ReplaceImportCodemod to renamed old imports to new imports.

    For performance, we only apply the codemod to Python files may possibly have the old exports.
    """
    symbols = [old_symbol.rsplit(".", 1)[1] for old_symbol in srcs]
    combined = "(" + "|".join(symbols) + ")"

    grep_for_filenames_command = f"git grep --files-with-matches --extended-regexp '{combined}' {str(ROOT_DIR)} | grep -E '[.]py$'"
    codemod_command = f"python3 -m libcst.tool codemod __init__.ReplaceImportCodemod --old={','.join(srcs)} --new={','.join(dsts)}"
    command = f"{grep_for_filenames_command} | xargs {codemod_command}"
    shell(command)


def move_import(srcs: List[str], dsts: List[str]) -> None:
    codemod_imports(srcs, dsts)
