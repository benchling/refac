from contextlib import contextmanager
from pathlib import Path
from tempfile import TemporaryDirectory
from textwrap import dedent

import libcst as cst
from libcst.codemod import CodemodTest
from libcst.codemod._context import CodemodContext
from libcst.codemod.visitors import ImportItem
from libcst.metadata.full_repo_manager import FullRepoManager
from libcst.metadata.name_provider import FullyQualifiedNameProvider

from refac.visitors import AddSymbolsVisitor


@contextmanager
def test_context():
    with TemporaryDirectory() as temp_dir:
        filename = "a/b.py"
        (Path(temp_dir) / "a").mkdir()
        (Path(temp_dir) / filename).touch()
        full_filename = str((Path(temp_dir) / filename))

        manager = FullRepoManager(temp_dir, [full_filename], [FullyQualifiedNameProvider])
        context = CodemodContext(
            filename=full_filename, full_module_name="a.b", metadata_manager=manager
        )
        yield context


class TestAddSymbolsVisitor(CodemodTest):
    TRANSFORM = AddSymbolsVisitor

    def test_add_constant(self):
        before = """
        """
        after = """
            baz = 1
        """
        with test_context() as context:
            module = cst.parse_module("baz = 1")
            self.assertCodemod(
                before, after, set(module.body), set(), context_override=context
            )

    def test_add_function(self):
        before = """
        """
        after = """
            def foo(): pass
        """
        with test_context() as context:
            module = cst.parse_module("def foo(): pass")
            self.assertCodemod(
                before, after, set(module.body), set(), context_override=context
            )

    def test_add_class(self):
        before = """
        """
        after = """
            class Bar: pass
        """
        with test_context() as context:
            module = cst.parse_module("class Bar: pass")
            self.assertCodemod(
                before, after, set(module.body), set(), context_override=context
            )

    def test_adds_missing_import(self):
        before = """
        """
        after = """
            from a.b import c

            def foo():
                c
        """
        with test_context() as context:
            module = cst.parse_module(
                dedent(
                    """
                        def foo():
                           c
                    """
                )
            )
            self.assertCodemod(
                before,
                after,
                set(module.body),
                {ImportItem("a.b", "c")},
                context_override=context,
            )
