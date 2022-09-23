import re
import subprocess
import sys

from move_symbol.utils import ROOT_DIR, shell


def find_and_replace(old: str, new: str) -> subprocess.CompletedProcess:
    """Find and replace a string in all files in the repo.

    Relies on `git grep` and `sed` commands.

    >>> find_and_replace("old", "new")
    """
    bsd_sed = "sed -i '' -e"
    gnu_sed = "sed -i"
    sed = bsd_sed if sys.platform == "darwin" else gnu_sed
    command = f"git grep --files-with-matches --fixed-strings '{old}' | xargs {sed} 's/{re.escape(old)}/{re.escape(new)}/g'"
    return shell(command)
