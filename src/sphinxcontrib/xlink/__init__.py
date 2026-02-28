import os
import re
import json
import glob
import unicodedata
from docutils import nodes
from docutils.transforms import Transform
from sphinx.addnodes import pending_xref
from sphinx.util.nodes import make_refnode
from sphinx.util import logging

logger = logging.getLogger(__name__)

class xlink_reference(nodes.Inline, nodes.TextElement):
    pass

def visit_xlink_reference_latex(self, node):
    uri = node.get('refuri', '')
    escaped_uri = uri.replace('\\', '\\\\').replace('%', '\\%').replace('#', '\\#')
    self.body.append(r'\sphinxhref{%s}{' % escaped_uri)

def depart_xlink_reference_latex(self, node):
    uri = node.get('refuri', '')
    style = node.get('xlink_latex_style', 'no')
    escaped_uri = uri.replace('\\', '\\\\').replace('%', '\\%').replace('#', '\\#')
    
    self.body.append('}')
    if style == 'inline':
        self.body.append(r' (\nolinkurl{%s})' % uri)
    elif style == 'footnote':
        self.body.append(r'\footnote{\nolinkurl{%s}}' % escaped_uri)

def downgrade_xlink_nodes(app, doctree, fromdocname):
    if getattr(app.builder, 'format', '') == 'latex' or app.builder.name == 'latex':
        return
        
    iterator = doctree.findall(xlink_reference) if hasattr(doctree, 'findall') else doctree.traverse(xlink_reference)
    for node in list(iterator):
        new_node = nodes.reference(**node.attributes)
        new_node.extend(node.children)
        node.replace_self(new_node)


# --- Custom Transform Engine for Terms & Refs ---

class XLinkSubstitutionTransform(Transform):
    """
    Intercepts |xlink-term-xxx| and |xlink-ref-xxx| before Docutils triggers a 
    missing substitution warning, and converts them into pending cross-references.
    """
    default_priority = 210

    def apply(self):
        for node in list(self.document.findall(nodes.substitution_reference)):
            refname = node['refname']
            
            # 1. Handle Glossary Terms
            if refname.startswith('xlink-term-'):
                slug = refname[11:] 
                
                is_full = False
                if slug.endswith('-full'):
                    slug = slug[:-5]
                    is_full = True

                xref = pending_xref(
                    '',
                    refdomain='std',
                    reftype='term',
                    reftarget=slug,
                    refexplicit=False, 
                    refwarn=True,
                    modname=None,
                    classname=None,
                    xlink_is_full=is_full
                )
                xref['refdoc'] = self.document.settings.env.docname
                xref += nodes.inline('', f'|{refname}|', classes=['xlink-term-placeholder'])
                node.replace_self(xref)

            # 2. Handle Document Section References
            elif refname.startswith('xlink-ref-'):
                slug = refname[10:]
                
                xref = pending_xref(
                    '',
                    refdomain='std',
                    reftype='ref',
                    reftarget=slug,
                    refexplicit=False,
                    refwarn=True,
                    modname=None,
                    classname=None
                )
                xref['refdoc'] = self.document.settings.env.docname
                xref += nodes.inline('', f'|{refname}|', classes=['xlink-ref-placeholder'])
                node.replace_self(xref)


def resolve_xlink_term(app, env, node, contnode):
    """
    Catches the pending cross-reference created by the Transform and 
    maps it perfectly to the correct Glossary term, preserving exact casing.
    """
    if node.get('reftype') == 'term' and node.get('xlink_is_full') is not None:
        slug = node['reftarget']
        is_full = node['xlink_is_full']
        
        std_domain = env.domains.get('std')
        if not std_domain: 
            return None
        
        for obj in std_domain.get_objects():
            if obj[2] == 'term':
                term = obj[1]
                
                match = re.search(r'^(.*?)\s*\((.*?)\)$', term)
                if match:
                    short_text = match.group(2).strip()
                    normalized = unicodedata.normalize('NFD', short_text).encode('ascii', 'ignore').decode('utf-8')
                    term_slug = re.sub(r'[^a-z0-9]+', '-', normalized.lower()).strip('-')
                    display_text = term if is_full else short_text
                else:
                    normalized = unicodedata.normalize('NFD', term).encode('ascii', 'ignore').decode('utf-8')
                    term_slug = re.sub(r'[^a-z0-9]+', '-', normalized.lower()).strip('-')
                    display_text = term
                    
                if term_slug == slug:
                    docname = obj[3]
                    anchor = obj[4]
                    
                    refnode = make_refnode(
                        app.builder, 
                        node['refdoc'], 
                        docname, 
                        anchor,
                        nodes.inline('', display_text, classes=['xref', 'std', 'std-term']),
                        term
                    )
                    return refnode
                    
        return None


