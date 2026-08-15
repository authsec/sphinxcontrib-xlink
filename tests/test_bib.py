import pytest
from pathlib import Path


@pytest.fixture(autouse=True)
def _reset_tag_pattern_cache():
    """Reset the module-level compiled tag pattern cache between tests.

    sphinxcontrib.xlink caches compiled regex patterns in a module global.
    Without this reset, state can leak between tests causing false passes/failures.
    """
    import sphinxcontrib.xlink as xlink_mod
    xlink_mod._compiled_tag_patterns = None
    yield
    xlink_mod._compiled_tag_patterns = None


# --- Unit tests for parse_tag_list ---

def test_parse_tag_list_basic():
    """Unit test for parse_tag_list: normal comma separation, empty strings, single tags."""
    from sphinxcontrib.xlink import parse_tag_list

    assert parse_tag_list('engineer, code') == ['engineer', 'code']
    assert parse_tag_list('general') == ['general']
    assert parse_tag_list('') == []
    assert parse_tag_list('  ') == []
    assert parse_tag_list('a, , b') == ['a', 'b']
    assert parse_tag_list('bib:type:online, bib:author:Harold David Moore') == [
        'bib:type:online', 'bib:author:Harold David Moore'
    ]


def test_parse_tag_list_quoted():
    """Unit test: quoted values with commas inside are preserved as single tags."""
    from sphinxcontrib.xlink import parse_tag_list

    result = parse_tag_list('bib:type:online, bib:author:"van Beethoven, Ludwig", bib:year:2021')
    assert result == [
        'bib:type:online',
        'bib:author:"van Beethoven, Ludwig"',
        'bib:year:2021',
    ]

    # Quotes are preserved
    assert '"van Beethoven, Ludwig"' in result[1]

    # Multiple quoted values
    result2 = parse_tag_list('"a, b", "c, d"')
    assert result2 == ['"a, b"', '"c, d"']


# --- Integration tests for BibTeX generation ---

@pytest.mark.sphinx('html', testroot='bib', freshenv=True)
def test_bib_file_generated(app, status, warning):
    """Build the test root, verify references.bib exists."""
    app.build(force_all=True)

    bib_path = Path(app.srcdir) / 'references.bib'
    assert bib_path.exists(), f"Expected {bib_path} to exist after build"


@pytest.mark.sphinx('html', testroot='bib', freshenv=True)
def test_bib_file_content(app, status, warning):
    """Verify the generated .bib file contains correct entries with proper fields."""
    app.build(force_all=True)

    bib_path = Path(app.srcdir) / 'references.bib'
    content = bib_path.read_text(encoding='utf-8')

    # Check nist-csf entry
    assert '@online{nist-csf,' in content
    assert 'author = {Zeeshan Haider},' in content
    assert 'year = {2021},' in content
    assert 'urldate = {2026-07-10},' in content

    # Check beethoven-bio entry
    assert '@book{beethoven-bio,' in content
    assert 'year = {1900},' in content
    assert 'publisher = {Classic Books},' in content


@pytest.mark.sphinx('html', testroot='bib', freshenv=True)
def test_bib_quoted_author_stripped(app, status, warning):
    """Verify that in the .bib output, quoted author has quotes stripped."""
    app.build(force_all=True)

    bib_path = Path(app.srcdir) / 'references.bib'
    content = bib_path.read_text(encoding='utf-8')

    # Quotes should be stripped in the bib output
    assert 'author = {van Beethoven, Ludwig},' in content
    # Raw quotes should NOT appear
    assert '"van Beethoven, Ludwig"' not in content


@pytest.mark.sphinx('html', testroot='bib', freshenv=True)
def test_bib_reuses_title_and_url(app, status, warning):
    """Verify title and url from the xlink entry appear in the bib output."""
    app.build(force_all=True)

    bib_path = Path(app.srcdir) / 'references.bib'
    content = bib_path.read_text(encoding='utf-8')

    assert 'title = {NIST Cybersecurity Framework},' in content
    assert 'url = {https://example.com/nist-csf},' in content
    assert 'title = {Biography of Beethoven},' in content
    assert 'url = {https://example.com/beethoven},' in content


@pytest.mark.sphinx('html', testroot='bib', freshenv=True)
def test_bib_skips_non_bib_entries(app, status, warning):
    """Verify no-bib-link does NOT appear in the .bib file."""
    app.build(force_all=True)

    bib_path = Path(app.srcdir) / 'references.bib'
    content = bib_path.read_text(encoding='utf-8')

    assert 'no-bib-link' not in content
    assert 'Regular Link' not in content


@pytest.mark.sphinx('html', testroot='bib', freshenv=True)
def test_bib_warns_on_missing_required_fields(app, status, warning):
    """Verify that building with missing-fields produces warnings."""
    app.build(force_all=True)

    warnings = warning.getvalue()
    assert "missing-fields" in warnings
    assert "article" in warnings
    assert "author" in warnings or "journal" in warnings or "year" in warnings


@pytest.mark.sphinx('html', testroot='bib', freshenv=True, confoverrides={'xlink_generate_bib': False})
def test_bib_disabled_by_default(app, status, warning):
    """A build with xlink_generate_bib = False does not produce a .bib file."""
    bib_path = Path(app.srcdir) / 'references.bib'
    # Remove any leftover from previous test runs sharing the same srcdir
    if bib_path.exists():
        bib_path.unlink()

    app.build(force_all=True)

    assert not bib_path.exists(), "references.bib should NOT exist when xlink_generate_bib is False"


@pytest.mark.sphinx('html', testroot='bib', freshenv=True)
def test_bib_no_type_warning_for_string_config(app, status, warning):
    """Verify no type mismatch warning is emitted when xlink_generate_bib is a string.

    Sphinx warns when a config value's runtime type does not match the default's
    type unless valid types are explicitly declared. This test ensures the fix
    (declaring [bool, str] as accepted types) suppresses that warning.
    """
    app.build(force_all=True)

    warnings = warning.getvalue()
    # Check that no single warning line mentions both the config name and a type mismatch
    for line in warnings.splitlines():
        assert not ("has type" in line and "xlink_generate_bib" in line), (
            f"Type mismatch warning found for xlink_generate_bib: {line}"
        )
