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
    default_priority = 210

    def apply(self):
        for node in list(self.document.findall(nodes.substitution_reference)):
            refname = node['refname']
            
            if refname.startswith('xlink-term-'):
                slug = refname[11:] 
                is_full = False
                if slug.endswith('-full'):
                    slug = slug[:-5]
                    is_full = True

                xref = pending_xref(
                    '', refdomain='std', reftype='term', reftarget=slug,
                    refexplicit=False, refwarn=True, modname=None, classname=None,
                    xlink_is_full=is_full
                )
                xref['refdoc'] = self.document.settings.env.docname
                xref += nodes.inline('', f'|{refname}|', classes=['xlink-term-placeholder'])
                node.replace_self(xref)

            elif refname.startswith('xlink-ref-'):
                slug = refname[10:]
                xref = pending_xref(
                    '', refdomain='std', reftype='ref', reftarget=slug,
                    refexplicit=False, refwarn=True, modname=None, classname=None
                )
                xref['refdoc'] = self.document.settings.env.docname
                xref += nodes.inline('', f'|{refname}|', classes=['xlink-ref-placeholder'])
                node.replace_self(xref)

def resolve_xlink_term(app, env, node, contnode):
    if node.get('reftype') == 'term' and node.get('xlink_is_full') is not None:
        slug = node['reftarget']
        is_full = node['xlink_is_full']
        std_domain = env.domains.get('std')
        if not std_domain: return None
        
        for obj in std_domain.get_objects():
            if obj[2] == 'term':
                term = obj[1]
                match = re.search(r'^(.*?)\s*\((.*?)\)$', term)
                short_text = match.group(2).strip() if match else term.strip()
                normalized = unicodedata.normalize('NFD', short_text).encode('ascii', 'ignore').decode('utf-8')
                term_slug = re.sub(r'[^a-z0-9]+', '-', normalized.lower()).strip('-')
                    
                if term_slug == slug:
                    display_text = term if is_full else short_text
                    return make_refnode(
                        app.builder, node['refdoc'], obj[3], obj[4],
                        nodes.inline('', display_text, classes=['xref', 'std', 'std-term']), term
                    )
    return None

def auto_label_sections(app, doctree):
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
    env = app.env
    config = env.config
    source_dir = os.path.normpath(os.path.join(env.srcdir, config.xlink_directory))
    if not os.path.isdir(source_dir): return None, None

    for root, dirs, files in os.walk(source_dir):
        if '.xlink' in dirs: dirs.remove('.xlink')
        for filename in files:
            if filename.endswith('.xlink'):
                with open(os.path.join(root, filename), "r", encoding="utf-8-sig") as f:
                    for line in f:
                        clean = line.strip()
                        if not clean or clean.startswith('#'): continue
                        if " :: " in clean:
                            parts = [p.strip() for p in clean.split(" :: ", 3)]
                            if len(parts) >= 3 and parts[0] == link_id:
                                return parts[1], parts[2]
    return None, None

def xlink_func(app, need, needs, link_ids):
    if isinstance(link_ids, str): link_ids = [i.strip() for i in link_ids.split(',')]
    results = []
    for lid in link_ids:
        title, url = _get_xlink_data(app, lid)
        if title and url: results.append(f"{title} <{url}>")
    return "; ".join(results) if results else ""

def xlink_url_func(app, need, needs, link_ids):
    if isinstance(link_ids, str): link_ids = [i.strip() for i in link_ids.split(',')]
    results = []
    for lid in link_ids:
        _, url = _get_xlink_data(app, lid)
        if url: results.append(url)
    return "; ".join(results)

def xlink_title_func(app, need, needs, link_ids):
    if isinstance(link_ids, str): link_ids = [i.strip() for i in link_ids.split(',')]
    results = []
    for lid in link_ids:
        title, _ = _get_xlink_data(app, lid)
        if title: results.append(title)
    return "; ".join(results)

