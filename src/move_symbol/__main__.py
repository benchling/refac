from pathlib import Path
import argparse
import sys

from .move_file import move_file
from .move_symbol import move_symbol

NAME = "move-symbol"
DESCRIPTION = "Move Python symbols."
USAGE = """
  move-symbol <src> <dst>

examples:
  move-symbol /path/to/src.py /path/to/dst.py
  move-symbol path.to.src.symbol path.to.dst.symbol
  move-symbol path.to.src.symbol1,path.to.src.symbol2 path.to.dst.symbol1,path.to.dst.symbol2
"""


parser = argparse.ArgumentParser(prog=NAME, description=DESCRIPTION, usage=USAGE)
parser.add_argument("src", type=str, help="src symbol or comma separated src symbols")
parser.add_argument("dst", type=str, help="dst symbol or comma separated dst symbols")
args = parser.parse_args()

src, dst = args.src, args.dst

if src == dst:
    sys.exit(0)

if Path(src).is_file():
    move_file(Path(src), Path(dst), include_strings=True)
else:
    move_symbol(src, dst)
