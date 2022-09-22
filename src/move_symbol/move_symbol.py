#!/usr/bin/env python

"""
Move Python symbol to a different location

Usage:
>> python move_symbol/move_symbol.py OLD_SYMBOL NEW_SYMBOL

"""

from dataclasses import dataclass
from functools import cache
from pathlib import Path
import subprocess
import symbol
import sys
from typing import Iterable, Optional, Union

import click
import libcst as cst
from libcst.codemod._command import VisitorBasedCodemodCommand
from libcst.codemod._context import CodemodContext
from libcst.codemod.visitors import AddImportsVisitor, RemoveImportsVisitor
from libcst.metadata.full_repo_manager import FullRepoManager
from libcst.metadata.name_provider import FullyQualifiedNameProvider
from libcst.metadata.scope_provider import (
    QualifiedName,
    QualifiedNameSource,
)

AURELIA_ROOT = Path("/src")


POSSIBLE_REMOVED_IMPORTS: set["AddImport"] = set()
REMOVED_NODES: set[Optional[cst.CSTNode]] = set()
IS_REMOVING_NODE = False


@cache
def _to_file(module: str) -> str:
    """Convert a Python module to a Python filename.

    >>> _to_file("benchling.notebook.models.entry")
    Path('benchling.notebook.models.entry.py')
    """
    filename = module.replace(".", "/") + ".py"
    return filename


@dataclass
class Symbol:
    module: str
    name: str

    @classmethod
    def from_qualified_name(cls, s: str) -> "Symbol":
        assert "." in s, "Qualified symbol name must be of the form module.name"
        module, name = s.rsplit(".", 1)
        return cls(module, name)


@dataclass(frozen=True)
class AddImport:
    module: str
    obj: Optional[str]
    asname: Optional[str]


def iter_all_children(node: cst.CSTNode) -> Iterable[cst.CSTNode]:
    """Collect all nodes in the tree."""
    yield node
    for child in node.children:
        yield from iter_all_children(child)


class RemoveSymbolsVisitor(VisitorBasedCodemodCommand):
    """Remove Symbols in GlobalScope listed in `symbols_to_remove`.

    We exit before entering any `BaseCompoundStatement` (if, try, with, for, while, def, class),
    so some "globals" like `if True: x = 1` are ignored as well.

    Associated imports are collected on the scratch context.
    These can be used to add missing imports when moving the imports.
    """

    CONTEXT_KEY = "RemoveSymbolsVisitor"
    METADATA_DEPENDENCIES = (FullyQualifiedNameProvider,)

    def _add_associated_import(self, name: str) -> None:
        self.context.scratch[self.CONTEXT_KEY]["imports"].add(name)

    def _collect_associated_imports(self, nodes: set[cst.CSTNode]) -> None:
        # TODO: CAHNGE THIS FUNCTION NAME
        self.context.scratch[self.CONTEXT_KEY]["nodes"] |= nodes

        qnames: set[QualifiedName] = set()
        for node in nodes:
            for child in iter_all_children(node):
                qnames |= self.get_metadata(FullyQualifiedNameProvider, child, set())

        for qname in qnames:
            if qname.source == QualifiedNameSource.IMPORT:
                # TODO: asname
                self._add_associated_import(qname.name)
                module, obj = qname.name.rsplit(".", 1)
                RemoveImportsVisitor.remove_unused_import(self.context, module, obj)
            elif qname.source == QualifiedNameSource.LOCAL:
                xx = qname.name.removeprefix(self.context.full_module_name + ".")
                if "." not in xx and xx not in self.symbols_to_remove:
                    self._add_associated_import(qname.name)

    def __init__(self, context: CodemodContext, symbols_to_remove: set[str]) -> None:
        super().__init__(context)
        self.symbols_to_remove: set[str] = symbols_to_remove
        self._removed: set[
            Union[cst.FunctionDef, cst.ClassDef, cst.SimpleStatementLine]
        ] = set()
        self.context.scratch[self.CONTEXT_KEY] = {
            "imports": set(),
            "nodes": set(),
        }

    def visit_FunctionDef(self, node: cst.FunctionDef) -> Optional[bool]:
        return False

    def visit_ClassDef(self, node: cst.FunctionDef) -> Optional[bool]:
        return False

    def visit_If(self, node: cst.If) -> Optional[bool]:
        return False

    def visit_Try(self, node: cst.Try) -> Optional[bool]:
        return False

    def visit_With(self, node: cst.With) -> Optional[bool]:
        return False

    def visit_For(self, node: cst.For) -> Optional[bool]:
        return False

    def visit_While(self, node: cst.While) -> Optional[bool]:
        return False

    def leave_FunctionDef(
        self, original_node: cst.FunctionDef, updated_node: cst.FunctionDef
    ) -> Union[
        cst.BaseStatement, cst.FlattenSentinel[cst.BaseStatement], cst.RemovalSentinel
    ]:
        if original_node.name.value in self.symbols_to_remove:
            self._removed.add(original_node)
            return cst.RemoveFromParent()
        return super().leave_FunctionDef(original_node, updated_node)

    def leave_ClassDef(
        self, original_node: cst.ClassDef, updated_node: cst.ClassDef
    ) -> Union[
        cst.BaseStatement, cst.FlattenSentinel[cst.BaseStatement], cst.RemovalSentinel
    ]:
        if original_node.name.value in self.symbols_to_remove:
            self._removed.add(original_node)
            return cst.RemoveFromParent()
        return super().leave_ClassDef(original_node, updated_node)

    def leave_SimpleStatementLine(
        self,
        original_node: cst.SimpleStatementLine,
        updated_node: cst.SimpleStatementLine,
    ) -> Union[
        cst.BaseStatement, cst.FlattenSentinel[cst.BaseStatement], cst.RemovalSentinel
    ]:
        for node in original_node.body:
            if isinstance(node, cst.Assign):
                for assign_target in node.targets:
                    target = assign_target.target
                    if (
                        isinstance(target, cst.Name)
                        and target.value in self.symbols_to_remove
                    ):
                        return cst.RemoveFromParent()

            if isinstance(node, cst.AnnAssign):
                target = node.target
                if (
                    isinstance(target, cst.Name)
                    and target.value in self.symbols_to_remove
                ):
                    return cst.RemoveFromParent()

        return super().leave_SimpleStatementLine(original_node, updated_node)

    def leave_Module(
        self, original_node: cst.Module, updated_node: cst.Module
    ) -> cst.Module:
        self._collect_associated_imports(self._removed)
        return super().leave_Module(original_node, updated_node)


