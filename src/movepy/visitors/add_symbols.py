from typing import List, Union

import libcst as cst
from libcst.codemod import (
    CodemodContext,
    VisitorBasedCodemodCommand,
)
from libcst.codemod.visitors import AddImportsVisitor, ImportItem

Imports = Union[cst.Import, cst.ImportFrom]
Definitions = Union[cst.FunctionDef, cst.ClassDef, cst.SimpleStatementLine]


class AddSymbolsVisitor(VisitorBasedCodemodCommand):
    DESCRIPTION: str = "Adds symbols to a module."

    def __init__(
        self,
        context: CodemodContext,
        nodes_to_add: set[Union[Imports, Definitions]],
        imports_to_add: set[ImportItem],
    ) -> None:
        super().__init__(context)
        self.nodes_to_add = nodes_to_add
        self.imports_to_add = imports_to_add

    def leave_Module(
        self, original_node: cst.Module, updated_node: cst.Module
    ) -> cst.Module:
        for item in self.imports_to_add:
            AddImportsVisitor.add_needed_import(
                self.context, item.module, item.obj_name, item.alias
            )

        imports: List[Imports] = []
        defintions: List[Definitions] = []
        for node in self.nodes_to_add:
            if isinstance(node, (cst.Import, cst.ImportFrom)):
                imports.append(node)
            else:
                defintions.append(node)

        wrapped_imports: List[cst.SimpleStatementLine] = [
            cst.SimpleStatementLine(body=[i]) for i in imports
        ]

        return updated_node.with_changes(
            body=[*wrapped_imports, *updated_node.body, *defintions]
        )
