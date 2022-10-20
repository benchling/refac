`/src/movepy/**init**.py#main` is the entrypoint for the `movepy` script.

The three commands `file`, `symbol`, and `import` are implemented in `/src/movepy/move_file.py`, `/src/movepy/move_symbol.py`, and `/src/movepy/move_import.py`, respectively.

Each of these files has a similar layout. A `move_*()` function that consists of three parts:

1. Validation of the inputs.
2. Moving the file/symbol/import.
3. Updating the import statements for the other files in the codebase.
4. Updating any string references to the moved file/symbol/import.

```mermaid
graph LR;
    valid[Validate]-->move[Move file/symbol/import];
    move[Move file/symbol/import]-->import[Update imports];
    import[Update imports]-->string[Update strings];
```

The logic for #1 + #2 is bespoke to each move function.

1. Validation is fairly straightforward, and is mostly just checking that the source and destination paths are valid.

2. `move_file` is simpler than `move_symbol`. It effectively just runs `mv` command, but it will try and merge files or directories if the destination already exists. The `move_symbol` is a bit more complicated. It finds the symbol(s) to move, and finds all associated symbols needed to move as well. (An example of an associated symbol: `def f(): pass; def g(): return f` -- `f` is an associated symbol for the function `g`). It removes the symbol(s) from the source file with `RemoveSymbolsVisitor` and adds them to the new file with `AddSymbolsVisitor`. It will also add back any symbols to the old module if they were still being used by other symbols in the old module. `move_import` is very similar to `move_symbol` and may be merged in the future

The logic for #3 + #4 is shared across the `move_*` family.

3. We execute the `ReplaceImportsCodemod` to update all the import statements in the codebase. This is the meat of the movepy codemod. As a performance improvement, we try to only run it on files that may have been affected by `git grep`-ing for relevant words.

4. Finally, we `git grep` for the old and new paths and use `sed` to replace any string references to the moved file/symbol/import.
