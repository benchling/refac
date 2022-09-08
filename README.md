# move-symbol

A tool for moving and refactoring python code.

## Quickstart

```bash
pip install move-symbol
```

```bash
python -m move_symbol <src> <dst>
python -m move_symbol /path/to/src.py /path/to/dst.py
python -m move_symbol path.to.src.module path.to.dst.module
python -m move_symbol path.to.src.module.symbol path.to.dst.module.symbol
```

## Features

1. Move Python files or symbols
2. Automatically fix imports after moving.
