import pytest
from bs4 import BeautifulSoup
from pathlib import Path
from sphinx.errors import ExtensionError
from sphinx.testing.util import SphinxTestApp


@pytest.mark.sphinx('html', testroot='rsti', freshenv=True)
def test_rsti_files_are_read(app, status, warning):
    """Test that .rsti files in .xlink directories are properly read for section metadata."""
    app.build()

    html = Path(app.outdir / 'index.html').read_text(encoding='utf-8')
    soup = BeautifulSoup(html, 'html.parser')

    page_text = soup.get_text()

    # The section-name.rsti content should appear as a section heading
    assert "Engineering Examples" in page_text, \
        "section-name.rsti was not read: 'Engineering Examples' not found in output"

    # The section-description.rsti content should appear in the page
    assert "Links for the engineering team." in page_text, \
        "section-description.rsti was not read: description not found in output"


def test_rst_files_in_xlink_dir_cause_build_error(rootdir, tmp_path):
    """Test that .rst files in .xlink directories cause a build-time error."""
    srcdir = tmp_path / 'rsti-error'
    # Copy the test root to a temp location
    import shutil
    shutil.copytree(rootdir / 'test-rsti-error', srcdir)

    with pytest.raises(ExtensionError, match=r"\.rst files inside \.xlink metadata directories"):
        SphinxTestApp(
            buildername='html',
            srcdir=srcdir,
            freshenv=True,
        )


def test_rst_error_message_suggests_rsti(rootdir, tmp_path):
    """Test that the error message tells users to rename .rst to .rsti."""
    srcdir = tmp_path / 'rsti-error2'
    import shutil
    shutil.copytree(rootdir / 'test-rsti-error', srcdir)

    with pytest.raises(ExtensionError, match=r"rename the following files from \.rst to \.rsti"):
        SphinxTestApp(
            buildername='html',
            srcdir=srcdir,
            freshenv=True,
        )
