import unittest

from libcst import parse_statement
from libcst.codemod import CodemodContext

from movepy.visitors import import_utils


class ImportUtilsTest(unittest.TestCase):
    def test_get_absolute_module_for_import(self):
        for filename, import_stmt, expected_module in (
            ("a/b.py", "from . import c", "a"),
            ("a/b/__init__.py", "from . import c", "a.b"),
            ("a/b.py", "from x.y import z", "x.y"),
            ("a/b/__init__.py", "from x.y import z", "x.y"),
        ):
            node = parse_statement(import_stmt).body[0]
            context = CodemodContext(
                filename=filename,
                full_module_name=filename.replace(".py", "")
                .replace("/__init__", "")
                .replace("/", "."),
            )
            module = import_utils.get_absolute_module_for_import(context, node)
            self.assertEqual(module, expected_module)
