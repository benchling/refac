from typing import Union

import libcst as cst
from libcst.codemod import (
    CodemodContext,
    VisitorBasedCodemodCommand,
)
from libcst.codemod.visitors import AddImportsVisitor, ImportItem


class AddSymbolsVisitor(VisitorBasedCodemodCommand):
    DESCRIPTION: str = "Adds symbols to a module."

    def __init__(
        self,
        context: CodemodContext,
        symbols_to_add: set[
            Union[cst.FunctionDef, cst.ClassDef, cst.SimpleStatementLine]
        ],
        imports_to_add: set[ImportItem],
    ) -> None:
        super().__init__(context)
        self.symbols_to_add = symbols_to_add
        self.imports_to_add = imports_to_add

    def leave_Module(
        self, original_node: cst.Module, updated_node: cst.Module
    ) -> cst.Module:
        for item in self.imports_to_add:
            AddImportsVisitor.add_needed_import(
                self.context, item.module, item.obj_name, item.alias
            )
        return updated_node.with_changes(
            body=[*updated_node.body, *self.symbols_to_add]
        )