class AddSymbolsVisitor(VisitorBasedCodemodCommand):
    def __init__(
        self,
        context: CodemodContext,
        symbols_to_add: set[
            Union[cst.FunctionDef, cst.ClassDef, cst.SimpleStatementLine]
        ],
        imports_to_add: set[str],
    ) -> None:
        super().__init__(context)
        self.symbols_to_add = symbols_to_add
        self.imports_to_add = imports_to_add

    def leave_Module(
        self, original_node: cst.Module, updated_node: cst.Module
    ) -> cst.Module:
        for associated_imports in self.imports_to_add:
            # TODO: asname
            module, obj = associated_imports.rsplit(".", 1)
            AddImportsVisitor.add_needed_import(self.context, module, obj)
        return updated_node.with_changes(
            body=[*updated_node.body, *self.symbols_to_add]
        )


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

    old_file = _to_file(old_module)
    new_file = _to_file(new_module)

    assert Path(old_file).is_file(), f"File {old_file} does not exist"
    if not Path(new_file).exists():
        Path(new_file).parent.mkdir(parents=True, exist_ok=True)
        Path(new_file).touch()
    assert Path(new_file).is_file(), f"File {new_file} does not exist"

    manager = FullRepoManager(
        str(AURELIA_ROOT), [old_file, new_file], [FullyQualifiedNameProvider]
    )
    manager = FullRepoManager(
        str(AURELIA_ROOT), [old_file, new_file], [FullyQualifiedNameProvider]
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
    updated_old_tree = remove_visitor.transform_module(old_context.module)
    Path(old_file).write_text(updated_old_tree.code)

    removed = remove_visitor.context.scratch[RemoveSymbolsVisitor.CONTEXT_KEY]
    nodes_to_add = removed["nodes"]
    imports_to_add = removed["imports"]

    add_visitor = AddSymbolsVisitor(new_context, nodes_to_add, imports_to_add)
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

    grep_for_filenames_command = f"git grep --files-with-matches --extended-regexp '{combined}' {str(AURELIA_ROOT)} | grep -E '\.py$'"
    codemod_command = f"python3 -m libcst.tool codemod replace.ReplaceCodemod --old={old_symbols} --new={new_symbols}"
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


@click.command()
@click.argument("old_qualified_symbol_names", type=click.STRING)
@click.argument("new_qualified_symbol_names", type=click.STRING)
def main(old_qualified_symbol_names: str, new_qualified_symbol_names: str) -> None:
    move_symbol(old_qualified_symbol_names, new_qualified_symbol_names)


if __name__ == "__main__":
    main()
