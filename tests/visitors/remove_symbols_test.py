from contextlib import contextmanager
from pathlib import Path
from tempfile import TemporaryDirectory

from libcst.codemod.visitors import (
    ImportItem,
)
from libcst.codemod import CodemodTest
from libcst.codemod._context import CodemodContext
from libcst.metadata.full_repo_manager import FullRepoManager
from libcst.metadata.name_provider import FullyQualifiedNameProvider

from refac.visitors import RemoveSymbolsVisitor


@contextmanager
def test_context():
    with TemporaryDirectory() as temp_dir:
        filename = "a/b.py"
        (Path(temp_dir) / "a").mkdir()
        (Path(temp_dir) / filename).touch()

        manager = FullRepoManager(temp_dir, [filename], [FullyQualifiedNameProvider])
        context = CodemodContext(
            filename=filename, full_module_name="a.b", metadata_manager=manager
        )
        yield context


class TestRemoveSymbolsVisitor(CodemodTest):
    TRANSFORM = RemoveSymbolsVisitor

    def test_noops(self):
        before = """
            def foo(): pass
            class Bar: pass
            baz = 1
        """
        after = """
            def foo(): pass
            class Bar: pass
            baz = 1
        """
        with test_context() as context:
            self.assertCodemod(before, after, {}, context_override=context)

    def test_remove_constant(self):
        before = """
            baz = 1
        """
        after = """
        """
        with test_context() as context:
            self.assertCodemod(before, after, {"baz"}, context_override=context)

    def test_remove_function(self):
        before = """
            def foo(): pass
        """
        after = """
        """
        with test_context() as context:
            self.assertCodemod(before, after, {"foo"}, context_override=context)

    def test_remove_class(self):
        before = """
            class Bar: pass
        """
        after = """
        """
        with test_context() as context:
            self.assertCodemod(before, after, {"Bar"}, context_override=context)

    def test_keep_nested(self):
        before = """
            class Bar2:
                class Bar: pass
            def foo2():
                def foo(): pass 
            if True:
                baz = 1
        """
        after = """
            class Bar2:
                class Bar: pass
            def foo2():
                def foo(): pass 
            if True:
                baz = 1
        """
        with test_context() as context:
            self.assertCodemod(
                before, after, {"Bar", "foo", "baz"}, context_override=context
            )

    def test_remove_unused_import_from(self):
        before = """
            from x import y as z
            from a.b import c

            class Bar:
                True
                c
                c.d
                z
        """
        after = """
        """
        with test_context() as context:
            self.assertCodemod(before, after, {"Bar"}, context_override=context)
            self.assertEqual(
                context.scratch[self.TRANSFORM.CONTEXT_KEY]["imports"],
                {ImportItem("a.b", "c"), ImportItem("x", "y", "z")},
            )

    def test_remove_unused_import(self):
        before = """
            import m
            import f.k.j
            import g as h
            
            def foo():
                m
                h
                f.k.j
        """
        after = """
        """
        with test_context() as context:
            self.assertCodemod(before, after, {"foo"}, context_override=context)
            self.assertEqual(
                context.scratch[self.TRANSFORM.CONTEXT_KEY]["imports"],
                {ImportItem("f.k.j"), ImportItem("g", None, "h"), ImportItem("m")},
            )

    def test_remove_import_symbol(self):
        before = """
            import c
        """
        after = """
        """
        with test_context() as context:
            self.assertCodemod(before, after, {"c"}, context_override=context)
            removed_nodes = context.scratch[self.TRANSFORM.CONTEXT_KEY]["nodes"]
            self.assertEqual(len(removed_nodes), 1)
            self.assertEqual(next(iter(removed_nodes)).names[0].name.value, "c")
            self.assertEqual(
                context.scratch[self.TRANSFORM.CONTEXT_KEY]["imports"], set()
            )

    def test_remove_import_symbol_2(self):
        before = """
            import c, d
        """
        after = """
            import d
        """
        with test_context() as context:
            self.assertCodemod(before, after, {"c"}, context_override=context)
            removed_nodes = context.scratch[self.TRANSFORM.CONTEXT_KEY]["nodes"]
            self.assertEqual(len(removed_nodes), 1)
            self.assertEqual(next(iter(removed_nodes)).names[0].name.value, "c")
            self.assertEqual(
                context.scratch[self.TRANSFORM.CONTEXT_KEY]["imports"], set()
            )

    def test_remove_importfrom_symbol(self):
        before = """
            from c import d
        """
        after = """
        """
        with test_context() as context:
            self.assertCodemod(before, after, {"d"}, context_override=context)
            removed_nodes = context.scratch[self.TRANSFORM.CONTEXT_KEY]["nodes"]
            self.assertEqual(len(removed_nodes), 1)
            self.assertEqual(next(iter(removed_nodes)).names[0].name.value, "d")
            self.assertEqual(
                context.scratch[self.TRANSFORM.CONTEXT_KEY]["imports"], set()
            )

    def test_remove_importfrom_symbol_2(self):
        before = """
            from c import d, e
        """
        after = """
            from c import e
        """
        with test_context() as context:
            self.assertCodemod(before, after, {"d"}, context_override=context)
            removed_nodes = context.scratch[self.TRANSFORM.CONTEXT_KEY]["nodes"]
            self.assertEqual(len(removed_nodes), 1)
            self.assertEqual(next(iter(removed_nodes)).names[0].name.value, "d")
            self.assertEqual(
                context.scratch[self.TRANSFORM.CONTEXT_KEY]["imports"], set()
            )
