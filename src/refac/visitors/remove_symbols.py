from typing import Optional, Union

import libcst as cst
from libcst.codemod import (
    CodemodContext,
    VisitorBasedCodemodCommand,
)
from libcst.codemod._visitor import ContextAwareVisitor
from libcst.codemod.visitors import (
    RemoveImportsVisitor,
    ImportItem,
)
from libcst.metadata.scope_provider import (
    ScopeProvider,
    ImportAssignment,
    Assignment,
)
from libcst.helpers import get_full_name_for_node_or_raise
from libcst.metadata.name_provider import FullyQualifiedNameProvider


class CollectAssociatedImportsVisitor(ContextAwareVisitor):
    def __init__(self, context: CodemodContext, symbols_to_remove: set[str]) -> None:
        super().__init__(context)
        self.symbols_to_remove = symbols_to_remove
        metadata_wrapper = self.context.wrapper
        if metadata_wrapper is None:
            raise Exception("Cannot look up scope, metadata is not computed for node!")
        self.scope_provider = metadata_wrapper.resolve(ScopeProvider)

    def collect(self, node: Union[cst.Name, cst.Attribute]) -> None:
        scope = self.scope_provider.get(node)
        if scope is None:
            return

        name = get_full_name_for_node_or_raise(node)
        if name in self.symbols_to_remove:
            return

        for assignment in scope[name]:
            if isinstance(assignment, ImportAssignment):
                if assignment.scope == scope.globals:
                    if isinstance(assignment.node, (cst.Import, cst.ImportFrom)):
                        RemoveImportsVisitor.remove_unused_import_by_node(
                            self.context, assignment.node
                        )
                        RemoveSymbolsVisitor.add_associated_import_by_node(
                            self.context, assignment.node, name
                        )
            elif (
                isinstance(assignment, Assignment) and assignment.scope == scope.globals
            ):
                RemoveSymbolsVisitor.add_associated_import(
                    self.context, ImportItem(self.context.full_module_name, name, None)
                )

    def visit_Name(self, node: cst.Name) -> Optional[bool]:
        self.collect(node)
        return True

    def visit_Attribute(self, node: cst.Attribute) -> Optional[bool]:
        self.collect(node)
        return True


class RemoveSymbolsVisitor(VisitorBasedCodemodCommand):
    """Remove Symbols in GlobalScope listed in `symbols_to_remove`.

    We exit before entering any `BaseCompoundStatement` (if, try, with, for, while, def, class),
    so some "globals" like `if True: x = 1` are ignored as well.

    Associated imports are collected on the scratch context.
    These can be used to add missing imports when moving the imports.
    """

    CONTEXT_KEY = "RemoveSymbolsVisitor"
    METADATA_DEPENDENCIES = (FullyQualifiedNameProvider, ScopeProvider)

    @classmethod
    def add_removed_node(cls, context: CodemodContext, node: cst.CSTNode) -> None:
        context.scratch[cls.CONTEXT_KEY]["nodes"].add(node)

    @classmethod
    def add_associated_import(cls, context: CodemodContext, item: ImportItem) -> None:
        context.scratch[cls.CONTEXT_KEY]["imports"].add(item)

    @classmethod
    def add_associated_import_by_node(
        cls,
        context: CodemodContext,
        node: Union[cst.Import, cst.ImportFrom],
        name: str,
    ) -> None:
        if isinstance(node, cst.Import):
            for import_name in node.names:
                if (
                    import_name.evaluated_alias == name
                    or import_name.evaluated_name == name
                ):
                    cls.add_associated_import(
                        context,
                        ImportItem(
                            import_name.evaluated_name,
                            None,
                            import_name.evaluated_alias,
                        ),
                    )
        elif isinstance(node, cst.ImportFrom):
            if isinstance(node.names, cst.ImportStar):
                return
            for import_name in node.names:
                if (
                    import_name.evaluated_alias == name
                    or import_name.evaluated_name == name
                ):
                    cls.add_associated_import(
                        context,
                        ImportItem(
                            get_full_name_for_node_or_raise(node.module)
                            if node.module is not None
                            else "",
                            import_name.evaluated_name,
                            import_name.evaluated_alias,
                            len(node.relative),
                        ),
                    )

    def __init__(self, context: CodemodContext, symbols_to_remove: set[str]) -> None:
        super().__init__(context)
        assert all(
            "." not in symbol for symbol in symbols_to_remove
        ), "Cannot remove symbols with '.' in them"
        self.symbols_to_remove: set[str] = symbols_to_remove
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
            self.add_removed_node(self.context, original_node)
            original_node.visit(
                CollectAssociatedImportsVisitor(self.context, self.symbols_to_remove)
            )
            return cst.RemoveFromParent()
        return super().leave_FunctionDef(original_node, updated_node)

    def leave_ClassDef(
        self, original_node: cst.ClassDef, updated_node: cst.ClassDef
    ) -> Union[
        cst.BaseStatement, cst.FlattenSentinel[cst.BaseStatement], cst.RemovalSentinel
    ]:
        if original_node.name.value in self.symbols_to_remove:
            self.add_removed_node(self.context, original_node)
            original_node.visit(
                CollectAssociatedImportsVisitor(self.context, self.symbols_to_remove)
            )
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
                        self.add_removed_node(self.context, original_node)
                        return cst.RemoveFromParent()

            if isinstance(node, cst.AnnAssign):
                target = node.target
                if (
                    isinstance(target, cst.Name)
                    and target.value in self.symbols_to_remove
                ):
                    self.add_removed_node(self.context, original_node)
                    return cst.RemoveFromParent()

        return super().leave_SimpleStatementLine(original_node, updated_node)

    def leave_Import(
        self, original_node: cst.Import, updated_node: cst.Import
    ) -> Union[
        cst.BaseSmallStatement,
        cst.FlattenSentinel[cst.BaseSmallStatement],
        cst.RemovalSentinel,
    ]:
        # TODO: Handle removing by alias
        for node in original_node.names:
            if node.evaluated_name in self.symbols_to_remove:
                self.add_removed_node(
                    self.context,
                    cst.Import(names=[cst.ImportAlias(node.name, node.asname)]),
                )
        remaining_names = [
            cst.ImportAlias(node.name, node.asname)
            for node in original_node.names
            if node.evaluated_name not in self.symbols_to_remove
        ]
        if len(remaining_names) == 0:
            return cst.RemoveFromParent()
        else:
            return updated_node.with_changes(names=remaining_names)

    def leave_ImportFrom(
        self, original_node: cst.ImportFrom, updated_node: cst.ImportFrom
    ) -> Union[
        cst.BaseSmallStatement,
        cst.FlattenSentinel[cst.BaseSmallStatement],
        cst.RemovalSentinel,
    ]:
        if isinstance(original_node.names, cst.ImportStar):
            return super().leave_ImportFrom(original_node, updated_node)

        # TODO: Handle removing by alias
        for node in original_node.names:
            if node.evaluated_name in self.symbols_to_remove:
                self.add_removed_node(
                    self.context,
                    cst.ImportFrom(
                        module=original_node.module,
                        names=[node],
                        relative=original_node.relative,
                    ),
                )
        remaining_names = [
            cst.ImportAlias(node.name, node.asname)
            for node in original_node.names
            if node.evaluated_name not in self.symbols_to_remove
        ]
        if len(remaining_names) == 0:
            return cst.RemoveFromParent()
        else:
            return updated_node.with_changes(names=remaining_names)
