import click
from pathlib import Path

from .move_file import move_file
from .move_symbol import move_symbol


@click.command()
@click.argument("src", type=click.STRING)
@click.argument("dst", type=click.STRING)
@click.pass_context
def main(ctx: click.Context, src: str, dst: str) -> None:
    """Move modules and symbols with libcst codemods.

    TODO: Figure out how to install this package
    TODO: Figure out how to install this package
    TODO: Figure out how to install this package
    TODO: Figure out how to install this package
    TODO: Figure out how to install this package
    TODO: Support multiple srcs and dsts.
    """
    if src == dst:
        return

    if Path(src).is_file():
        move_file(Path(src), Path(dst), include_strings=True)
    else:
        move_symbol(src, dst)


main()