# --- Automated Header Labeling ---

def auto_label_sections(app, doctree):
    """
    Automatically creates a clean, normalized standard label for every heading 
    in the project so it can be referenced instantly via :ref:.
    """
    env = app.env
    std = env.domains.get('std')
    if not std: return
    
    for node in doctree.findall(nodes.section):
        title_node = next(node.findall(nodes.title), None)
        if title_node:
            title_text = title_node.astext()
            normalized = unicodedata.normalize('NFD', title_text).encode('ascii', 'ignore').decode('utf-8')
            slug = re.sub(r'[^a-z0-9]+', '-', normalized.lower()).strip('-')
            
            if not slug: continue
            
            node_id = node['ids'][0] if node['ids'] else slug
            
            if slug not in std.labels:
                std.labels[slug] = (env.docname, node_id, title_text)
                std.anonlabels[slug] = (env.docname, node_id)


# --- Sphinx-Needs Integration ---

def _get_xlink_data(app, link_id):
    """Internal helper to find link data for dynamic functions."""
    env = app.env
    config = env.config
    source_dir = os.path.normpath(os.path.join(env.srcdir, config.xlink_directory))
    
    if not os.path.isdir(source_dir):
        return None, None

    for filename in os.listdir(source_dir):
        if filename.endswith('.xlink'):
            path = os.path.join(source_dir, filename)
            with open(path, "r", encoding="utf-8-sig") as f:
                for line in f:
                    clean = line.strip()
                    if not clean or clean.startswith('#'): continue
                    if " :: " in clean:
                        parts = [p.strip() for p in clean.split(" :: ", 3)]
                        if len(parts) >= 3 and parts[0] == link_id:
                            return parts[1], parts[2]
    return None, None

def xlink_func(app, need, needs, link_ids):
    """Returns 'Title <URL>; ' for one or more link IDs in sphinx-needs."""
    if isinstance(link_ids, str):
        link_ids = [i.strip() for i in link_ids.split(',')]
    
    results = []
    for lid in link_ids:
        title, url = _get_xlink_data(app, lid)
        if title and url:
            results.append(f"{title} <{url}>")
        else:
            logger.warning(f"xlink: ID '{lid}' not found in needs function.")
            
    return "; ".join(results) if results else ""

def xlink_url(app, need, needs, link_ids):
    """Returns semicolon-separated raw URLs for sphinx-needs."""
    if isinstance(link_ids, str):
        link_ids = [i.strip() for i in link_ids.split(',')]
    
    results = []
    for lid in link_ids:
        _, url = _get_xlink_data(app, lid)
        if url: results.append(url)
    return "; ".join(results)

def xlink_title(app, need, needs, link_ids):
    """Returns semicolon-separated titles for sphinx-needs."""
    if isinstance(link_ids, str):
        link_ids = [i.strip() for i in link_ids.split(',')]
    
    results = []
    for lid in link_ids:
        title, _ = _get_xlink_data(app, lid)
        if title: results.append(title)
    return "; ".join(results)

def register_needs_integration(app, config):
    """Registers functions and default string_links if sphinx-needs is present."""
    if 'sphinx_needs' not in config.extensions and 'sphinxcontrib.needs' not in config.extensions:
        return

    # To avoid the 'unpickleable configuration value' warning, we ensure 
    # needs_functions is managed carefully.
    if not hasattr(config, 'needs_functions'):
        config.needs_functions = []
    
    # We use a list of tuples (function, name)
    funcs_to_add = [
        (xlink_func, 'xlink'), 
        (xlink_url, 'xlink_url'), 
        (xlink_title, 'xlink_title')
    ]
    
    # Get currently registered function names to avoid duplicates
    existing_names = []
    for f in config.needs_functions:
        if callable(f):
            existing_names.append(getattr(f, '__name__', ''))
        elif isinstance(f, (list, tuple)) and len(f) > 1:
            existing_names.append(f[1])

    for func, name in funcs_to_add:
        if name not in existing_names:
            # Setting the name on the function object helps sphinx-needs resolution
            func.__name__ = name
            config.needs_functions.append(func)

    # Register Default String Link Mapping
    target_options = getattr(config, 'xlink_needs_string_link_options', ['xlink'])
    
    xlink_mapping = {
        'regex': r'^(?P<name>.*?) <(?P<url>.*?)>$',
        'link_url': '{{url}}',
        'link_name': '{{name}}',
        'options': target_options 
    }

    if not hasattr(config, 'needs_string_links'):
        config.needs_string_links = {}
    
    if 'xlink' not in config.needs_string_links:
        config.needs_string_links['xlink'] = xlink_mapping


# --- VSCode Snippet Generators ---

