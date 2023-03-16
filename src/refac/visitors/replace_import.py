#!/usr/bin/env python3
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Type, Union

import libcst as cst
from libcst.codemod import (
    Codemod,
    CodemodCommand,
    CodemodContext,
    VisitorBasedCodemodCommand,
)
from libcst.helpers import get_full_name_for_node
from libcst.metadata import Assignment, ScopeProvider
from libcst.metadata.scope_provider import QualifiedNameSource, Scope

from .import_utils import Import
from .inplace_replace_import import InplaceReplaceImportVisitor

# Possible refactors:
#  - Add a AddCommentVisitor


@dataclass
class Pair:
    """Tranforms an import from `old` to `new`."""

    context: CodemodContext
    old: Import
    new: Import
    format_str: Optional[str]
    new_format: Optional[Import] = field(init=False)

    def __post_init__(self) -> None:
        if self.format_str is None:
            new_format = None
        else:
            format_node = cst.ensure_type(
                cst.parse_statement(self.format_str), cst.SimpleStatementLine
            )
            new_format = Import.create(self.context, format_node.body[0])

        if new_format is not None and not self.new.name.startswith(new_format.name):
            raise Exception("When specified, `format` must share a prefix with `new`.")
        self.new_format = new_format


class ReplaceImportCodemod(VisitorBasedCodemodCommand):
    """Replace any Python symbol with another.

    Example:
      ## before
      from a.b import c
      c.fn()

      ## after: python3 -m libcst.tool codemod replace.ReplaceImportCodemod --old=a.b.c --new=x.y.z <filename>
      from x.y import z
      z.fn()

    This is similar to libcst's RenameCommand, but has a few different features:
      1. Supports custom formatting with aliases (using --format)
      3. Imports get changed inplace (rather than adding to top of file).
      4. Supports multiple replaces in one invocation (see example invocation below).

    Command-line ImportMetadata:
        python3 -m libcst.tool codemod replace.ReplaceImportCodemod --old=a.b.c --new=x.y.z <file_or_directory>
        python3 -m libcst.tool codemod replace.ReplaceImportCodemod --old=a.b.c --new=x.y.z --format "from x.y import z as a" <file_or_directory>
        python3 -m libcst.tool codemod replace.ReplaceImportCodemod --old="a.b.c,d.e.f" --new="x.y.z,q.r.s" --format "from x.y import z as a,from q.r import s" <file_or_directory>
    """

    CONTEXT_KEY = "ReplaceImportCodemod"
    DESCRIPTION = "Replace any Python symbol with another"
    METADATA_DEPENDENCIES = (ScopeProvider,)

    @staticmethod
    def add_args(arg_parser):
        arg_parser.add_argument(
            "--old",
            dest="old",
            metavar="OLD",
            help="Module to be replace",
            type=str,
            required=True,
        )
        arg_parser.add_argument(
            "--new",
            dest="new",
            metavar="NEW",
            help="New module to use in place of old",
            type=str,
            required=True,
        )
        arg_parser.add_argument(
            "--format",
            dest="format",
            metavar="FORMAT",
            help="Format for new module (e.g. 'from a import b as c')",
            type=str,
            default=None,
        )

    def __init__(
        self,
        context: CodemodContext,
        old: str,
        new: str,
        format: Optional[str],
    ):
        super().__init__(context)
        olds = [x.strip() for x in old.split(",")]
        news = [x.strip() for x in new.split(",")]
        formats: list[Optional[str]] = (
            [x.strip() for x in format.split(",")]
            if format is not None
            else [None] * len(news)
        )
        if len(olds) != len(news):
            raise ValueError(
                f"`old` and `new` must be the same length. Got {len(olds)} and {len(news)}."
            )
        if len(news) != len(formats):
            raise ValueError(
                f"`format` must be the same length as `new` or empty. Got {len(formats)} and {len(news)}."
            )

        pairs = [
            Pair(context, Import(olds[i]), Import(news[i]), formats[i])
            for i in range(len(olds))
        ]
        self.pairs = [p for p in pairs if p.old != p.new or p.new_format is not None]

        # When present, adds a comment on nearest cst.SimpleStatementLine
        self.add_comment: str = ""

    def transform_module(self, tree: cst.Module) -> cst.Module:
        # Not calling naive super() to skip the `CodemodCommand.transform_module`
        tree = super(CodemodCommand, self).transform_module(tree)

        supported_transforms: Dict[str, Type[Codemod]] = {
            InplaceReplaceImportVisitor.CONTEXT_KEY: InplaceReplaceImportVisitor,
        }

        for key, transform in supported_transforms.items():
            if key in self.context.scratch:
                tree = self._instantiate_and_run(transform, tree)

        return tree

    def visit_Module(self, node: cst.Module) -> bool:
        if len(self.pairs) == 0:
            # Nothing to change, so exit early.
            return False
        return True

    def visit_Import(self, node: cst.Import) -> bool:
        self.fix_matching_and_unused_import(node)
        return False

    def visit_ImportFrom(self, node: cst.ImportFrom) -> bool:
        self.fix_matching_and_unused_import(node)
        return False

    def visit_Attribute(self, node: cst.Attribute) -> bool:
        # For an attribute `a.b.c`, we only want to visit the top level.
        # Return `False` to stop exploring traversal and skip children like `a.b`.
        if is_simple_attribute(node):
            return False
        return True

    def fix_matching_and_unused_import(
        self, node: Union[cst.Import, cst.ImportFrom]
    ) -> None:
        scope = self.get_metadata(ScopeProvider, node)
        imports = Import.bulk_create(self.context, node)
        unused_imports: List[Import] = []
        for old_import in imports:
            is_unused = all(len(assignment.references) == 0 for assignment in scope[old_import.key])  # type: ignore[index]
            if is_unused:
                unused_imports.append(old_import)

        matches: List[Tuple[Import, Pair]] = []
        for old_import in unused_imports:
            for pair in self.pairs:
                if pair.old.match(old_import.name):
                    matches.append((old_import, pair))
                    break

        for (old_import, pair) in matches:
            rest = old_import.name.removeprefix(pair.old.name)  # type: ignore
            origin = "Import" if isinstance(node, cst.Import) else "ImportFrom"
            new_import = Import(f"{pair.new.name}{rest}").format(origin)
            self.check_for_variable_shadowing(scope, old_import, new_import)  # type: ignore[arg-type]
            InplaceReplaceImportVisitor.replace_import(
                self.context, old_import, new_import
            )

    def leave_Name(self, original: cst.Name, updated: cst.Name) -> cst.BaseExpression:
        return self.fix_name_or_attribute(original, updated)

    def leave_Attribute(
        self, original: cst.Attribute, updated: cst.Attribute
    ) -> cst.BaseExpression:
        return self.fix_name_or_attribute(original, updated)

    def leave_SimpleStatementLine(
        self, original: cst.SimpleStatementLine, updated: cst.SimpleStatementLine
    ) -> cst.SimpleStatementLine:
        if self.add_comment:
            comment = self.add_comment
            self.add_comment = ""
            return updated.with_deep_changes(
                old_node=updated.trailing_whitespace,
                whitespace=cst.SimpleWhitespace("  "),
                comment=cst.Comment(comment),
            )
        return updated

    def fix_name_or_attribute(
        self,
        original: Union[cst.Name, cst.Attribute],
        updated: Union[cst.Name, cst.Attribute],
    ) -> cst.BaseExpression:
        if not is_simple_attribute(original):
            return updated

        try:
            scope = self.get_metadata(ScopeProvider, original)
        except KeyError:
            return updated
        if scope is None:
            return updated

        for pair in self.pairs:
            old_import = self.get_old_import(scope, original, pair)
            if not old_import:
                continue
            old_usage = get_full_name_for_node(original)
            (new_import, new_usage) = self.get_new_import_and_usage(old_import, old_usage, pair)  # type: ignore[arg-type]

            # Check if we are going to introduce variable shadowing
            # if old_usage != new_usage:
            self.check_for_variable_shadowing(scope, old_import, new_import)

            InplaceReplaceImportVisitor.replace_import(
                self.context, old_import, new_import
            )

            return cst.parse_expression(
                new_usage,
                config=self.context.module.config_for_parsing,  # type: ignore[union-attr]
            )
        return updated

    def get_old_import(
        self, scope: Scope, original: Union[cst.Name, cst.Attribute], pair: Pair
    ) -> Optional[Import]:
        is_imported = QualifiedNameSource.IMPORT in {
            qn.source for qn in scope.get_qualified_names_for(original)
        }
        if not is_imported:
            return None

        old_usage = get_full_name_for_node(original)
        key, *_ = old_usage.split(".", 1)  # type: ignore[union-attr]
        assignments = scope[key]

        import_nodes = {
            a.node
            for a in assignments
            if isinstance(a, Assignment)
            and isinstance(a.node, (cst.Import, cst.ImportFrom))
        }

        def is_possible_old_import(im: Import) -> bool:
            # Usage must match key or usage must match a module path.
            if old_usage != im.key and not old_usage.removeprefix(im.key).startswith("."):  # type: ignore[union-attr]
                return False
            qname = get_fully_qualified_name(im, old_usage)  # type: ignore[arg-type]
            return pair.old.match(qname)

        possible_imports = [
            im
            for node in import_nodes
            for im in Import.bulk_create(self.context, node)
            if is_possible_old_import(im)
        ]

        if not possible_imports:
            return None

        if len(assignments) > 1:
            msg = (
                "# TODO(FIXME): Cannot replace due to variable shadowing. Fix manually."
            )
            self.add_comment += msg
            return None

        return possible_imports[0]

    def get_new_import_and_usage(
        self, old_import: Import, old_usage: str, pair: Pair
    ) -> Tuple[Import, str]:
        old_qname = get_fully_qualified_name(old_import, old_usage)
        new_qname = old_qname.replace(pair.old.name, pair.new.name)
        origin = old_import.origin

        # Use the specificed `new_format` to format the new import if it exists.
        if pair.new_format:
            new_import = pair.new_format

        # Replace part of an existing import.
        # e.g `from a import b as y;y` :: (a -> x) :: `from x import b as y;y``
        elif old_import.name.startswith(pair.old.name + "."):
            module = f"{pair.new.name}{old_import.name.removeprefix(pair.old.name)}"  # type: ignore
            new_import = Import(module=module, asname=old_import.asname).format(origin)

        # Replace entire Import.
        # e.g `import a.b;a.b` :: (a.b -> x.y) :: `import x.y;x.y`
        elif origin == "Import":
            new_import = pair.new.format(origin)

        # Replace entire ImportFrom. Try and match number of dots in usage.
        # e.g `from a import b; b.c.d` :: (a.b -> x.y) :: `from x import y; y.c.d`
        # e.g `from a import b; b.c.d` :: (a.b -> x) :: `import x; x.c.d`
        elif origin == "ImportFrom":
            num_dots = old_usage.count(".")
            module, *_ = new_qname.rsplit(".", num_dots)
            new_import = Import(module).format(origin)

        new_usage = f"{new_import.key}{new_qname.removeprefix(new_import.name)}"  # type: ignore
        return (new_import, new_usage)

    def check_for_variable_shadowing(
        self, scope: Scope, old_import: Import, new_import: Import
    ) -> None:
        if old_import.key == new_import.key:
            return

        key = new_import.key
        is_already_used = key in scope.accesses  # len(scope.accesses[key]) != 0
        is_already_defined = (
            key in scope.assignments
        )  # len(scope.assignments[key]) != 0
        if is_already_used or is_already_defined:
            msg = f"# TODO(FIXME): Adding {new_import.name!r} may have introduced shadowing."
            if is_already_used:
                msg += f" {key!r} was already used in this scope."
            if is_already_defined:
                msg += f" {key!r} was already defined in this scope."
            self.add_comment += msg


def get_fully_qualified_name(im: Import, usage: str) -> str:
    if not usage.startswith(im.key):
        raise Exception(
            f"{usage} must start with {im.key} to have a qualified name with {im}"
        )
    import_part = im.name
    usage_part = usage.removeprefix(im.key)  # type: ignore
    return f"{import_part}{usage_part}"


def is_simple_attribute(node: cst.BaseExpression) -> bool:
    """A simple attribute is a dotted expression made of cst.Name nodes.

    >>> is_simple_attribute(cst.parse_expression("a.b.c"))
    True

    >>> is_simple_attribute(cst.parse_expression("a().b"))
    False
    """
    if isinstance(node, cst.Name):
        return True
    if isinstance(node, cst.Attribute):
        return is_simple_attribute(node.value)
    return False
