from typing import Any

from libcst.codemod import CodemodContext, CodemodTest

from move_symbol.visitors.replace_import import ReplaceCodemod


class ReplaceCodemodTest(CodemodTest):
    def assertCodemod(
        self,
        before: str,
        after: str,
        *args: Any,
        **kwargs: Any,
    ) -> None:
        old = kwargs.pop("old", None)
        new = kwargs.pop("new", None)
        format = kwargs.pop("format", None)
        exact = kwargs.pop("exact", False)
        context_override = kwargs.pop(
            "context_override", CodemodContext(filename="a.py")
        )
        return super().assertCodemod(
            before,
            after,
            *args,
            old=old,
            new=new,
            format=format,
            exact=exact,
            context_override=context_override,
            **kwargs,
        )


class TestOnlyImportCases(ReplaceCodemodTest):
    TRANSFORM = ReplaceCodemod

    def test_import_only(self):
        for (before_after, old_new) in (
            # `import a`
            (("import a as x", "import x"), ("a", "x")),
            (("import a as y", "import x"), ("a", "x")),
            (("import a", "import a"), ("a", "a")),
            (("import a", "import x"), ("a", "x")),
            (("import a", "import x.y"), ("a", "x.y")),
            # `import a.b`
            (("import a.b as x", "import x"), ("a.b", "x")),
            (("import a.b as y", "import x"), ("a.b", "x")),
            (("import a.b", "import a.b"), ("a.b", "a.b")),
            # (("import a.b", "import a"), ("a.b", "a")),  # TODO: check if this works; add sibling cases
            (("import a.b", "import a.b"), ("b", "x")),
            (("import a.b", "import a.x"), ("a.b", "a.x")),
            (("import a.b", "import x"), ("a.b", "x")),
            (("import a.b", "import x.b"), ("a", "x")),
            (("import a.b", "import x.b"), ("a.b", "x.b")),
            (("import a.b", "import x.y"), ("a.b", "x.y")),
            (("import a.b", "import x.y.z"), ("a.b", "x.y.z")),
            # `import a.b.c`
            (("import a.b.c as x", "import x"), ("a.b.c", "x")),
            (("import a.b.c as y", "import x"), ("a.b.c", "x")),
            (("import a.b.c", "import a.b.c"), ("a.b.c", "a.b.c")),
            (("import a.b.c", "import a.b.c"), ("b", "x.y")),
            (("import a.b.c", "import a.b.c"), ("b.c", "x.y")),
            (("import a.b.c", "import a.b.c"), ("c", "x.y")),
            (("import a.b.c", "import a.b.x"), ("a.b.c", "a.b.x")),
            (("import a.b.c", "import a.x.c"), ("a.b.c", "a.x.c")),
            (("import a.b.c", "import a.x.y"), ("a.b.c", "a.x.y")),
            (("import a.b.c", "import w.x.y.z"), ("a.b.c", "w.x.y.z")),
            (("import a.b.c", "import x"), ("a.b.c", "x")),
            (("import a.b.c", "import x.b.c"), ("a", "x")),
            (("import a.b.c", "import x.b.c"), ("a.b.c", "x.b.c")),
            (("import a.b.c", "import x.c"), ("a.b", "x")),
            (("import a.b.c", "import x.y"), ("a.b.c", "x.y")),
            (("import a.b.c", "import x.y.b.c"), ("a", "x.y")),
            (("import a.b.c", "import x.y.c"), ("a.b", "x.y")),
            (("import a.b.c", "import x.y.c"), ("a.b.c", "x.y.c")),
            (("import a.b.c", "import x.y.z"), ("a.b.c", "x.y.z")),
        ):
            before, after = before_after
            old, new = old_new
            self.assertCodemod(before, after, old=old, new=new)

    def test_importfrom_only(self):
        for (before_after, old_new) in (
            # `from a import b`
            (("from a import b as x", "import x"), ("a.b", "x")),
            (("from a import b as y", "import x"), ("a.b", "x")),
            (("from a import b", "from a import b"), ("a.b", "a.b")),
            (("from a import b", "from a import b"), ("b", "x")),
            (("from a import b", "from a import x"), ("a.b", "a.x")),
            (("from a import b", "from x import b"), ("a", "x")),
            (("from a import b", "from x import b"), ("a.b", "x.b")),
            (("from a import b", "from x import y"), ("a.b", "x.y")),
            (("from a import b", "from x.y import b"), ("a", "x.y")),
            (("from a import b", "from x.y import z"), ("a.b", "x.y.z")),
            (("from a import b", "import x"), ("a.b", "x")),
            # `from a.b import c`
            (("from a.b import c as x", "import x"), ("a.b.c", "x")),
            (("from a.b import c as y", "import x"), ("a.b.c", "x")),
            (("from a.b import c as z", "from x.y import z"), ("a.b.c", "x.y.z")),
            (("from a.b import c", "from a.b import c"), ("a.b.c", "a.b.c")),
            (("from a.b import c", "from a.b import c"), ("b", "a.b.c")),
            (("from a.b import c", "from a.b import x"), ("a.b.c", "a.b.x")),
            (("from a.b import c", "from a.x import c"), ("a.b.c", "a.x.c")),
            (("from a.b import c", "from a.x import y"), ("a.b.c", "a.x.y")),
            (("from a.b import c", "from w.x.y import z"), ("a.b.c", "w.x.y.z")),
            (("from a.b import c", "from x import c"), ("a.b", "x")),
            (("from a.b import c", "from x import y"), ("a.b.c", "x.y")),
            (("from a.b import c", "from x.b import c"), ("a", "x")),
            (("from a.b import c", "from x.b import c"), ("a.b.c", "x.b.c")),
            (("from a.b import c", "from x.y import c"), ("a.b", "x.y")),
            (("from a.b import c", "from x.y import c"), ("a.b.c", "x.y.c")),
            (("from a.b import c", "from x.y import z"), ("a.b.c", "x.y.z")),
            (("from a.b import c", "from x.y.b import c"), ("a", "x.y")),
            (("from a.b import c", "import x"), ("a.b.c", "x")),
        ):
            before, after = before_after
            old, new = old_new
            self.assertCodemod(before, after, old=old, new=new)

    def test_relative_importfrom_only(self):
        for (before_after, old_new) in (
            # `from . import b`
            (("from . import b as x", "import x"), ("a.b", "x")),
            (("from . import b as y", "import x"), ("a.b", "x")),
            (("from . import b", "from . import b"), ("a.b", "a.b")),
            (("from . import b", "from . import b"), ("b", "x")),
            (("from . import b", "from a import x"), ("a.b", "a.x")),
            (("from . import b", "from x import b"), ("a", "x")),
            (("from . import b", "from x import b"), ("a.b", "x.b")),
            (("from . import b", "from x import y"), ("a.b", "x.y")),
            (("from . import b", "from x.y import b"), ("a", "x.y")),
            (("from . import b", "from x.y import z"), ("a.b", "x.y.z")),
            (("from . import b", "import x"), ("a.b", "x")),
            # `from .b import c`
            (("from .b import c as x", "import x"), ("a.b.c", "x")),
            (("from .b import c as y", "import x"), ("a.b.c", "x")),
            (("from .b import c as z", "from x.y import z"), ("a.b.c", "x.y.z")),
            (("from .b import c", "from .b import c"), ("a.b.c", "a.b.c")),
            (("from .b import c", "from .b import c"), ("b", "x")),
            (("from .b import c", "from a.b import x"), ("a.b.c", "a.b.x")),
            (("from .b import c", "from a.x import c"), ("a.b.c", "a.x.c")),
            (("from .b import c", "from a.x import y"), ("a.b.c", "a.x.y")),
            (("from .b import c", "from w.x.y import z"), ("a.b.c", "w.x.y.z")),
            (("from .b import c", "from x import c"), ("a.b", "x")),
            (("from .b import c", "from x import y"), ("a.b.c", "x.y")),
            (("from .b import c", "from x.b import c"), ("a", "x")),
            (("from .b import c", "from x.b import c"), ("a.b.c", "x.b.c")),
            (("from .b import c", "from x.y import c"), ("a.b", "x.y")),
            (("from .b import c", "from x.y import c"), ("a.b.c", "x.y.c")),
            (("from .b import c", "from x.y import z"), ("a.b.c", "x.y.z")),
            (("from .b import c", "from x.y.b import c"), ("a", "x.y")),
            (("from .b import c", "import x"), ("a.b.c", "x")),
        ):
            before, after = before_after
            old, new = old_new
            context = CodemodContext(
                filename="a/some_module.py", full_module_name="a.some_module"
            )
            self.assertCodemod(
                before, after, old=old, new=new, context_override=context
            )


