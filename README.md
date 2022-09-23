# move-symbol
A tool for moving and refactoring python code.

## Quickstart

```bash
pip install move-symbol
```

```bash
move-symbol <src> <dst>
move-symbol /path/to/src.py /path/to/dst.py
move-symbol path.to.src.module path.to.dst.module
move-symbol path.to.src.module.symbol path.to.dst.module.symbol
```

## Features

1. Move Python files or symbols
2. Automatically fix imports after moving.
3. Automatically fix exact string references.