def register_needs_integration(app, config):
    if 'sphinx_needs' not in config.extensions and 'sphinxcontrib.needs' not in config.extensions:
        return
    if not hasattr(config, 'needs_functions'): config.needs_functions = []
    
    mapping = [(xlink_func, 'xlink'), (xlink_url_func, 'xlink_url'), (xlink_title_func, 'xlink_title')]
    existing = [getattr(f, '__name__', str(f)) for f in config.needs_functions]
    
    for func, name in mapping:
        if name not in existing:
            func.__name__ = name
            config.needs_functions.append(func)

    target_options = getattr(config, 'xlink_needs_string_link_options', ['xlink'])
    xlink_mapping = {'regex': r'^(?P<name>.*?) <(?P<url>.*?)>$', 'link_url': '{{url}}', 
                     'link_name': '{{name}}', 'options': target_options}

    if not hasattr(config, 'needs_string_links'): config.needs_string_links = {}
    if 'xlink' not in config.needs_string_links: config.needs_string_links['xlink'] = xlink_mapping

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
    
    for root, dirs, files in os.walk(xlink_dir):
        if '.xlink' in dirs: dirs.remove('.xlink')
        for filename in files:
            if filename.endswith('.xlink'):
                filepath = os.path.join(root, filename)
                rel_path = os.path.relpath(filepath, xlink_dir)
                rel_file_base = os.path.splitext(rel_path)[0].replace(os.sep, '/')
                file_list.append(rel_file_base)
                
                with open(filepath, "r", encoding="utf-8-sig") as f:
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
    if not app.config.xlink_generate_vscode_snippets: return
    
    vscode_dir = os.path.join(os.path.dirname(app.srcdir), '.vscode')
    snippet_file = os.path.join(vscode_dir, 'xlink-needs.json.code-snippets')
    
    id_list = []
    source_dir = os.path.normpath(os.path.join(app.srcdir, app.config.xlink_directory))
    if os.path.isdir(source_dir):
        for root, dirs, files in os.walk(source_dir):
            if '.xlink' in dirs: dirs.remove('.xlink')
            for filename in files:
                if filename.endswith('.xlink'):
                    with open(os.path.join(root, filename), "r", encoding="utf-8-sig") as f:
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

def generate_vscode_tag_snippets(app, env):
    config = app.config
    if not config.xlink_generate_vscode_snippets: return
    
    vscode_dir = os.path.join(os.path.dirname(app.srcdir), '.vscode')
    snippet_file = os.path.join(vscode_dir, 'xlink-tags.json.code-snippets')
    
    snippets = {}
    for tag_slug, tag_data in config.xlink_allowed_tags.items():
        title = tag_slug
        desc = ""
        if isinstance(tag_data, (list, tuple)):
            title = str(tag_data[0])
            desc = str(tag_data[1]) if len(tag_data) > 1 else ""
        else:
            title = str(tag_data)
            
        display_desc = f"{title}\n\n{desc}" if desc else title
        
        snippets[f"xlink-tag-{tag_slug}"] = {
            "prefix": [f"ddxtag-{title}", f"ddxtag-{tag_slug}"],
            "body": [tag_slug],
            "description": f"Tag: {display_desc}"
        }

    try:
        os.makedirs(vscode_dir, exist_ok=True)
        with open(snippet_file, 'w', encoding='utf-8') as f:
            json.dump(snippets, f, indent=2)
    except Exception: pass

def generate_vscode_file_snippets(app, env):
    config = app.config
    if not config.xlink_generate_vscode_snippets: return
    
    source_dir = os.path.normpath(os.path.join(app.srcdir, config.xlink_directory))
    if not os.path.isdir(source_dir): return
    
    vscode_dir = os.path.join(os.path.dirname(app.srcdir), '.vscode')
    snippet_file = os.path.join(vscode_dir, 'xlink-files.json.code-snippets')
    
    snippets = {}
    for root, dirs, files in os.walk(source_dir):
        if '.xlink' in dirs: dirs.remove('.xlink')
        for filename in files:
            if filename.endswith('.xlink'):
                filepath = os.path.join(root, filename)
                rel_path = os.path.relpath(filepath, source_dir)
                rel_file_base = os.path.splitext(rel_path)[0].replace(os.sep, '/')
                
                section_name = filename[:-6]
                section_desc = ""
                
                with open(filepath, "r", encoding="utf-8-sig") as f:
                    for _ in range(10):
                        line = f.readline().strip()
                        if line.startswith("# xlink-section-name:"):
                            section_name = line.replace("# xlink-section-name:", "").strip()
                        elif line.startswith("# xlink-section-description:"):
                            section_desc += line.replace("# xlink-section-description:", "").strip() + " "
                
                display_desc = f"File: {rel_file_base}.xlink\nName: {section_name}"
                if section_desc: display_desc += f"\n\n{section_desc}"
                
                # Create a safe JSON key by replacing forward slashes with hyphens
                safe_key = rel_file_base.replace('/', '-')
                
                snippets[f"xlink-file-{safe_key}"] = {
                    "prefix": [f"ddxfile-{section_name}", f"ddxfile-{rel_file_base}"],
                    "body": [rel_file_base],
                    "description": display_desc
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
    app.add_config_value('xlink_needs_string_link_options', ['xlink'], 'env')
    
    app.add_config_value('xlink_add_to_toctree_builders', ['html', 'dirhtml', 'singlehtml', 'readthedocs'], 'env')
    
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
    app.connect('env-updated', generate_vscode_tag_snippets)
    app.connect('env-updated', generate_vscode_file_snippets)
    
    app.connect('build-finished', cleanup_temp_files)
    app.connect('doctree-resolved', downgrade_xlink_nodes)

    package_dir = os.path.abspath(os.path.dirname(__file__))
    static_dir = os.path.join(package_dir, 'static')
    app.connect('builder-inited', lambda app: app.config.html_static_path.append(static_dir))
    app.add_css_file('xlink.css')

    return {'version': '1.1.0', 'parallel_read_safe': True, 'parallel_write_safe': True}