class TestImportNameCases(ReplaceCodemodTest):
    TRANSFORM = ReplaceCodemod

    def test_import_name_usage(self):
        for (before_after, old_new) in (
            # `import a`
            (("import a as x\nx", "import x\nx"), ("a", "x")),
            (("import a as y\ny", "import x\nx"), ("a", "x")),
            (("import a\na", "import a\na"), ("a", "a")),
            (("import a\na", "import x.y\nx.y"), ("a", "x.y")),
            (("import a\na", "import x\nx"), ("a", "x")),
            # `import a.b`
            (("import a.b as x\nx", "import x\nx"), ("a.b", "x")),
            (("import a.b as y\ny", "import a.b as y\ny"), ("b", "x")),
            (("import a.b as y\ny", "import x.b as y\ny"), ("a", "x")),
            (("import a.b as y\ny", "import x.y.b as y\ny"), ("a", "x.y")),
            (("import a.b as y\ny", "import x\nx"), ("a.b", "x")),
            # `import a.b.c`
            (("import a.b.c as x\nx", "import a.b.c as x\nx"), ("b", "x")),
            (("import a.b.c as x\nx", "import x.b.c as x\nx"), ("a", "x")),
            (("import a.b.c as x\nx", "import x.c as x\nx"), ("a.b", "x")),
            (("import a.b.c as x\nx", "import x.y.b.c as x\nx"), ("a", "x.y")),
            (("import a.b.c as x\nx", "import x.y.c as x\nx"), ("a.b", "x.y")),
            (("import a.b.c as x\nx", "import x\nx"), ("a.b.c", "x")),
            (("import a.b.c as y\ny", "import x\nx"), ("a.b.c", "x")),
        ):
            before, after = before_after
            old, new = old_new
            self.assertCodemod(before, after, old=old, new=new)

    def test_importfrom_name_usage(self):
        for (before_after, old_new) in (
            # `from a import b`
            (("from a import b as x\nx", "from x import b as x\nx"), ("a", "x")),
            (("from a import b as x\nx", "import x\nx"), ("a.b", "x")),
            (("from a import b as y\ny", "import x\nx"), ("a.b", "x")),
            (("from a import b\nb", "from a import b\nb"), ("a.b", "a.b")),
            (("from a import b\nb", "from a import b\nb"), ("b", "x")),
            (("from a import b\nb", "from a import x\nx"), ("a.b", "a.x")),
            (("from a import b\nb", "from x import b\nb"), ("a", "x")),
            (("from a import b\nb", "from x import b\nb"), ("a.b", "x.b")),
            (("from a import b\nb", "from x import y\ny"), ("a.b", "x.y")),
            (("from a import b\nb", "from x.y import b\nb"), ("a", "x.y")),
            (("from a import b\nb", "from x.y import z\nz"), ("a.b", "x.y.z")),
            (("from a import b\nb", "import x\nx"), ("a.b", "x")),
            # `from a.b import c`
            (("from a.b import c\nc", "from x.b import c\nc"), ("a", "x")),
            (("from a.b import c\nc", "from x.y.b import c\nc"), ("a", "x.y")),
            (("from a.b import c\nc", "from x import c\nc"), ("a.b", "x")),
            (("from a.b import c\nc", "from x.y import c\nc"), ("a.b", "x.y")),
            (("from a.b import c\nc", "from a.b import c\nc"), ("a.b.c", "a.b.c")),
            (("from a.b import c\nc", "import x\nx"), ("a.b.c", "x")),
            (("from a.b import c\nc", "from x import y\ny"), ("a.b.c", "x.y")),
            (("from a.b import c\nc", "from x.y import z\nz"), ("a.b.c", "x.y.z")),
            (("from a.b import c\nc", "from w.x.y import z\nz"), ("a.b.c", "w.x.y.z")),
            (("from a.b import c\nc", "from a.b import x\nx"), ("a.b.c", "a.b.x")),
            (("from a.b import c\nc", "from a.x import c\nc"), ("a.b.c", "a.x.c")),
            (("from a.b import c\nc", "from x.b import c\nc"), ("a.b.c", "x.b.c")),
            (("from a.b import c\nc", "from a.x import y\ny"), ("a.b.c", "a.x.y")),
            (("from a.b import c\nc", "from x.y import c\nc"), ("a.b.c", "x.y.c")),
            (("from a.b import c as z\nz", "from x.y import z\nz"), ("a.b.c", "x.y.z")),
        ):
            before, after = before_after
            old, new = old_new
            self.assertCodemod(before, after, old=old, new=new)

    def test_relative_importfrom_name_usage(self):
        for (before_after, old_new) in (
            # `from a import b`
            (("from . import b as y\ny", "from x import b as y\ny"), ("a", "x")),
            (("from . import b as y\ny", "import x\nx"), ("a.b", "x")),
            (("from . import b\nb", "from . import b\nb"), ("a.b", "a.b")),
            (("from . import b\nb", "from . import b\nb"), ("b", "x")),
            (("from . import b\nb", "from a import x\nx"), ("a.b", "a.x")),
            (("from . import b\nb", "from x import b\nb"), ("a", "x")),
            (("from . import b\nb", "from x import b\nb"), ("a.b", "x.b")),
            (("from . import b\nb", "from x import y\ny"), ("a.b", "x.y")),
            (("from . import b\nb", "from x.y import b\nb"), ("a", "x.y")),
            (("from . import b\nb", "from x.y import z\nz"), ("a.b", "x.y.z")),
            (("from . import b\nb", "import x\nx"), ("a.b", "x")),
            # `from a.b import c`
            (("from .b import c as z\nz", "from x.y import c as z\nz"), ("a.b", "x.y")),
            (("from .b import c as z\nz", "from x.y import z\nz"), ("a.b.c", "x.y.z")),
            (("from .b import c\nc", "from .b import c\nc"), ("a.b.c", "a.b.c")),
            (("from .b import c\nc", "from .b import c\nc"), ("b", "x.y")),
            (("from .b import c\nc", "from a.b import x\nx"), ("a.b.c", "a.b.x")),
            (("from .b import c\nc", "from a.x import c\nc"), ("a.b.c", "a.x.c")),
            (("from .b import c\nc", "from a.x import y\ny"), ("a.b.c", "a.x.y")),
            (("from .b import c\nc", "from w.x.y import z\nz"), ("a.b.c", "w.x.y.z")),
            (("from .b import c\nc", "from x import c\nc"), ("a.b", "x")),
            (("from .b import c\nc", "from x import y\ny"), ("a.b.c", "x.y")),
            (("from .b import c\nc", "from x.b import c\nc"), ("a", "x")),
            (("from .b import c\nc", "from x.b import c\nc"), ("a.b.c", "x.b.c")),
            (("from .b import c\nc", "from x.y import c\nc"), ("a.b", "x.y")),
            (("from .b import c\nc", "from x.y import c\nc"), ("a.b.c", "x.y.c")),
            (("from .b import c\nc", "from x.y import z\nz"), ("a.b.c", "x.y.z")),
            (("from .b import c\nc", "from x.y.b import c\nc"), ("a", "x.y")),
            (("from .b import c\nc", "import x\nx"), ("a.b.c", "x")),
        ):
            before, after = before_after
            old, new = old_new
            context = CodemodContext(
                filename="a/some_module.py", full_module_name="a.some_module"
            )
            self.assertCodemod(
                before, after, old=old, new=new, context_override=context
            )


