# refac

A tool for moving and refactoring python code. It supports moving files or entire directories (refac file). Also supports moving specific symbols inside a file (refac symbol) or specific imports (refac import).

[![Checks](https://github.com/benchling/refac/actions/workflows/checks.yaml/badge.svg?branch=main&event=push)](https://github.com/benchling/refac/actions/workflows/checks.yaml)

## Quickstart

```bash
pip install refac
refac file /path/to/src.py /path/to/dst.py
```

and add the following to your `.libcst.codemod.yaml` at the root of your project:

```yaml
modules:
  - "refac.visitors"
```

```bash
usage:
    refac [file|symbol|import] <src> <dst>

  examples:
    refac file /path/to/src.py /path/to/dst.py
    refac symbol path.to.SrcClass path.to.DstClass
    refac symbol path.to.src_func1,path.to.src_func2 path.to.dst_func1,path.to.dst_func2
    refac import path.to.src_import path.to.dst_import
```

## Contributing

Contributions are welcomed and appreciated. Check out ARCHITECTURE.md for an overview of the codebase.

To run tests:

```bash
# Must be using Python >3.9
python -m pip install -r requirements.txt
python -m unittest tests/**/*.py
```

Please file GitHub issues for any bugs.
