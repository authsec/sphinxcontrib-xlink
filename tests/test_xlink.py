import pytest
from bs4 import BeautifulSoup
from pathlib import Path
import re

# Add freshenv=True to prevent Sphinx from caching the environment across tests
@pytest.mark.sphinx('html', testroot='basic', freshenv=True)
def test_inline_roles(app, status, warning):
    app.build()
    
    html = Path(app.outdir / 'index.html').read_text(encoding='utf-8')
    soup = BeautifulSoup(html, 'html.parser')
    
    # Locate section by ID (using regex to handle potential slug variations)
    role_section = soup.find('section', id=re.compile(r'testing-roles'))
    assert role_section is not None, "Section 'testing-roles' not found."
    
    role_links = role_section.find_all('a', class_='xlink-link')
    assert len(role_links) == 2, "Should have rendered exactly 2 inline links"
    
    # Check titles defined in protocols.xlink
    assert "First Valid Link" in role_links[0].text
    assert "Click Here" in role_links[1].text

@pytest.mark.sphinx('html', testroot='basic', freshenv=True)
def test_directive_group_by_tag(app, status, warning):
    app.build()
    html = Path(app.outdir / 'index.html').read_text(encoding='utf-8')
    soup = BeautifulSoup(html, 'html.parser')
    
    container = soup.find('div', class_='xlink-list-container')
    assert container is not None, "xlink-list-container not found"
    
    page_text = container.get_text()
    # Verify titles from conf.py:xlink_allowed_tags
    assert "Software Engineer" in page_text
    assert "Project Management" in page_text
    assert "Threat Model" in page_text
    assert "Coding" in page_text

@pytest.mark.sphinx('html', testroot='basic', freshenv=True)
def test_malformed_warnings(app, status, warning):
    from sphinxcontrib.xlink import directives, roles
    
    # Reset warning cache for a clean capture
    directives._WARNED_ENTRIES.clear()
    roles._WARNED_ENTRIES.clear()
    
    app.build(force_all=True)
    warnings = warning.getvalue()
    
    # Check for expected parsing warnings
    assert "Missing ' :: ' delimiter" in warnings
    assert "bad-2-entirely-missing-delimiter" in warnings
    assert "Expected 3 or 4 parts" in warnings
    assert "bad-1 :: Only Two Parts" in warnings
    assert "Unknown tag 'made-up-tag'" in warnings

@pytest.mark.sphinx('html', testroot='basic', freshenv=True)
def test_description_visibility(app, status, warning):
    app.build()
    html = (app.outdir / 'index.html').read_text()
    soup = BeautifulSoup(html, 'html.parser')
    page_text = soup.get_text()

    # 1. Global visibility check
    assert "Detailed desc for Example1." not in page_text # Hidden via ! in index.rst
    assert "Detailed desc for Example2." in page_text     # Visible

    # Helper to find a section based on a text string anywhere inside its heading
    def find_section_by_text(search_text):
        text_node = soup.find(string=re.compile(re.escape(search_text)))
        return text_node.find_parent('section') if text_node else None

    ex1_section = find_section_by_text('Example1 File')
    ex2_section = find_section_by_text('Example2 File')
    
    assert ex1_section is not None, "Example1 File container not found"
    assert ex2_section is not None, "Example2 File container not found"

    # 2. Test Tag Hiding (!engineer prefix) under Example1
    eng_text_node = ex1_section.find(string=re.compile(r'Software Engineer'))
    ex1_eng_section = eng_text_node.find_parent('section')
    # The 'xlink-tag-description' div should be missing
    assert ex1_eng_section.find('div', class_='xlink-tag-description', recursive=False) is None

    # 3. Test Suffix Cascade (manager!![productivity-apps]) under Example2
    man_text_node = ex2_section.find(string=re.compile(r'Project Management'))
    man_section = man_text_node.find_parent('section')
    assert "Links for tracking milestones" in man_section.get_text()
    
    # Child 'Productivity' under Manager should NOT have a description due to !!
    prod_text_node = man_section.find(string=re.compile(r'Productivity'))
    man_prod_section = prod_text_node.find_parent('section')
    assert man_prod_section.find('div', class_='xlink-tag-description', recursive=False) is None

    # 4. Verify Visibility (Productivity under Engineer should be SHOWN)
    eng_text_ex2 = ex2_section.find(string=re.compile(r'Software Engineer'))
    ex2_eng_sec = eng_text_ex2.find_parent('section')
    eng_prod_text = ex2_eng_sec.find(string=re.compile(r'Productivity'))
    eng_prod_sec = eng_prod_text.find_parent('section')
    assert eng_prod_sec.find('div', class_='xlink-tag-description', recursive=False) is not None