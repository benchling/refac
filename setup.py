# https://hynek.me/articles/sharing-your-labor-of-love-pypi-quick-and-dirty
import re
from pathlib import Path

from setuptools import setup, find_packages

ROOT_DIR = Path(__file__).parent.resolve()

###################################################################

NAME = "move-symbol"
PACKAGES = find_packages(where="src")
META_PATH = ROOT_DIR.joinpath("src/move_symbol/__init__.py")
KEYWORDS = ["refactor", "symbol", "move"]
CLASSIFIERS = [
    "Intended Audience :: Developers",
    "Natural Language :: English",
    "Programming Language :: Python :: 3",
    "Topic :: Software Development :: Libraries :: Python Modules",
]
INSTALL_REQUIRES = ["click", "libcst"]

###################################################################


META_FILE = META_PATH.read_text()


def find_meta(meta):
    """
    Extract __*meta*__ from META_FILE.
    """
    meta_match = re.search(
        r"^__{meta}__ = ['\"]([^'\"]*)['\"]".format(meta=meta), META_FILE, re.M
    )
    if meta_match:
        return meta_match.group(1)
    raise RuntimeError("Unable to find __{meta}__ string.".format(meta=meta))


if __name__ == "__main__":
    setup(
        name=NAME,
        description=find_meta("description"),
        license=find_meta("license"),
        url=find_meta("uri"),
        version=find_meta("version"),
        author=find_meta("author"),
        author_email=find_meta("email"),
        maintainer=find_meta("author"),
        maintainer_email=find_meta("email"),
        keywords=KEYWORDS,
        long_description=(ROOT_DIR / "README.md").read_text(),
        long_description_content_type="text/markdown",
        packages=PACKAGES,
        package_dir={"": "src"},
        package_data={"move_symbol": ["py.typed"]},
        zip_safe=False,
        classifiers=CLASSIFIERS,
        install_requires=INSTALL_REQUIRES,
        options={"bdist_wheel": {"universal": "1"}},
        entry_points={"console_scripts": ["move-symbol = move_symbol.__main__"]},
    )
