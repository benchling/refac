__description__ = "Tool to move around Python source code."
__license__ = "MIT License"
__uri__ = "https://github.com/benchling/movepy"
__version__ = "0.0.1"
__author__ = "Benchling Eng"
__email__ = "eng@benchling.com"

import argparse
import sys

from .move_file import move_file
from .move_import import move_import
from .move_symbol import move_symbol


def main():
    NAME = "movepy"
    DESCRIPTION = "Move Python symbols."
    USAGE = """
    movepy [file|symbol|import] <src> <dst>

  examples:
    movepy file /path/to/src.py /path/to/dst.py
    movepy symbol path.to.SrcClass path.to.DstClass
    movepy symbol path.to.src_func1,path.to.src_func2 path.to.dst_func1,path.to.dst_func2
    movepy import path.to.src_import path.to.dst_import
  """

    parser = argparse.ArgumentParser(prog=NAME, description=DESCRIPTION, usage=USAGE)
    parser.add_argument(
        "type",
        type=str,
        help="type of move to perform",
        choices=["file", "symbol", "import"],
    )
    parser.add_argument("src", type=str, help="src or comma separated srcs")
    parser.add_argument("dst", type=str, help="dst or comma separated dsts")
    args = parser.parse_args()

    _type, src, dst = args.type, args.src, args.dst

    if src == dst:
        sys.exit(0)

    if _type == "file":
        move_file(src.split(","), dst.split(","), include_strings=True)
    elif _type == "symbol":
        move_symbol(src.split(","), dst.split(","))
    elif _type == "import":
        move_import(src.split(","), dst.split(","))
