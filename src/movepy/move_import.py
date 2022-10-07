"""
Move Python imports.
"""
from typing import List

from libcst.codemod._context import CodemodContext
from libcst.metadata.full_repo_manager import FullRepoManager
from libcst.metadata.name_provider import FullyQualifiedNameProvider

from movepy.visitors.add_symbols import AddSymbolsVisitor
from movepy.visitors.remove_symbols import RemoveSymbolsVisitor
from movepy.utils import ROOT_DIR, shell, to_file


def move(src: str, dst: str) -> None:
    """Copy contents of `srcs` to `dsts`."""
    old_module, old_symbol = src.rsplit(".", 1)
    new_module, new_symbol = dst.rsplit(".", 1)

    old_file = to_file(old_module, already_exists=True)
    new_file = to_file(new_module, should_create=True)

    manager = FullRepoManager(
        str(ROOT_DIR), [str(old_file), str(new_file)], [FullyQualifiedNameProvider]
    )
    old_wrapper = manager.get_metadata_wrapper_for_path(str(old_file))
    new_wrapper = manager.get_metadata_wrapper_for_path(str(new_file))

    old_context = CodemodContext(
        filename=str(old_file),
        full_module_name=old_module,
        wrapper=old_wrapper,
        metadata_manager=manager,
    )
    new_context = CodemodContext(
        filename=str(new_file),
        full_module_name=new_module,
        wrapper=new_wrapper,
        metadata_manager=manager,
    )

    remove_visitor = RemoveSymbolsVisitor(old_context, {old_symbol})
    assert old_context.module, "Module must be defined"
    updated_old_tree = remove_visitor.transform_module(old_context.module)
    old_file.write_text(updated_old_tree.code)

    removed = remove_visitor.context.scratch[RemoveSymbolsVisitor.CONTEXT_KEY]
    nodes_to_add = removed["nodes"]

    add_visitor = AddSymbolsVisitor(new_context, nodes_to_add, set())
    assert new_context.module, "Module must be defined"
    updated_new_tree = add_visitor.transform_module(new_context.module)
    new_file.write_text(updated_new_tree.code)


def codemod_imports(srcs: List[str], dsts: List[str]) -> None:
    """Execute ReplaceCodemod to renamed old imports to new imports.

    For performance, we only apply the codemod to Python files may possibly have the old exports.
    """
    symbols = [old_symbol.rsplit(".", 1)[1] for old_symbol in srcs]
    combined = "(" + "|".join(symbols) + ")"

    grep_for_filenames_command = f"git grep --files-with-matches --extended-regexp '{combined}' {str(ROOT_DIR)} | grep -E '\.py$'"
    codemod_command = f"python3 -m libcst.tool codemod replace.ReplaceCodemod --old={','.join(srcs)} --new={','.join(dsts)}"
    command = f"{grep_for_filenames_command} | xargs {codemod_command}"
    shell(command)


def move_import(srcs: List[str], dsts: List[str]) -> None:
    if len(srcs) != 1 or len(dsts) != 1:
        raise Exception("Only support moving one import at a time right now :/")
    move(srcs[0], dsts[0])
    codemod_imports(srcs, dsts)
