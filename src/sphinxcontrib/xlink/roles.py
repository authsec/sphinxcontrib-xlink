import os
import re
from docutils import nodes
from sphinx.util import logging

logger = logging.getLogger(__name__)

_WARNED_ENTRIES = set()

def xlink_role(name, rawtext, text, lineno, inliner, options=None, content=None):
    env = inliner.document.settings.env
    config = env.config
    label = None
    key = None

    bracket_match = re.search(r'^(?P<label>.*)\s*<(?P<key>.*)>$', text)
    if bracket_match:
        label = bracket_match.group('label').strip()
        key = bracket_match.group('key').strip()
    elif "~@~" in text:
        logger.warning('xlink: The "~@~" separator is deprecated. Use :xlink:`Label <key>` instead.', location=(env.docname, lineno))
        parts = text.split("~@~")
        label = parts[0].strip()
        key = parts[1].strip() if len(parts) > 1 else parts[0].strip()
    else:
        label = key = text.strip()

    key = key.strip('` ')
    source_directory = os.path.normpath(os.path.join(env.srcdir, config.xlink_directory))
    if not os.path.isdir(source_directory):
        return [], []

    key_value_pairs = {}
    
    # FIXED: Re-applied os.walk for recursive folder support
    for root, dirs, files in os.walk(source_directory):
        if '.xlink' in dirs: dirs.remove('.xlink')
        for filename in files:
            if filename.endswith('.xlink'):
                with open(os.path.join(root, filename), "r", encoding="utf-8-sig") as file:
                    for line_num, line in enumerate(file, 1):
                        clean_line = line.strip()
                        if not clean_line or clean_line.startswith('#'):
                            continue

                        if " :: " in clean_line:
                            p = [i.strip() for i in clean_line.split(" :: ", 3)]
                            if len(p) in (3, 4):
                                key_value_pairs[p[0]] = (p[1], p[2])
                            else:
                                warning_key = f"{filename}:{line_num}"
                                if warning_key not in _WARNED_ENTRIES:
                                    logger.warning(f"xlink: Malformed entry in {filename}:{line_num} (Expected 3 or 4 parts). Check spaces around '::'. Line: '{clean_line}'", location=(env.docname, lineno))
                                    _WARNED_ENTRIES.add(warning_key)
                        else:
                            warning_key = f"{filename}:{line_num}"
                            if warning_key not in _WARNED_ENTRIES:
                                logger.warning(f"xlink: Malformed entry in {filename}:{line_num} (Missing ' :: ' delimiter). Line: '{clean_line}'", location=(env.docname, lineno))
                                _WARNED_ENTRIES.add(warning_key)

    if key not in key_value_pairs:
        msg = inliner.reporter.error(f'xlink ID "{key}" not found.', line=lineno)
        return [inliner.problematic(rawtext, rawtext, msg)], [msg]

    description, url = key_value_pairs[key]
    link_text = label if (label and label != key) else description
    
    result_nodes = []
    if config.xlink_render_link_icon and env.app.builder.name == 'html':
        icon = nodes.inline(classes=['xlink-icon', 'fa-solid', 'fa-arrow-up-right-from-square'])
        icon.append(nodes.Text(' '))
        result_nodes.append(icon)

    link = nodes.reference(rawtext, link_text, refuri=url, classes=['xlink-link'], target='_blank')
    result_nodes.append(link)
    return result_nodes, []