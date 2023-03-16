import re
import subprocess
import sys

from refac.utils import shell


def escape(s: str) -> str:
    """Escape a string for use in sed.

    In addition to usual regex escaping, we also need to escape forward slashes (/).
    >>> escape("foo/bar.py")
    "foo\\/bar\\.py"
    """
    return re.escape(s).replace("/", "\\/")


def find_and_replace(old: str, new: str) -> subprocess.CompletedProcess:
    """Find and replace a string in all files in the repo.

    Relies on `git grep` and `sed` commands.

    >>> find_and_replace("old", "new")
    """
    bsd_sed = "sed -i '' -e"
    gnu_sed = "sed -i"
    sed = bsd_sed if sys.platform == "darwin" else gnu_sed

    bsd_xargs = "xargs"
    gnu_xargs = "xargs --no-run-if-empty"
    xargs = bsd_xargs if sys.platform == "darwin" else gnu_xargs
    command = f"git grep --files-with-matches --fixed-strings '{old}' | {xargs} {sed} 's/{escape(old)}/{escape(new)}/g'"
    return shell(command)
