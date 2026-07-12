import pytest
from bs4 import BeautifulSoup
from pathlib import Path


@pytest.mark.sphinx('html', testroot='tag-patterns', freshenv=True)
def test_pattern_tags_are_accepted(app, status, warning):
    """Tags matching xlink_allowed_tag_patterns should not produce warnings."""
    from sphinxcontrib.xlink import directives, _compiled_tag_patterns
    import sphinxcontrib.xlink as xlink_mod
    directives._WARNED_ENTRIES.clear()
    xlink_mod._compiled_tag_patterns = None  # Reset cache

    app.build(force_all=True)
    warnings = warning.getvalue()

    # Pattern-matched tags should NOT produce warnings
    assert "Unknown tag 'DR-0001'" not in warnings
    assert "Unknown tag 'DR-0002'" not in warnings
    assert "Unknown tag 'ADR0001'" not in warnings
    assert "Unknown tag '11.21'" not in warnings
    assert "Unknown tag 'KEY-42'" not in warnings

    # Static tag should not produce a warning either
    assert "Unknown tag 'general'" not in warnings

    # Invalid tag SHOULD produce a warning
    assert "Unknown tag 'INVALID-TAG'" in warnings


@pytest.mark.sphinx('html', testroot='tag-patterns', freshenv=True)
def test_pattern_tags_resolve_to_literal_value(app, status, warning):
    """Pattern-matched tags should use their literal value as display name."""
    import sphinxcontrib.xlink as xlink_mod
    xlink_mod._compiled_tag_patterns = None

    app.build()
    html = Path(app.outdir / 'index.html').read_text(encoding='utf-8')
    soup = BeautifulSoup(html, 'html.parser')

    container = soup.find('div', class_='pattern-test-list')
    assert container is not None, "pattern-test-list container not found"

    page_text = container.get_text()

    # Pattern tags should appear as their literal values (not the pattern's display name)
    assert "DR-0001" in page_text
    assert "DR-0002" in page_text
    assert "ADR0001" in page_text
    assert "11.21" in page_text
    assert "KEY-42" in page_text

    # Static tag should use its configured display name
    assert "General" in page_text


@pytest.mark.sphinx('html', testroot='tag-patterns', freshenv=True)
def test_pattern_tags_in_tag_filter(app, status, warning):
    """Pattern-matched tags should work in :tags: filter option."""
    import sphinxcontrib.xlink as xlink_mod
    xlink_mod._compiled_tag_patterns = None

    app.build()
    html = Path(app.outdir / 'index.html').read_text(encoding='utf-8')
    soup = BeautifulSoup(html, 'html.parser')

    container = soup.find('div', class_='pattern-filter-list')
    assert container is not None, "pattern-filter-list container not found"

    links = container.find_all('a', class_='xlink-link')
    link_texts = [l.text for l in links]

    # Only DR-0001 and DR-0002 tagged links should appear
    assert "Use PostgreSQL" in link_texts
    assert "Use REST API" in link_texts
    assert "Adopt Microservices" not in link_texts
    assert "Version Link" not in link_texts
    assert "JIRA Issue" not in link_texts


@pytest.mark.sphinx('html', testroot='tag-patterns', freshenv=True)
def test_pattern_tag_fullmatch_required(app, status, warning):
    """Pattern must match the entire tag (fullmatch), not just a substring."""
    from sphinxcontrib.xlink import is_tag_allowed
    import sphinxcontrib.xlink as xlink_mod
    xlink_mod._compiled_tag_patterns = None

    app.build()
    config = app.config

    # Should match
    assert is_tag_allowed('DR-0001', config) is True
    assert is_tag_allowed('DR-9999', config) is True
    assert is_tag_allowed('KEY-1', config) is True
    assert is_tag_allowed('KEY-12345', config) is True
    assert is_tag_allowed('ADR0001', config) is True
    assert is_tag_allowed('11.21', config) is True

    # Should NOT match (partial matches)
    assert is_tag_allowed('DR-00011', config) is False  # Too many digits
    assert is_tag_allowed('XDR-0001', config) is False  # Prefix added
    assert is_tag_allowed('DR-001', config) is False    # Too few digits
    assert is_tag_allowed('KEY-', config) is False      # No digits
    assert is_tag_allowed('ADR00011', config) is False  # Too many digits
    assert is_tag_allowed('111.21', config) is False    # Three digits before dot

    # Static tag
    assert is_tag_allowed('general', config) is True
    assert is_tag_allowed('nonexistent', config) is False
