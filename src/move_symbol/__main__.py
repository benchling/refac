import click
from pathlib import Path

from .move_file import move_file
from .move_symbol import move_symbol


@click.command()
@click.argument("src", type=click.STRING)
@click.argument("dst", type=click.STRING)
def main(src: str, dst: str) -> None:
    """Move symbols with libcst codemods."""
    if src == dst:
        return

    if Path(src).is_file():
        move_file(Path(src), Path(dst), include_strings=True)
    else:
        move_symbol(src, dst)


main()
