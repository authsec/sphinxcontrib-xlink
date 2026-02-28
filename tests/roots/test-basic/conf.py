import os
import sys
sys.path.insert(0, os.path.abspath('../../../src'))

extensions = ['sphinxcontrib.xlink']
project = 'XLink Test'
html_theme = 'basic'

xlink_allowed_tags = {
    'engineer': ('Software Engineer', 'Resources for the **technical** staff.'),
    'manager': ('Project Management', 'Links for tracking *milestones* and budgets.'),
    'code': ('Coding', 'Standard *coding* practices.'),
    'productivity-apps': ('Productivity', 'Apps to boost your **focus**.'),
    'threat-model': ('Threat Model', 'Security analysis links.')
}

xlink_default_untagged_name = 'Uncategorized'
xlink_render_link_icon = False # Disabled to make HTML assertions simpler

xlink_directory = 'xlinks'
xlink_generate_vscode_snippets = False  # Disable for tests