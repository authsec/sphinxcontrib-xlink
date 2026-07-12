import os
import sys
sys.path.insert(0, os.path.abspath('../../../src'))

extensions = ['sphinxcontrib.xlink']
project = 'XLink RSTI Error Test'
html_theme = 'basic'

xlink_allowed_tags = {}
xlink_generate_vscode_snippets = False
xlink_directory = 'xlinks'