class TestImportAttributeCases(ReplaceCodemodTest):
    TRANSFORM = ReplaceCodemod

    def test_import_attribute_usage(self):
        for (before_after, old_new) in (
            # `import a`
            (("import a\na.zz", "import a\na.zz"), ("a", "a")),
            (("import a\na.zz", "import x\nx.zz"), ("a", "x")),
            (("import a as x\nx.zz", "import x\nx.zz"), ("a", "x")),
            (("import a as y\ny.zz", "import x\nx.zz"), ("a", "x")),
            # `import a.b`
            (("import a\na.b", "import a; import a.x\na.x"), ("a.b", "a.x")),
            (("import a\na.b", "import x\nx"), ("a.b", "x")),
            (("import a\na.b.zz", "import a; import a.x\na.x.zz"), ("a.b", "a.x")),
            (("import a\na.b.zz", "import x\nx.zz"), ("a.b", "x")),
            (("import a.b as x\nx.zz", "import x\nx.zz"), ("a.b", "x")),
            (("import a.b as y\ny.zz", "import x\nx.zz"), ("a.b", "x")),
            # (("import a.b\na.attr", "import a\nimport x\na.attr"), ("a.b", "x")),
            (("import a.b\na.b", "import a.b\na.b"), ("a.b", "a.b")),
            (("import a.b\na.b", "import a.b\na.b"), ("b", "x")),
            (("import a.b\na.b", "import a.x\na.x"), ("a.b", "a.x")),
            (("import a.b\na.b", "import x.b\nx.b"), ("a", "x")),
            (("import a.b\na.b", "import x.b\nx.b"), ("a.b", "x.b")),
            (("import a.b\na.b", "import x.y.b\nx.y.b"), ("a", "x.y")),
            (("import a.b\na.b", "import x.y.z\nx.y.z"), ("a.b", "x.y.z")),
            (("import a.b\na.b", "import x.y\nx.y"), ("a.b", "x.y")),
            (("import a.b\na.b", "import x\nx"), ("a.b", "x")),
            (("import a.b\na.b.zz", "import a.b\na.b.zz"), ("a.b", "a.b")),
            (("import a.b\na.b.zz", "import a.b\na.b.zz"), ("b", "x")),
            (("import a.b\na.b.zz", "import a.x\na.x.zz"), ("a.b", "a.x")),
            (("import a.b\na.b.zz", "import x.b\nx.b.zz"), ("a", "x")),
            (("import a.b\na.b.zz", "import x.b\nx.b.zz"), ("a.b", "x.b")),
            (("import a.b\na.b.zz", "import x.y.b\nx.y.b.zz"), ("a", "x.y")),
            (("import a.b\na.b.zz", "import x.y.z\nx.y.z.zz"), ("a.b", "x.y.z")),
            (("import a.b\na.b.zz", "import x.y\nx.y.zz"), ("a.b", "x.y")),
            (("import a.b\na.b.zz", "import x\nx.zz"), ("a.b", "x")),
            # `import a.b.c`
            (("import a\na.b.c", "import a; import a.b.x\na.b.x"), ("a.b.c", "a.b.x")),
            (("import a\na.b.c", "import a; import a.x\na.x"), ("a.b.c", "a.x")),
            (("import a\na.b.c", "import x\nx"), ("a.b.c", "x")),
            (
                ("import a\na.b.c.zz", "import a; import a.b.x\na.b.x.zz"),
                ("a.b.c", "a.b.x"),
            ),
            (("import a\na.b.c.zz", "import a; import a.x\na.x.zz"), ("a.b.c", "a.x")),
            (("import a\na.b.c.zz", "import x\nx.zz"), ("a.b.c", "x")),
            (
                ("import a.b\na.b.c", "import a.b; import a.b.x\na.b.x"),
                ("a.b.c", "a.b.x"),
            ),
            (("import a.b\na.b.c", "import a.x\na.x"), ("a.b.c", "a.x")),
            (("import a.b\na.b.c", "import x\nx"), ("a.b.c", "x")),
            (
                ("import a.b\na.b.c.zz", "import a.b; import a.b.x\na.b.x.zz"),
                ("a.b.c", "a.b.x"),
            ),
            (("import a.b\na.b.c.zz", "import a.x\na.x.zz"), ("a.b.c", "a.x")),
            (("import a.b\na.b.c.zz", "import x\nx.zz"), ("a.b.c", "x")),
            (("import a.b.c as x\nx.zz", "import x\nx.zz"), ("a.b.c", "x")),
            (("import a.b.c as y\ny.zz", "import x\nx.zz"), ("a.b.c", "x")),
            # # (("import a.b.c\na.attr", "import a\nimport x\na.attr"), ("a.b.c", "x")),
            # # (("import a.b.c\na.b.attr", "import a.b\nimport x\na.b.attr"), ("a.b.c", "x")),
            (("import a.b.c\na.b.c", "import a.b.c\na.b.c"), ("a.b.c", "a.b.c")),
            (("import a.b.c\na.b.c", "import a.b.x\na.b.x"), ("a.b.c", "a.b.x")),
            (("import a.b.c\na.b.c", "import a.x.c\na.x.c"), ("a.b.c", "a.x.c")),
            (("import a.b.c\na.b.c", "import a.x.y\na.x.y"), ("a.b.c", "a.x.y")),
            (("import a.b.c\na.b.c", "import w.x.y.z\nw.x.y.z"), ("a.b.c", "w.x.y.z")),
            (("import a.b.c\na.b.c", "import x.b.c\nx.b.c"), ("a", "x")),
            (("import a.b.c\na.b.c", "import x.b.c\nx.b.c"), ("a.b.c", "x.b.c")),
            (("import a.b.c\na.b.c", "import x.c\nx.c"), ("a.b", "x")),
            (("import a.b.c\na.b.c", "import x.y.b.c\nx.y.b.c"), ("a", "x.y")),
            (("import a.b.c\na.b.c", "import x.y.c\nx.y.c"), ("a.b", "x.y")),
            (("import a.b.c\na.b.c", "import x.y.c\nx.y.c"), ("a.b.c", "x.y.c")),
            (("import a.b.c\na.b.c", "import x.y.z.c\nx.y.z.c"), ("a.b", "x.y.z")),
            (("import a.b.c\na.b.c", "import x.y.z\nx.y.z"), ("a.b.c", "x.y.z")),
            (("import a.b.c\na.b.c", "import x.y\nx.y"), ("a.b.c", "x.y")),
            (("import a.b.c\na.b.c", "import x\nx"), ("a.b.c", "x")),
            (("import a.b.c\na.b.c.zz", "import a.b.c\na.b.c.zz"), ("a.b.c", "a.b.c")),
            (("import a.b.c\na.b.c.zz", "import a.b.x\na.b.x.zz"), ("a.b.c", "a.b.x")),
            (("import a.b.c\na.b.c.zz", "import a.x.c\na.x.c.zz"), ("a.b.c", "a.x.c")),
            (("import a.b.c\na.b.c.zz", "import a.x.y\na.x.y.zz"), ("a.b.c", "a.x.y")),
            (
                ("import a.b.c\na.b.c.zz", "import w.x.y.z\nw.x.y.z.zz"),
                ("a.b.c", "w.x.y.z"),
            ),
            (("import a.b.c\na.b.c.zz", "import x.b.c\nx.b.c.zz"), ("a", "x")),
            (("import a.b.c\na.b.c.zz", "import x.b.c\nx.b.c.zz"), ("a.b.c", "x.b.c")),
            (("import a.b.c\na.b.c.zz", "import x.c\nx.c.zz"), ("a.b", "x")),
            (("import a.b.c\na.b.c.zz", "import x.y.b.c\nx.y.b.c.zz"), ("a", "x.y")),
            (("import a.b.c\na.b.c.zz", "import x.y.c\nx.y.c.zz"), ("a.b", "x.y")),
            (("import a.b.c\na.b.c.zz", "import x.y.c\nx.y.c.zz"), ("a.b.c", "x.y.c")),
            (
                ("import a.b.c\na.b.c.zz", "import x.y.z.c\nx.y.z.c.zz"),
                ("a.b", "x.y.z"),
            ),
            (("import a.b.c\na.b.c.zz", "import x.y.z\nx.y.z.zz"), ("a.b.c", "x.y.z")),
            (("import a.b.c\na.b.c.zz", "import x.y\nx.y.zz"), ("a.b.c", "x.y")),
            (("import a.b.c\na.b.c.zz", "import x\nx.zz"), ("a.b.c", "x")),
        ):
            before, after = before_after
            old, new = old_new
            self.assertCodemod(before, after, old=old, new=new)

    def test_importfrom_attribute_usage(self):
        for (before_after, old_new) in (
            # `from a import b`
            (("from a import b\nb.zz", "from a import b\nb.zz"), ("a.b", "a.b")),
            (("from a import b\nb.zz", "from a import b\nb.zz"), ("b", "a.b")),
            (("from a import b\nb.zz", "from a import x\nx.zz"), ("a.b", "a.x")),
            (("from a import b\nb.zz", "from x import b\nb.zz"), ("a", "x")),
            (("from a import b\nb.zz", "from x import b\nb.zz"), ("a.b", "x.b")),
            (("from a import b\nb.zz", "from x import y\ny.zz"), ("a.b", "x.y")),
            (("from a import b\nb.zz", "from x.y import b\nb.zz"), ("a", "x.y")),
            (("from a import b\nb.zz", "from x.y import z\nz.zz"), ("a.b", "x.y.z")),
            (("from a import b\nb.zz", "import x\nx.zz"), ("a.b", "x")),
            # `from a.b import c`
            (("from a import b\nb.c", "import x\nx.y"), ("a.b.c", "x.y")),
            (("from a import b\nb.c", "from x import y\ny.z"), ("a.b.c", "x.y.z")),
            (("from a import b\nb.c", "import x\nx"), ("a.b.c", "x")),
            (
                ("from a.b import c as z\nz.zz", "from x.y import z\nz.zz"),
                ("a.b.c", "x.y.z"),
            ),
            (
                ("from a.b import c\nc.zz", "from a.b import c\nc.zz"),
                ("a.b.c", "a.b.c"),
            ),
            (("from a.b import c\nc.zz", "from a.b import c\nc.zz"), ("b", "x")),
            (
                ("from a.b import c\nc.zz", "from a.b import x\nx.zz"),
                ("a.b.c", "a.b.x"),
            ),
            (
                ("from a.b import c\nc.zz", "from a.x import c\nc.zz"),
                ("a.b.c", "a.x.c"),
            ),
            (
                ("from a.b import c\nc.zz", "from a.x import y\ny.zz"),
                ("a.b.c", "a.x.y"),
            ),
            (
                ("from a.b import c\nc.zz", "from w.x.y import z\nz.zz"),
                ("a.b.c", "w.x.y.z"),
            ),
            (("from a.b import c\nc.zz", "from x import c\nc.zz"), ("a.b", "x")),
            (("from a.b import c\nc.zz", "from x import y\ny.zz"), ("a.b.c", "x.y")),
            (("from a.b import c\nc.zz", "from x.b import c\nc.zz"), ("a", "x")),
            (
                ("from a.b import c\nc.zz", "from x.b import c\nc.zz"),
                ("a.b.c", "x.b.c"),
            ),
            (("from a.b import c\nc.zz", "from x.y import c\nc.zz"), ("a.b", "x.y")),
            (
                ("from a.b import c\nc.zz", "from x.y import c\nc.zz"),
                ("a.b.c", "x.y.c"),
            ),
            (
                ("from a.b import c\nc.zz", "from x.y import z\nz.zz"),
                ("a.b.c", "x.y.z"),
            ),
            (("from a.b import c\nc.zz", "from x.y.b import c\nc.zz"), ("a", "x.y")),
            (("from a.b import c\nc.zz", "import x\nx.zz"), ("a.b.c", "x")),
        ):

            before, after = before_after
            old, new = old_new
            self.assertCodemod(before, after, old=old, new=new)

    def test_relative_importfrom_attribute_usage(self):
        for (before_after, old_new) in (
            # `from a import b`
            (("from . import b\nb.zz", "from . import b\nb.zz"), ("a.b", "a.b")),
            (("from . import b\nb.zz", "from x import b\nb.zz"), ("a", "x")),
            (("from . import b\nb.zz", "from x.y import b\nb.zz"), ("a", "x.y")),
            (("from . import b\nb.zz", "from . import b\nb.zz"), ("b", "x.y")),
            (("from . import b\nb.zz", "import x\nx.zz"), ("a.b", "x")),
            (("from . import b\nb.zz", "from x import y\ny.zz"), ("a.b", "x.y")),
            (("from . import b\nb.zz", "from x.y import z\nz.zz"), ("a.b", "x.y.z")),
            (("from . import b\nb.zz", "from a import x\nx.zz"), ("a.b", "a.x")),
            (("from . import b\nb.zz", "from x import b\nb.zz"), ("a.b", "x.b")),
            # `from a.b import c`
            (("from .b import c\nc.zz", "from .b import c\nc.zz"), ("a.b.c", "a.b.c")),
            (("from .b import c\nc.zz", "from x.b import c\nc.zz"), ("a", "x")),
            (("from .b import c\nc.zz", "from x.y.b import c\nc.zz"), ("a", "x.y")),
            (("from .b import c\nc.zz", "from x import c\nc.zz"), ("a.b", "x")),
            (("from .b import c\nc.zz", "from x.y import c\nc.zz"), ("a.b", "x.y")),
            (("from .b import c\nc.zz", "from .b import c\nc.zz"), ("b", "x")),
            (("from .b import c\nc.zz", "import x\nx.zz"), ("a.b.c", "x")),
            (("from .b import c\nc.zz", "from x import y\ny.zz"), ("a.b.c", "x.y")),
            (("from .b import c\nc.zz", "from x.y import z\nz.zz"), ("a.b.c", "x.y.z")),
            (
                ("from .b import c\nc.zz", "from w.x.y import z\nz.zz"),
                ("a.b.c", "w.x.y.z"),
            ),
            (("from .b import c\nc.zz", "from a.b import x\nx.zz"), ("a.b.c", "a.b.x")),
            (("from .b import c\nc.zz", "from a.x import c\nc.zz"), ("a.b.c", "a.x.c")),
            (("from .b import c\nc.zz", "from x.b import c\nc.zz"), ("a.b.c", "x.b.c")),
            (("from .b import c\nc.zz", "from a.x import y\ny.zz"), ("a.b.c", "a.x.y")),
            (("from .b import c\nc.zz", "from x.y import c\nc.zz"), ("a.b.c", "x.y.c")),
            (
                ("from .b import c as z\nz.zz", "from x.y import z\nz.zz"),
                ("a.b.c", "x.y.z"),
            ),
        ):
            before, after = before_after
            old, new = old_new
            context = CodemodContext(
                filename="a/some_module.py", full_module_name="a.some_module"
            )
            self.assertCodemod(
                before, after, old=old, new=new, context_override=context
            )


