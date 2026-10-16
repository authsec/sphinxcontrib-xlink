import importlib.util
import pathlib

import pytest

INIT_PATH = (
    pathlib.Path(__file__).parent.parent
    / "src"
    / "sphinxcontrib"
    / "xlink"
    / "__init__.py"
)


def test_import_raises_with_migration_message():
    """Importing the deprecated package must fail loudly.

    Load the tombstone module directly by path so the test is not affected by
    any other 'sphinxcontrib' package that happens to be installed in the
    environment (namespace packages resolve via sys.path otherwise).
    """
    spec = importlib.util.spec_from_file_location(
        "sphinxcontrib_xlink_tombstone", str(INIT_PATH)
    )
    module = importlib.util.module_from_spec(spec)
    with pytest.raises(ImportError) as excinfo:
        spec.loader.exec_module(module)
    msg = str(excinfo.value)
    assert "doxtr-xlink" in msg
    assert "pip install doxtr-xlink" in msg


def test_setup_raises_with_migration_message():
    """Enabling the extension in Sphinx must fail loudly.

    The module raises ImportError on import, so we exec just the setup()
    function body in isolation to confirm it also refuses to run.
    """
    source = INIT_PATH.read_text()
    # Drop the trailing module-level `raise ImportError(...)` so we can load
    # the setup() definition, then assert calling it raises.
    source = source.replace(
        "\n# Fail on direct import", "\n# (import guard stripped for test)  # Fail on direct import"
    )
    source = source.replace("\nraise ImportError(_MESSAGE)\n", "\n")

    namespace = {}
    exec(compile(source, str(INIT_PATH), "exec"), namespace)

    assert "setup" in namespace
    with pytest.raises(RuntimeError) as excinfo:
        namespace["setup"](object())
    assert "doxtr-xlink" in str(excinfo.value)
