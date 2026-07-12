import os
import sys
sys.path.insert(0, os.path.abspath('../../../src'))

extensions = ['sphinxcontrib.xlink']
project = 'XLink Tag Pattern Test'
html_theme = 'basic'

xlink_allowed_tags = {
    'general': ('General', 'General purpose links.'),
}

xlink_allowed_tag_patterns = {
    r'DR-\d{4}': ('Decision Record', 'Architecture decision records.'),
    r'KEY-\d+': ('JIRA Key', 'JIRA issue identifiers.'),
    r'\d{2}\.\d{2}': ('Version', 'Version identifiers.'),
    r'ADR\d{4}': ('ADR', 'Architecture decision records.'),
}

xlink_render_link_icon = False
xlink_directory = 'xlinks'
xlink_generate_vscode_snippets = False