class TestShadowedVariables(ReplaceCodemodTest):
    TRANSFORM = ReplaceCodemod

    def test_introduce_shadowing_variable_assignment_importonly(self):
        before = """
            from a import b
            y = 1
        """
        after = """
            from x import y  # TODO(FIXME): Adding 'x.y' may have introduced shadowing. 'y' was already defined in this scope.
            y = 1
        """

        self.assertCodemod(before, after, old="a.b", new="x.y")

    def test_introduce_shadowing_variable_access_importonly(self):
        before = """
            from a import b
            y
        """
        after = """
            from x import y  # TODO(FIXME): Adding 'x.y' may have introduced shadowing. 'y' was already used in this scope.
            y
        """

        self.assertCodemod(before, after, old="a.b", new="x.y")

    def test_introduce_shadowing_variable_assignment(self):
        before = """
            from a import b
            y = 1
            b
        """
        after = """
            from x import y
            y = 1
            y  # TODO(FIXME): Adding 'x.y' may have introduced shadowing. 'y' was already defined in this scope.
        """

        self.assertCodemod(before, after, old="a.b", new="x.y")

    def test_introduce_shadowing_variable_access(self):
        before = """
            from a import b
            y
            b
        """
        after = """
            from x import y
            y
            y  # TODO(FIXME): Adding 'x.y' may have introduced shadowing. 'y' was already used in this scope.
        """

        self.assertCodemod(before, after, old="a.b", new="x.y")

    def test_do_not_replace_shadowed_variable(self):
        before = """
            from a import b
            b
            b = 1
            b
        """
        after = """
            from a import b
            b  # TODO(FIXME): Cannot replace due to variable shadowing. Fix manually.
            b = 1
            b  # TODO(FIXME): Cannot replace due to variable shadowing. Fix manually.
        """

        self.assertCodemod(before, after, old="a.b", new="x.y")

    def test_only_shadowed_variables_that_match_old_get_comment(self):
        before = """
            from a import c
            c = 1
            c
        """
        after = """
            from a import c
            c = 1
            c
        """

        self.assertCodemod(before, after, old="a.b", new="x.y")


