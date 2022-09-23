#!/usr/bin/env python

"""
Move Python symbol to a different location

Usage:
>> python move_symbol/move_symbol.py OLD_SYMBOL NEW_SYMBOL

"""

from dataclasses import dataclass
from pathlib import Path
import subprocess
import sys

from libcst.codemod._context import CodemodContext
from libcst.metadata.full_repo_manager import FullRepoManager
from libcst.metadata.name_provider import FullyQualifiedNameProvider

from move_symbol.utils import ROOT_DIR, to_file
from move_symbol.visitors.add_symbols import AddSymbolsVisitor
from move_symbol.visitors.remove_symbols import RemoveSymbolsVisitor


@dataclass
class Symbol:
    module: str
    name: str

    @classmethod
    def from_qualified_name(cls, s: str) -> "Symbol":
        assert "." in s, "Qualified symbol name must be of the form module.name"
        module, name = s.rsplit(".", 1)
        return cls(module, name)


def move_symbol(
    old_qualified_symbol_names: str, new_qualified_symbol_names: str
) -> None:
    old_symbols = [
        Symbol.from_qualified_name(s) for s in old_qualified_symbol_names.split(",")
    ]
    new_symbols = [
        Symbol.from_qualified_name(s) for s in new_qualified_symbol_names.split(",")
    ]
    assert len(old_symbols) == len(
        new_symbols
    ), "Must specify the same number of old and new symbols"
    old_modules = set(s.module for s in old_symbols)
    new_modules = set(s.module for s in new_symbols)
    assert (
        len(old_modules) == 1
    ), f"Old symbols must all be in the same module. Found: {old_modules}"
    assert (
        len(new_modules) == 1
    ), f"New symbols must all be in the same module. Found: {new_modules}"
    old_module = old_modules.pop()
    new_module = new_modules.pop()

    old_file = to_file(old_module)
    new_file = to_file(new_module)

    assert Path(old_file).is_file(), f"File {old_file} does not exist"
    if not Path(new_file).exists():
        Path(new_file).parent.mkdir(parents=True, exist_ok=True)
        Path(new_file).touch()
    assert Path(new_file).is_file(), f"File {new_file} does not exist"

    manager = FullRepoManager(
        str(ROOT_DIR), [old_file, new_file], [FullyQualifiedNameProvider]
    )
    manager = FullRepoManager(
        str(ROOT_DIR), [old_file, new_file], [FullyQualifiedNameProvider]
    )
    old_wrapper = manager.get_metadata_wrapper_for_path(old_file)
    new_wrapper = manager.get_metadata_wrapper_for_path(new_file)

    old_context = CodemodContext(
        filename=old_file,
        full_module_name=old_module,
        wrapper=old_wrapper,
        metadata_manager=manager,
    )
    new_context = CodemodContext(
        filename=new_file,
        full_module_name=new_module,
        wrapper=new_wrapper,
        metadata_manager=manager,
    )

    remove_visitor = RemoveSymbolsVisitor(old_context, {s.name for s in old_symbols})
    assert old_context.module, "Module must be defined"
    updated_old_tree = remove_visitor.transform_module(old_context.module)
    Path(old_file).write_text(updated_old_tree.code)

    removed = remove_visitor.context.scratch[RemoveSymbolsVisitor.CONTEXT_KEY]
    nodes_to_add = removed["nodes"]
    imports_to_add = removed["imports"]

    add_visitor = AddSymbolsVisitor(new_context, nodes_to_add, imports_to_add)
    assert new_context.module, "Module must be defined"
    updated_new_tree = add_visitor.transform_module(new_context.module)
    Path(new_file).write_text(updated_new_tree.code)

    codemod_old_exports_to_new_exports(
        old_qualified_symbol_names, new_qualified_symbol_names
    )


def codemod_old_exports_to_new_exports(old_symbols: str, new_symbols: str) -> None:
    """Execute ReplaceCodemod to renamed old exports to new exports.

    For performance, we only apply the codemod to Python files that contain any of the old symbols
    """

    symbols = [old_symbol.rsplit(".", 1)[1] for old_symbol in old_symbols.split(",")]
    combined = "(" + "|".join(symbols) + ")"

    grep_for_filenames_command = f"git grep --files-with-matches --extended-regexp '{combined}' {str(ROOT_DIR)} | grep -E '\.py$'"
    codemod_command = f"python3 -m libcst.tool codemod replace.ReplaceCodemod --old={old_symbols} --new={new_symbols}"
    command = f"{grep_for_filenames_command} | xargs {codemod_command}"
    print(command)

    subprocess.run(
        command,
        shell=True,
        stdin=sys.stdin,
        stdout=sys.stdout,
        stderr=sys.stderr,
        cwd=ROOT_DIR,
    )
