# movepy

A tool for moving and refactoring python code. It supports moving files or entire directories (movepy file). Also supports moving specific symbols inside a file (movepy symbol) or specific imports (movepy import).

## Quickstart

```bash
pip install movepy
movepy file /path/to/src.py /path/to/dst.py
```

```bash
usage:
    movepy [file|symbol|import] <src> <dst>

  examples:
    movepy file /path/to/src.py /path/to/dst.py
    movepy symbol path.to.SrcClass path.to.DstClass
    movepy symbol path.to.src_func1,path.to.src_func2 path.to.dst_func1,path.to.dst_func2
    movepy import path.to.src_import path.to.dst_import
```

## Contributing

Contributions are welcomed and appreciated. Check out ARCHITECTURE.md for an overview of the codebase.

To run tests:

```bash
python -m unittest tests/**/*.py
```

Please file GitHub issues for any bugs.