class TestFormat(ReplaceCodemodTest):
    TRANSFORM = ReplaceCodemod

    def test_format(self):
        before = """
            from a import b
            b.c
        """
        after = """
            from x.y import z as b
            b.c
        """

        self.assertCodemod(
            before, after, old="a.b.c", new="x.y.z.c", format="from x.y import z as b"
        )


class TestMultipleReplaces(ReplaceCodemodTest):
    TRANSFORM = ReplaceCodemod

    def test_multiple_replaces(self):
        before = """
            from a import b
            from c import d
            b.c
        """
        after = """
            from x import y
            from c import e
            y.z
        """

        self.assertCodemod(before, after, old="a.b.c,c.d", new="x.y.z,c.e")

    def test_multiple_replaces_with_format(self):
        before = """
            from a import b
            from c import d
            b.c
            d
        """
        after = """
            from x.y import z
            from c import e as f
            z
            f
        """

        self.assertCodemod(
            before,
            after,
            old="a.b.c,c.d",
            new="x.y.z,c.e",
            format="from x.y import z,from c import e as f",
        )

    # test is flaky
    def test_replace_multiple_on_same_line(self):
        before = """
            from a import b, c
            b
            c
        """
        after = """
            from x import y; from x import z
            y
            z
        """
        self.assertCodemod(before, after, old="a.b,a.c", new="x.y,x.z")

    # test is flaky
    def test_replace_multiple_on_same_line_with_old_import(self):
        before = """
            from a import b, c, d
            b
            c
        """
        after = """
            from a import d; from x import y; from x import z
            y
            z
        """
        self.assertCodemod(before, after, old="a.b,a.c", new="x.y,x.z")


