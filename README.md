# movepy

A tool for moving and refactoring python code.

## Quickstart

```bash
pip install movepy
```

```bash
movepy <src> <dst>
movepy /path/to/src.py /path/to/dst.py
movepy path.to.src.module path.to.dst.module
movepy path.to.src.module.symbol path.to.dst.module.symbol
```

## Features

1. Move Python files or symbols
2. Automatically fix imports after moving.
3. Automatically fix exact string references.
