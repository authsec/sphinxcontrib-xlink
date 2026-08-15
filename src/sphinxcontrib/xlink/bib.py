"""BibTeX .bib file generator for sphinxcontrib-xlink.

This module provides the BibTeX generation pipeline in two public phases:

1. ``collect_bib_entries(app)`` — walks .xlink files and extracts entries
   tagged with ``bib:type:<entrytype>``, returning a list of entry tuples.
2. ``write_bib_file(entries, bib_path)`` — serializes collected entries to
   a ``.bib`` file at the given path.

The high-level ``generate_bib_file(app, exception)`` function connects to
Sphinx's ``build-finished`` event and orchestrates both phases. Child themes
or extensions can call ``collect_bib_entries`` directly and provide their
own serializer for alternative output formats (RIS, CSL-JSON, etc.).
"""

import os
from sphinx.util import logging
from . import parse_tag_list

logger = logging.getLogger(__name__)

# Default output filename when xlink_generate_bib is set to True (non-string truthy).
_DEFAULT_BIB_FILENAME = 'references.bib'


def collect_bib_entries(app):
    """Collect BibTeX entries from .xlink files.

    Walks the configured xlink directory and extracts entries tagged with
    ``bib:type:<entrytype>``. Each entry's xlink ID becomes the cite key,
    and ``title``/``url`` are inherited from the xlink line unless explicitly
    overridden by ``bib:title:...`` or ``bib:url:...`` tags.

    Args:
        app: The Sphinx application instance.

    Returns:
        A sorted list of ``(cite_key, entry_type, fields_dict)`` tuples,
        ordered alphabetically by cite key for deterministic output.
        Returns an empty list if the xlink directory does not exist.
    """
    config = app.config
    source_dir = os.path.normpath(os.path.join(app.srcdir, config.xlink_directory))

    if not os.path.isdir(source_dir):
        logger.warning(
            "xlink-bib: xlink_directory '%s' not found. Skipping .bib generation.",
            config.xlink_directory,
        )
        return []

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

                    # Parse bib: tags.  Tag anatomy: bib:<field>:<value>
                    # The first colon after "bib:" separates field from value;
                    # subsequent colons are part of the value (e.g. URLs, DOIs).
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
    return entries


def write_bib_file(entries, bib_path):
    """Serialize BibTeX entries to a .bib file.

    Args:
        entries: A list of ``(cite_key, entry_type, fields_dict)`` tuples
            as returned by :func:`collect_bib_entries`.
        bib_path: Absolute path where the .bib file will be written.
            Parent directories are created if they do not exist.

    Returns:
        The number of entries written.
    """
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

    return len(entries)


def generate_bib_file(app, exception):
    """Generate a .bib file from xlink entries tagged with bib:type:<entrytype>.

    Connected to the 'build-finished' Sphinx event. Orchestrates
    :func:`collect_bib_entries` and :func:`write_bib_file`.

    The ``xlink_generate_bib`` config value controls behavior:

    - ``False`` (default): generation is disabled.
    - ``True``: generates ``references.bib`` in the source directory.
    - A string path: generates the .bib file at that path (relative to
      srcdir, or absolute).
    """
    if exception is not None:
        return

    config = app.config
    bib_path = config.xlink_generate_bib

    if not bib_path:
        return

    # Handle True (non-string truthy) by using a sensible default filename.
    if bib_path is True:
        bib_path = _DEFAULT_BIB_FILENAME

    # Resolve the output path
    if not os.path.isabs(bib_path):
        bib_path = os.path.join(app.srcdir, bib_path)

    entries = collect_bib_entries(app)
    if not entries and not os.path.isdir(os.path.normpath(os.path.join(app.srcdir, config.xlink_directory))):
        return

    count = write_bib_file(entries, bib_path)
    logger.info("xlink-bib: Generated %s with %d entries.", bib_path, count)
