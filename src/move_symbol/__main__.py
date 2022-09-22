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
        assert dst.endswith(".py"), "dst must end with '.py'"
        if not Path(dst).is_file():
            move_file(Path(src), Path(dst), include_strings=True)
        # else:
        # collect symbols
        # move all symbols

    #     src_file = src
    # else:
    #     src_file, src_symbol = src.rsplit(".", 1)
    #     assert Path(src_file).is_file(), f"Cannot find source file from {src}."

    # if Path(dst).is_file():
    #     dst_file = dst
    # else:
    #     dst_file, dst_symbol = dst.rsplit(".", 1)
    #     assert Path(dst_file).is_file(), f"Cannot find source file from {dst}."

    # if src_symbol is None:
    #     assert dst_symbol is None, f"Cannot move file {src} to symbol {dst}."

    # if src_symbol is not None:
    #     if dst_symbol is None:
    #         dst_symbol = src_symbol

    # if src_symbol is None and dst_symbol is None:
    # else:
    #     move_symbol(src_symbol, dst_symbol)


main()
