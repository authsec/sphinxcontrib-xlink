"""sphinxcontrib-xlink has been renamed to **doxtr-xlink**.

This is a deprecated tombstone release (1.3.2). It contains no functionality.
Importing it or enabling it as a Sphinx extension raises an error with
migration instructions.

Migration:
    pip uninstall sphinxcontrib-xlink
    pip install doxtr-xlink

Then update your conf.py:
    extensions = ['doxtr_xlink']   # was: 'sphinxcontrib.xlink'
"""

__version__ = "1.3.2"

_MESSAGE = (
    "'sphinxcontrib-xlink' has been renamed to 'doxtr-xlink' and is no longer "
    "maintained under the old name.\n\n"
    "Migrate with:\n"
    "    pip uninstall sphinxcontrib-xlink\n"
    "    pip install doxtr-xlink\n\n"
    "Then in your conf.py change:\n"
    "    extensions = ['sphinxcontrib.xlink']\n"
    "to:\n"
    "    extensions = ['doxtr_xlink']\n\n"
    "See https://github.com/doxtr/doxtr-xlink for details."
)


def setup(app):
    """Sphinx entry point. Fails loudly to force migration to doxtr-xlink."""
    raise RuntimeError(_MESSAGE)


# Fail on direct import as well, so any code that does
# `import sphinxcontrib.xlink` gets the migration message immediately.
raise ImportError(_MESSAGE)
