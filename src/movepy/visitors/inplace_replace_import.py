#!/usr/bin/env python3
from typing import cast, Optional, Sequence, Set, Tuple, Union

import libcst as cst
from libcst.codemod import CodemodContext, ContextAwareTransformer
from libcst.metadata import ScopeProvider
from libcst.metadata.scope_provider import Scope

from .import_utils import Import


class InplaceReplaceImportVisitor(ContextAwareTransformer):
    """Replace `remove` with `add`.

    Compared with AddImportsVisitor and RemoveImportsVisitor, this visitor
    will try and keep the import modification in the same place (instead
    of moving the imports to the top of the file.)

    For example::

        InplaceReplaceImportVisitor.replace_import(self.context, "a.b", "x.y")

    Will make the following transformation:

        ## before
        def fn():
          from x import y

        ## after
        def fn():
          from a import b
    """

    CONTEXT_KEY = "InplaceReplaceImportVisitor"
    METADATA_DEPENDENCIES = (ScopeProvider,)

    @staticmethod
    def replace_import(context: CodemodContext, remove: Import, add: Import) -> None:
        replacements = context.scratch.get(
            InplaceReplaceImportVisitor.CONTEXT_KEY, set()
        )
        replacements.add((remove, add))
        context.scratch[InplaceReplaceImportVisitor.CONTEXT_KEY] = replacements

    def __init__(
        self,
        context: CodemodContext,
        replacements: Optional[Set[Tuple[Import, Import]]] = None,
    ):
        super().__init__(context)
        self.replacements = context.scratch.get(
            InplaceReplaceImportVisitor.CONTEXT_KEY, set()
        ).union(replacements or set())
        self.scheduled_replacements = {
            remove: add for (remove, add) in self.replacements
        }
        self.scheduled_additions: Set[Import] = set()

    def leave_ImportFrom(
        self, original: cst.ImportFrom, updated: cst.ImportFrom
    ) -> Union[cst.Import, cst.ImportFrom, cst.RemovalSentinel]:
        return self._replace_import(original, updated)

    def leave_Import(
        self, original: cst.Import, updated: cst.Import
    ) -> Union[cst.Import, cst.ImportFrom, cst.RemovalSentinel]:
        return self._replace_import(original, updated)

    def _replace_import(
        self,
        original: Union[cst.Import, cst.ImportFrom],
        updated: Union[cst.Import, cst.ImportFrom],
    ) -> Union[cst.Import, cst.ImportFrom, cst.RemovalSentinel]:
        imports = Import.bulk_create(self.context, updated)
        removes = (im for im in imports if im in self.scheduled_replacements)
        for remove in sorted(removes, key=lambda im: im.key):
            add = self.scheduled_replacements[remove]
            self.scheduled_additions.add(add)

            can_remove = add.key == remove.key or self.is_unused(original, remove)
            if can_remove:
                updated, remove_sentinal = self._remove_import(remove, updated)
                if remove_sentinal:
                    return remove_sentinal
        return updated

    def _remove_import(
        self, remove: Import, updated: Union[cst.Import, cst.ImportFrom]
    ) -> Tuple[Union[cst.Import, cst.ImportFrom], Optional[cst.RemovalSentinel]]:
        aliases = cast(Sequence[cst.ImportAlias], updated.names)
        if len(aliases) == 1:
            return updated, cst.RemoveFromParent()
        else:
            if isinstance(updated, cst.ImportFrom):
                remove_name = remove.obj or remove.module
            elif isinstance(updated, cst.Import):
                remove_name = remove.module
            changes = {
                "names": [
                    cst.ImportAlias(name=alias.name, asname=alias.asname)
                    for alias in aliases
                    if alias.evaluated_name != remove_name
                ]
            }
            return updated.with_changes(**changes), None

    def leave_SimpleStatementLine(
        self, original: cst.SimpleStatementLine, updated: cst.SimpleStatementLine
    ) -> cst.SimpleStatementLine:
        if not self.scheduled_additions:
            return updated
        additions = self.scheduled_additions.copy()
        self.scheduled_additions = set()
        changes = {
            "body": (
                *updated.body,
                *[add.to_libcst_node(self.context) for add in sorted(additions, key=lambda i: i.name)],
            )
        }
        return updated.with_changes(**changes)

    def is_unused(
        self, node: Union[cst.Import, cst.ImportFrom], remove: Import
    ) -> bool:
        try:
            scope: Optional[Scope] = self.get_metadata(ScopeProvider, node)
        except KeyError:
            return True
        return all(len(assignment.references) == 0 for assignment in scope[remove.key])  # type: ignore[index]
