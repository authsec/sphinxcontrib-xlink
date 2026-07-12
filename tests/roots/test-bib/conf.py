import os, sys
sys.path.insert(0, os.path.abspath('../../../src'))

extensions = ['sphinxcontrib.xlink']
project = 'XLink Bib Test'
html_theme = 'basic'

xlink_allowed_tags = {
    'general': ('General', 'General purpose links.'),
}
xlink_allowed_tag_patterns = {
    r'bib:[a-z]+:.*': ('BibTeX', 'BibTeX metadata tags.'),
}
xlink_generate_bib = 'references.bib'
xlink_directory = 'xlinks'
xlink_generate_vscode_snippets = False
xlink_render_link_icon = False