def generate_vscode_snippets(app):
    config = app.config
    if not config.xlink_generate_vscode_snippets: return

    vscode_dir = os.path.join(os.path.dirname(app.srcdir), '.vscode')
    snippet_file = os.path.join(vscode_dir, 'xlinks.json.code-snippets')
    xlink_dir = os.path.normpath(os.path.join(app.srcdir, config.xlink_directory))
    
    if not os.path.isdir(xlink_dir): return

    snippets = {}
    id_list = []
    file_list = []
    
    for filename in os.listdir(xlink_dir):
        if filename.endswith('.xlink'):
            file_list.append(filename[:-6])
            with open(os.path.join(xlink_dir, filename), "r", encoding="utf-8-sig") as f:
                for line in f:
                    clean_line = line.strip()
                    if not clean_line or clean_line.startswith('#'): continue
                    if " :: " in clean_line:
                        parts = [p.strip() for p in clean_line.split(" :: ", 3)]
                        if len(parts) in (3, 4):
                            lid, title, _ = parts[:3]
                            tags = parts[3].strip() if len(parts) == 4 else ""
                            id_list.append((lid, title))
                            
                            description = f"Title:\n{title}\n\nID: {lid}"
                            if tags: description += f"\nTags: {tags}"
                            
                            snippets[f"xlink-{lid}"] = {
                                "prefix": [f"ddxl-{title}", f"ddxl-{lid}"],
                                "body": [f":xlink:`{lid}`$0"],
                                "description": description
                            }

    if not id_list: return
    id_list.sort()
    file_list.sort()
    
    escaped_ids = ",".join([item[0].replace(',', '\\,') for item in id_list])
    file_choices = ",".join([f.replace(',', '\\,') for f in file_list]) if file_list else ""
    file_snippet = f"${{1|{file_choices}|}}" if file_choices else "${1:filename}"
    tags_list = sorted(list(config.xlink_allowed_tags.keys()))
    tag_choices = ",".join([t.replace(',', '\\,') for t in tags_list]) if tags_list else ""
    tag_snippet = f"${{2|{tag_choices}|}}" if tag_choices else "${2:tag1, tag2}"

    snippets["ddxl-xlink-select-id"] = {
        "prefix": "ddxl-id-select",
        "body": [f":xlink:`${{1|{escaped_ids}|}}`$0"],
        "description": "Select xlink ID from dropdown."
    }
    snippets["ddxl-xlink-select-name"] = {
        "prefix": "ddxl-name-select",
        "body": [f":xlink:`${{2:Alternative Name}} <${{1|{escaped_ids}|}}>`$0"],
        "description": "Select ID from dropdown, then provide custom label."
    }
    snippets["ddxl-xlink-directive-simple"] = {
        "prefix": [".. xlink-list", "ddxl-list-simple"],
        "body": [
            ".. xlink-list::",
            "   :group-by: ${1|tag,file,tag\\, file,file\\, tag|}",
            f"   :tags: {tag_snippet}",
            "   $0"
        ],
        "description": "Insert a simple xlink-list grouped by tags or files."
    }

    try:
        os.makedirs(vscode_dir, exist_ok=True)
        with open(snippet_file, 'w', encoding='utf-8') as f:
            json.dump(snippets, f, indent=2)
    except Exception: pass

def generate_vscode_term_snippets(app, env):
    if not app.config.xlink_generate_vscode_snippets: return
    std_domain = env.domains.get('std')
    if not std_domain: return

    terms = [obj[1] for obj in std_domain.get_objects() if obj[2] == 'term']
    snippet_file = os.path.join(os.path.dirname(app.srcdir), '.vscode', 'xlink-terms.json.code-snippets')

    if not terms:
        if os.path.exists(snippet_file):
            try: os.remove(snippet_file)
            except Exception: pass
        return

    snippets = {}
    for term in sorted(terms):
        match = re.search(r'^(.*?)\s*\((.*?)\)$', term)
        short_text = match.group(2).strip() if match else term.strip()
        normalized = unicodedata.normalize('NFD', short_text).encode('ascii', 'ignore').decode('utf-8')
        slug = re.sub(r'[^a-z0-9]+', '-', normalized.lower()).strip('-')
        if not slug: continue

        snippets[f"xlink-term-{slug}"] = {
            "prefix": [f"ddxt-{short_text}", f"ddxt-{slug}"],
            "body": [f"|xlink-term-{slug}|"],
            "description": f"Glossary Link: {short_text}"
        }
        snippets[f"xlink-term-{slug}-full"] = {
            "prefix": [f"ddxt-{term}", f"ddxt-{slug}-full"],
            "body": [f"|xlink-term-{slug}-full|"],
            "description": f"Glossary Link (Full): {term}"
        }

    try:
        with open(snippet_file, 'w', encoding='utf-8') as f:
            json.dump(snippets, f, indent=2)
    except Exception: pass