class TestExact(ReplaceCodemodTest):
    TRANSFORM = ReplaceCodemod

    def test_exact_true_hit(self):
        before = """
            from a import b
            b.c
        """
        after = """
            from x import y
            y.z
        """

        self.assertCodemod(before, after, old="a.b.c", new="x.y.z", exact=True)

    def test_exact_true_miss(self):
        before = """
            from a import b
            b.c
        """
        after = """
            from a import b
            b.c
        """

        self.assertCodemod(before, after, old="a.b", new="x.y.z", exact=True)

    def test_exact_false_hit(self):
        before = """
            from a import b
            b.c
        """
        after = """
            from x.y import z
            z.c
        """

        self.assertCodemod(before, after, old="a.b", new="x.y.z", exact=False)


class TestBugsFound(ReplaceCodemodTest):
    TRANSFORM = ReplaceCodemod

    def test_only_add_import_once(self):
        before = """
            from a import b
            b.c
            b.c
        """
        after = """
            from x.y import z as b
            b.c
            b.c
        """

        self.assertCodemod(
            before, after, old="a.b.c", new="x.y.z.c", format="from x.y import z as b"
        )

    def test_remove_single_name(self):
        before = """
            from a import b, c
            c
        """
        after = """
            from a import b; from a import x
            x
        """

        self.assertCodemod(before, after, old="a.c", new="a.x")

    def test_keeps_imports_if_still_used(self):
        before = """
            from a import b
            b.c
            b.d
        """
        after = """
            from a import b; from a.b import x
            x
            b.d
        """

        self.assertCodemod(
            before, after, old="a.b.c", new="a.b.x", format="from a.b import x"
        )

    def test_removes_unused_imports(self):
        before = """
            from a import b
            b
        """
        after = """
            from a import x
            x
        """

        self.assertCodemod(before, after, old="a.b", new="a.x")

    def test_only_rename_import(self):
        before = """
            from a import b
            b
        """
        after = """
            from a import b as c
            c
        """

        self.assertCodemod(
            before, after, old="a.b", new="a.b", format="from a import b as c"
        )

    def test_replace_invocation(self):
        before = """
            from a import b
            b(x=1).c
        """
        after = """
            from a.z import b
            b(x=1).c
        """

        self.assertCodemod(before, after, old="a.b", new="a.z.b")

    def test_relative_importfrom_in_init_file(self):
        before = """
            from .c import d
        """
        after = """
            from x import y
        """
        context = CodemodContext(filename="a/b.py", full_module_name="a.b")
        context_init = CodemodContext(
            filename="a/b/__init__.py", full_module_name="a.b"
        )

        self.assertCodemod(
            before, before, old="a.b.c.d", new="x.y", context_override=context
        )
        self.assertCodemod(
            before, before, old="a.c.d", new="x.y", context_override=context_init
        )

        self.assertCodemod(
            before, after, old="a.c.d", new="x.y", context_override=context
        )
        self.assertCodemod(
            before, after, old="a.b.c.d", new="x.y", context_override=context_init
        )

    def test_similarly_named_imports(self):
        before = """
            from a.b import c, cd
            c
            cd
        """
        after = """
            from a.b import c; from x.y import cd
            c
            cd
        """

        self.assertCodemod(before, after, old="a.b.cd", new="x.y.cd")


class TestPlayground(ReplaceCodemodTest):
    TRANSFORM = ReplaceCodemod

    def test_playground(self):
        before = """
            from a import b
            b.c
            b.c
        """
        after = """
            from x.y import z as b
            b.c
            b.c
        """

        self.assertCodemod(
            before,
            after,
            old="a.b.c",
            new="x.y.z.c",
            format="from x.y import z as b",
        )
