#!/usr/bin/env python3
from dataclasses import dataclass, field
from typing import Union

import libcst as cst
from libcst.codemod import (
    CodemodContext,
    VisitorBasedCodemodCommand,
)
from libcst.codemod.visitors import AddImportsVisitor


class AddSymbolsVisitor(VisitorBasedCodemodCommand):
    DESCRIPTION: str = "Adds symbols to a module."

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
