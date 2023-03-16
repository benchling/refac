from dataclasses import dataclass
from typing import Any, cast, List, Literal, Optional, Sequence, Union

import libcst as cst
from libcst.codemod import CodemodContext
from libcst.helpers import get_absolute_module_for_import_or_raise

from refac.utils import to_file


@dataclass(frozen=True)
class Import:
    """Represents a single import.

    The import statement `from a.b import c,d` refers to two imports: a.b.c, a.b.d

    TODO: Consider replaceing with libcst.visitors.ImportItem
    """

    module: str
    obj: Optional[str] = None
    asname: Optional[str] = None

    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, Import):
            return False
        return self.name == other.name

    @property
    def parts(self) -> List[str]:
        parts = self.module.split(".")
        if self.obj:
            parts += [self.obj]
        return parts

    @property
    def name(self) -> str:
        return ".".join(self.parts)

    @property
    def key(self) -> str:
        """Part of the import used when referencing the import in code.

        from a import b      -> b
        from a import b as c -> c
        import a.b           -> a.b
        """
        if self.asname:
            return self.asname
        elif self.obj:
            return self.obj
        else:
            return self.module

    @property
    def origin(self) -> Literal["Import", "ImportFrom"]:
        return "ImportFrom" if self.obj is not None else "Import"

    @classmethod
    def create(cls, context: CodemodContext, node: cst.CSTNode) -> "Import":
        if not isinstance(node, (cst.Import, cst.ImportFrom)):
            raise Exception(
                f"Expected a cst.Import or cst.ImportFrom node. Got: {type(node)}"
            )
        imports = Import.bulk_create(context, node)
        if len(imports) > 1:
            raise Exception("Expected to find 1 import from node.")
        return imports[0]

    @classmethod
    def bulk_create(
        cls, context: CodemodContext, node: Union[cst.ImportFrom, cst.Import]
    ) -> List["Import"]:
        imports: List["Import"] = []
        if isinstance(node, cst.ImportFrom):
            if isinstance(node.names, cst.ImportStar):
                print("Ignoring ImportStar import")
                return []

            module = get_absolute_module_for_import(context, node)
            for alias_node in cast(Sequence[cst.ImportAlias], node.names):
                imports.append(
                    Import(
                        module, alias_node.evaluated_name, alias_node.evaluated_alias
                    )
                )
        else:
            for alias_node in node.names:
                imports.append(
                    Import(alias_node.evaluated_name, None, alias_node.evaluated_alias)
                )
        return imports

    def format(self, origin: str) -> "Import":
        if origin == "Import" or len(self.parts) == 1:
            return Import(self.name, None, self.asname)
        elif origin == "ImportFrom":
            return Import(".".join(self.parts[:-1]), self.parts[-1], self.asname)
        raise Exception(f"Unknown origin: {origin}")
    
    def match(self, qname: str) -> bool:
        """True if `self` is a valid way to import the `qname` symbol.
        
        >>> Import("a", "b"), "a.b")
        True
        >>> Import("a", "b"), "a.b.c")
        True
        >>> Import("a", "b"), "a.b.c.d")
        True
        >>> Import("a", "b", "a.bc")
        False
        """
        return self.name == qname or qname.startswith(f"{self.name}.")
        

    def to_libcst_node(
        self, context: CodemodContext
    ) -> Union[cst.Import, cst.ImportFrom]:
        def parse(s: str) -> cst.Name:
            return cast(cst.Name, cst.parse_expression(s, config=context.module.config_for_parsing))  # type: ignore[union-attr]

        if self.obj:
            return cst.ImportFrom(
                module=parse(self.module),
                names=[
                    cst.ImportAlias(
                        name=parse(self.obj),
                        asname=cst.AsName(name=parse(self.asname))
                        if self.asname
                        else None,
                    )
                ],
            )
        else:
            return cst.Import(
                names=[
                    cst.ImportAlias(
                        name=parse(self.module),
                        asname=cst.AsName(name=parse(self.asname))
                        if self.asname
                        else None,
                    )
                ]
            )

    @property
    def is_symbol(self) -> bool:
        """True if the last part of the import refers to a symbol, not a module.

        >>> Import('foo.bar.baz').is_symbol
        True
        >>> Import('foo.bar').is_symbol
        False
        """
        if self.name.count(".") == 0:
            return False

        [head, last] = self.name.rsplit(".", 1)
        f = to_file(head, should_already_exist=False)
        return f.is_file() or (
            (f / "__init__.py").is_file() and not (f / f"{last}.py").is_file()
        )

    @property
    def requires_exact_match(self) -> bool:
        """True if this import is a symbol.

        Symbols require exact matches because we're just trying to rename a specific object.
        Modules do not require exact matches because we're trying to renamed a bunch of objects with a shared prefix.

        Examples:
            Symbol #1: a.b.c
            Symbol #2: a.b.cd

            If we try and rename a.b.c, we don't accidentally want to move a.b.cd
            If we try and rename a.b, we want to move both a.b.c and a.b.cd
        """
        return self.is_symbol


def get_absolute_module_for_import(
    context: CodemodContext, node: cst.ImportFrom
) -> str:
    full_module_name = context.full_module_name
    if context.filename.endswith("__init__.py") and node.relative:  # type: ignore[union-attr]
        # The module `a.b` can refer to either `a/b.py` or `a/b/__init__.py`.
        # To correctly disambiguate relative imports from __init__ files, we
        # append an `.__init__` module.
        full_module_name += ".__init__"  # type: ignore[operator]
    return get_absolute_module_for_import_or_raise(full_module_name, node)