def generate_vscode_ref_snippets(app, env):
    if not app.config.xlink_generate_vscode_snippets: return
    std_domain = env.domains.get('std')
    if not std_domain: return

    labels = std_domain.labels
    snippet_file = os.path.join(os.path.dirname(app.srcdir), '.vscode', 'xlink-refs.json.code-snippets')

    if not labels:
        if os.path.exists(snippet_file):
            try: os.remove(snippet_file)
            except Exception: pass
        return

    snippets = {}
    for label_name, (docname, labelid, sectname) in labels.items():
        if not isinstance(label_name, str): continue
        if label_name in ['genindex', 'modindex', 'search']: continue
        display_title = sectname if sectname else label_name
        
        snippets[f"xlink-ref-{label_name}"] = {
            "prefix": [f"ddxr-{display_title}", f"ddxr-{label_name}"],
            "body": [f"|xlink-ref-{label_name}|"],
            "description": f"Section Ref: {display_title} (in {docname})"
        }

    try:
        with open(snippet_file, 'w', encoding='utf-8') as f:
            json.dump(snippets, f, indent=2)
    except Exception: pass

def generate_vscode_needs_snippets(app, env):
    """Generates ddxn- snippets for sphinx-needs usage."""
    if not app.config.xlink_generate_vscode_snippets: return
    
    vscode_dir = os.path.join(os.path.dirname(app.srcdir), '.vscode')
    snippet_file = os.path.join(vscode_dir, 'xlink-needs.json.code-snippets')
    
    id_list = []
    source_dir = os.path.normpath(os.path.join(app.srcdir, app.config.xlink_directory))
    if os.path.isdir(source_dir):
        for filename in os.listdir(source_dir):
            if filename.endswith('.xlink'):
                with open(os.path.join(source_dir, filename), "r", encoding="utf-8-sig") as f:
                    for line in f:
                        if " :: " in line and not line.strip().startswith('#'):
                            parts = line.split(" :: ")
                            id_list.append((parts[0].strip(), parts[1].strip()))

    snippets = {}
    for lid, title in id_list:
        snippets[f"needs-xlink-{lid}"] = {
            "prefix": [f"ddxn-{title}", f"ddxn-{lid}"],
            "body": [f"[[ xlink('{lid}') ]]"],
            "description": f"Sphinx-Needs Link: {title}"
        }

    try:
        os.makedirs(vscode_dir, exist_ok=True)
        with open(snippet_file, 'w', encoding='utf-8') as f:
            json.dump(snippets, f, indent=2)
    except Exception: pass


def cleanup_temp_files(app, exception):
    pattern = os.path.join(app.srcdir, "bookmarks_*.html")
    for f in glob.glob(pattern):
        try: os.remove(f)
        except Exception: pass


from .roles import xlink_role
from .directives import XLinkListDirective

def setup(app):
    app.add_config_value('xlink_directory', 'xlinks', 'env')
    app.add_config_value('xlink_render_link_icon', True, 'env')
    app.add_config_value('xlink_list_render_link_icon', False, 'env')
    app.add_config_value('xlink_generate_vscode_snippets', True, 'env')
    app.add_config_value('xlink_check_links', False, 'env')
    app.add_config_value('xlink_check_timeout', 5.0, 'env')
    app.add_config_value('xlink_latex_show_urls', 'no', 'env')
    app.add_config_value('xlink_allowed_tags', {}, 'env')
    app.add_config_value('xlink_default_untagged_name', 'Untagged', 'env')
    
    # NEW configuration option for sphinx-needs integration
    app.add_config_value('xlink_needs_string_link_options', ['xlink'], 'env')
    
    app.add_node(xlink_reference, latex=(visit_xlink_reference_latex, depart_xlink_reference_latex))
    
    app.add_transform(XLinkSubstitutionTransform)
    app.connect('doctree-read', auto_label_sections)
    app.connect('missing-reference', resolve_xlink_term)
    
    app.add_role('xlink', xlink_role)
    app.add_directive('xlink-list', XLinkListDirective)
    
    app.connect('builder-inited', generate_vscode_snippets)
    app.connect('config-inited', register_needs_integration)
    app.connect('env-updated', generate_vscode_term_snippets)
    app.connect('env-updated', generate_vscode_ref_snippets)
    app.connect('env-updated', generate_vscode_needs_snippets)
    app.connect('build-finished', cleanup_temp_files)
    app.connect('doctree-resolved', downgrade_xlink_nodes)

    package_dir = os.path.abspath(os.path.dirname(__file__))
    static_dir = os.path.join(package_dir, 'static')
    app.connect('builder-inited', lambda app: app.config.html_static_path.append(static_dir))
    app.add_css_file('xlink.css')

    return {'version': '1.0.0', 'parallel_read_safe': True, 'parallel_write_safe': True}