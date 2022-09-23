#!/usr/bin/env python3
from typing import Iterable, Optional, Union

import libcst as cst
from libcst.codemod import (
    CodemodContext,
    VisitorBasedCodemodCommand,
)
from libcst.codemod.visitors import RemoveImportsVisitor
from libcst.metadata.scope_provider import (
    QualifiedName,
    QualifiedNameSource,
)
from libcst.codemod._context import CodemodContext
from libcst.metadata.name_provider import FullyQualifiedNameProvider


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

    def _collect_associated_imports(
        self, nodes: set[Union[cst.FunctionDef, cst.ClassDef, cst.SimpleStatementLine]]
    ) -> None:
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
                full_module_name = self.context.full_module_name
                assert full_module_name, "Context missing `full_module_name`"
                xx = qname.name.removeprefix(full_module_name + ".")
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

    def visit_ClassDef(self, node: cst.ClassDef) -> Optional[bool]:
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


def iter_all_children(node: cst.CSTNode) -> Iterable[cst.CSTNode]:
    """Collect all nodes in the tree."""
    yield node
    for child in node.children:
        yield from iter_all_children(child)
