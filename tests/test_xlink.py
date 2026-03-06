import pytest
from bs4 import BeautifulSoup
from pathlib import Path
import re

@pytest.mark.sphinx('html', testroot='basic', freshenv=True)
def test_inline_roles(app, status, warning):
    app.build()
    
    html = Path(app.outdir / 'index.html').read_text(encoding='utf-8')
    soup = BeautifulSoup(html, 'html.parser')
    
    role_section = soup.find('section', id=re.compile(r'testing-roles'))
    assert role_section is not None, "Section 'testing-roles' not found."
    
    role_links = role_section.find_all('a', class_='xlink-link')
    assert len(role_links) == 2, "Should have rendered exactly 2 inline links"
    
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
    assert "Software Engineer" in page_text
    assert "Project Management" in page_text
    assert "Threat Model" in page_text
    assert "Coding" in page_text

@pytest.mark.sphinx('html', testroot='basic', freshenv=True)
def test_malformed_warnings(app, status, warning):
    from sphinxcontrib.xlink import directives, roles
    
    directives._WARNED_ENTRIES.clear()
    roles._WARNED_ENTRIES.clear()
    
    app.build(force_all=True)
    warnings = warning.getvalue()
    
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
    
    # Isolate the assertions strictly to the Test Project section
    # This prevents the test from failing due to the newly added Toctree lists at the bottom of the page
    test_project_section = soup.find('section', id=re.compile(r'test-project'))
    assert test_project_section is not None, "Test Project section not found"
    
    section_text = test_project_section.get_text()

    assert "Detailed desc for Example1." not in section_text 
    assert "Detailed desc for Example2." in section_text     

    def find_section_by_text(search_text):
        text_node = test_project_section.find(string=re.compile(re.escape(search_text)))
        return text_node.find_parent('section') if text_node else None

    ex1_section = find_section_by_text('Example1 File')
    ex2_section = find_section_by_text('Example2 File')
    
    assert ex1_section is not None, "Example1 File container not found"
    assert ex2_section is not None, "Example2 File container not found"

    eng_text_node = ex1_section.find(string=re.compile(r'Software Engineer'))
    ex1_eng_section = eng_text_node.find_parent('section')
    assert ex1_eng_section.find('div', class_='xlink-tag-description', recursive=False) is None

    man_text_node = ex2_section.find(string=re.compile(r'Project Management'))
    man_section = man_text_node.find_parent('section')
    assert "Links for tracking milestones" in man_section.get_text()
    
    prod_text_node = man_section.find(string=re.compile(r'Productivity'))
    man_prod_section = prod_text_node.find_parent('section')
    assert man_prod_section.find('div', class_='xlink-tag-description', recursive=False) is None

    eng_text_ex2 = ex2_section.find(string=re.compile(r'Software Engineer'))
    ex2_eng_sec = eng_text_ex2.find_parent('section')
    eng_prod_text = ex2_eng_sec.find(string=re.compile(r'Productivity'))
    eng_prod_sec = eng_prod_text.find_parent('section')
    assert eng_prod_sec.find('div', class_='xlink-tag-description', recursive=False) is not None

@pytest.mark.sphinx('html', testroot='basic', freshenv=True)
def test_query_filtering(app, status, warning):
    from sphinxcontrib.xlink import directives
    directives._WARNED_ENTRIES.clear()
    
    app.build()
    html = (app.outdir / 'index.html').read_text(encoding='utf-8')
    soup = BeautifulSoup(html, 'html.parser')

    warnings = warning.getvalue()
    assert "Detected accidental ':query:' prefix" in warnings

    container_1 = soup.find('div', class_='query-test-list-1')
    assert container_1 is not None, "query-test-list-1 container missing"
    
    links_1 = container_1.find_all('a', class_='xlink-link')
    assert len(links_1) == 1, f"Expected 1 match, found {len(links_1)}"
    assert links_1[0].text == "Link 1"
    
    container_2 = soup.find('div', class_='query-test-list-2')
    assert container_2 is not None, "query-test-list-2 container missing"
    
    links_2 = container_2.find_all('a', class_='xlink-link')
    assert len(links_2) == 2, f"Expected 2 matches, found {len(links_2)}"
    
    found_texts = [l.text for l in links_2]
    assert "Second Valid Link" in found_texts
    assert "Third Valid Link" in found_texts

    container_3 = soup.find('div', class_='query-test-list-3')
    assert container_3 is not None, "query-test-list-3 container missing"
    links_3 = container_3.find_all('a', class_='xlink-link')
    assert len(links_3) == 1, f"Expected 1 match for stripped query, found {len(links_3)}"

@pytest.mark.sphinx('html', testroot='basic', freshenv=True)
def test_add_to_toctree_and_prefixes(app, status, warning):
    app.build()
    html = (app.outdir / 'index.html').read_text(encoding='utf-8')
    soup = BeautifulSoup(html, 'html.parser')

    toctree_section = soup.find('section', id=re.compile(r'testing-toctree-integration'))
    assert toctree_section is not None, "Toctree testing section not found"

    child_sections = toctree_section.find_all('section', recursive=False)
    assert len(child_sections) > 0, "No raw section nodes were appended to the document root"

    # 1. The list should automatically generate a prefix like xlink-X-example1-file
    auto_section = soup.find('section', id=re.compile(r'^xlink-\d+-example1-file'))
    assert auto_section is not None, "Auto-generated namespace prefix not applied to sections"

    # 2. The explicit id-prefix directive should have 'custom-prefix-example1-file'
    custom_section = soup.find('section', id='custom-prefix-example1-file')
    assert custom_section is not None, "Explicit id-prefix option was ignored"