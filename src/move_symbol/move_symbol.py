"""
Move Python symbol and fix all imports.
"""

from pathlib import Path
from typing import List, Set, Tuple

from libcst.codemod._context import CodemodContext
from libcst.metadata.full_repo_manager import FullRepoManager
from libcst.metadata.name_provider import FullyQualifiedNameProvider

from move_symbol.utils import ROOT_DIR, make_py_file, shell, to_file
from move_symbol.visitors.add_symbols import AddSymbolsVisitor
from move_symbol.visitors.remove_symbols import RemoveSymbolsVisitor


def validate(
    old_full_symbols: List[str], new_full_symbols: List[str]
) -> Tuple[str, Set[str], str, Set[str]]:
    """Validate that all imports are valid and that all symbols are defined"""

    assert len(old_full_symbols) == len(new_full_symbols), (
        "Must specify the same number of old and new symbols",
    )

    old_modules = set(s.rsplit(".", 1)[0] for s in old_full_symbols)
    new_modules = set(s.rsplit(".", 1)[0] for s in new_full_symbols)
    assert len(old_modules) == 1, (
        f"Old symbols must all be in the same module. Found: {old_modules}",
    )
    assert len(new_modules) == 1, (
        f"New symbols must all be in the same module. Found: {new_modules}",
    )
    old_module = old_modules.pop()
    new_module = new_modules.pop()

    old_symbols = set(s.rsplit(".", 1)[1] for s in old_full_symbols)
    new_symbols = set(s.rsplit(".", 1)[1] for s in new_full_symbols)
    # TODO: Allow renaming symbols.
    assert old_symbols == new_symbols, (
        f"Old symbols names must match new symbol names. {old_symbols} != {new_symbols}",
    )

    old_file = to_file(old_module)
    new_file = to_file(new_module)

    assert Path(old_file).is_file(), f"File {old_file} does not exist"
    make_py_file(Path(new_file))

    return (old_module, old_symbols, new_module, new_symbols)


def move(srcs: List[str], dsts: List[str]) -> None:
    (old_module, old_symbols, new_module, _new_symbols) = validate(srcs, dsts)
    old_file = to_file(old_module)
    new_file = to_file(new_module)

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

    remove_visitor = RemoveSymbolsVisitor(old_context, old_symbols)
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


def codemod_old_exports_to_new_exports(
    old_symbols: List[str], new_symbols: List[str]
) -> None:
    """Execute ReplaceCodemod to renamed old exports to new exports.

    For performance, we only apply the codemod to Python files that contain any of the old symbols
    """

    symbols = [old_symbol.rsplit(".", 1)[1] for old_symbol in old_symbols]
    combined = "(" + "|".join(symbols) + ")"

    grep_for_filenames_command = f"git grep --files-with-matches --extended-regexp '{combined}' {str(ROOT_DIR)} | grep -E '\.py$'"
    codemod_command = f"python3 -m libcst.tool codemod replace.ReplaceCodemod --old={','.join(old_symbols)} --new={','.join(new_symbols)}"
    command = f"{grep_for_filenames_command} | xargs {codemod_command}"
    shell(command)


def move_symbol(srcs: List[str], dsts: List[str]) -> None:
    move(srcs, dsts)
    codemod_old_exports_to_new_exports(srcs, dsts)
