# movepy
A tool for moving and refactoring python code. It supports moving files or entire directories (movepy file). Also supports moving specific objects inside a file (movepy object) or specific imports (movepy import).

## Quickstart
```bash
pip install movepy
movepy file /path/to/src.py /path/to/dst.py
```

```bash
usage: 
    movepy [file|object|import] <src> <dst>

  examples:
    movepy file /path/to/src.py /path/to/dst.py
    movepy object path.to.SrcClass path.to.DstClass
    movepy object path.to.src_func1,path.to.src_func2 path.to.dst_func1,path.to.dst_func2
    movepy import path.to.src_import path.to.dst_import
```

## Contributing
Contributions are welcomed and appreciated. Please file GitHub issues for any bugs.
