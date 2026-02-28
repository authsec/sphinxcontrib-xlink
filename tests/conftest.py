import sys
import os
from pathlib import Path
import pytest

# Get the absolute path to the project's 'src' directory
src_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src'))
sys.path.insert(0, src_dir)

# Force the already-loaded 'sphinxcontrib' namespace to also look in our local src dir.
try:
    import sphinxcontrib
    local_namespace = os.path.join(src_dir, 'sphinxcontrib')
    if hasattr(sphinxcontrib, '__path__') and local_namespace not in sphinxcontrib.__path__:
        sphinxcontrib.__path__.append(local_namespace)
except ImportError:
    pass

pytest_plugins = 'sphinx.testing.fixtures'

@pytest.fixture(scope='session')
def rootdir():
    # standard setup for sphinx testing roots
    return Path(__file__).parent.resolve() / 'roots'