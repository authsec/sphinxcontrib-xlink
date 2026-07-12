"""BibTeX .bib file generator for sphinxcontrib-xlink."""

import os
from sphinx.util import logging
from . import parse_tag_list

logger = logging.getLogger(__name__)


def generate_bib_file(app, exception):
    """Generate a .bib file from xlink entries tagged with bib:type:<entrytype>.

    Connected to the 'build-finished' Sphinx event.
    """
    if exception is not None:
        return

    config = app.config
    bib_path = config.xlink_generate_bib

    if not bib_path:
        return

    # Resolve the output path
    if not os.path.isabs(bib_path):
        bib_path = os.path.join(app.srcdir, bib_path)

    source_dir = os.path.normpath(os.path.join(app.srcdir, config.xlink_directory))
    if not os.path.isdir(source_dir):
        logger.warning("xlink-bib: xlink_directory '%s' not found. Skipping .bib generation.", config.xlink_directory)
        return

    required_fields_map = config.xlink_bib_required_fields
    entries = []

    for root, dirs, files in os.walk(source_dir):
        if '.xlink' in dirs:
            dirs.remove('.xlink')
        for filename in sorted(files):
            if not filename.endswith('.xlink'):
                continue
            filepath = os.path.join(root, filename)
            with open(filepath, 'r', encoding='utf-8-sig') as f:
                for line in f:
                    clean = line.strip()
                    if not clean or clean.startswith('#'):
                        continue
                    if ' :: ' not in clean:
                        continue
                    parts = [p.strip() for p in clean.split(' :: ', 3)]
                    if len(parts) not in (3, 4):
                        continue

                    lid, title, url = parts[:3]
                    raw_tags = parse_tag_list(parts[3]) if len(parts) == 4 else []

                    # Find bib:type tag
                    entry_type = None
                    bib_fields = {}

                    for tag in raw_tags:
                        if not tag.startswith('bib:'):
                            continue
                        remainder = tag[4:]  # strip 'bib:' prefix
                        field, _, value = remainder.partition(':')
                        if not field:
                            continue
                        # Strip surrounding quotes from value
                        value = value.strip('"')

                        if field == 'type':
                            entry_type = value
                        else:
                            bib_fields[field] = value

                    if entry_type is None:
                        continue

                    # Add title and url from the xlink entry (user tags take priority)
                    if 'title' not in bib_fields:
                        bib_fields['title'] = title
                    if 'url' not in bib_fields:
                        bib_fields['url'] = url

                    # Validate required fields
                    required = required_fields_map.get(entry_type, [])
                    missing = [f for f in required if f not in bib_fields]
                    if missing:
                        logger.warning(
                            "xlink-bib: Entry '%s' (type '%s') is missing required fields: %s",
                            lid, entry_type, ', '.join(missing)
                        )

                    entries.append((lid, entry_type, bib_fields))

    # Sort entries by cite key for deterministic output
    entries.sort(key=lambda e: e[0])

    # Write the .bib file
    lines = []
    for i, (cite_key, entry_type, fields) in enumerate(entries):
        if i > 0:
            lines.append('')
        lines.append(f'@{entry_type}{{{cite_key},')
        for field_name, field_value in fields.items():
            lines.append(f'  {field_name} = {{{field_value}}},')
        lines.append('}')

    os.makedirs(os.path.dirname(bib_path), exist_ok=True)
    with open(bib_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines))
        if lines:
            f.write('\n')

    logger.info("xlink-bib: Generated %s with %d entries.", bib_path, len(entries))
