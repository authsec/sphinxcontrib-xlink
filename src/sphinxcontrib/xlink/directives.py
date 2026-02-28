import os
import re
import datetime
import urllib.request
import urllib.error
from docutils import nodes
from docutils.statemachine import ViewList
from docutils.parsers.rst import Directive, directives
from sphinx.util import logging
from sphinx.addnodes import download_reference
from . import xlink_reference

logger = logging.getLogger(__name__)

_WARNED_ENTRIES = set()

def optional_render_list(argument):
    if not argument:
        return 'before'
    choice = argument.strip().lower()
    if choice in ('before', 'after'):
        return choice
    raise ValueError('Must be "before" or "after"')

class XLinkListDirective(Directive):
    has_content = False
    option_spec = {
        'id-filter-regex': directives.unchanged,
        'id-starts-with': directives.unchanged,
        'url-filter-regex': directives.unchanged,
        'title-filter-regex': directives.unchanged,
        'files': directives.unchanged,
        'tags': directives.unchanged,
        'sort-by': lambda x: directives.choice(x, ('id', 'title')),
        'order': lambda x: directives.choice(x, ('asc', 'desc')),
        'group-by': directives.unchanged,
        'group-by-file': directives.flag,
        'class': directives.class_option,
        'render-link-icon': lambda x: directives.choice(x, ('true', 'false')),
        'download-as-bookmarks': directives.unchanged,
        'download-as-bookmarks-external-link': directives.unchanged,
        'render-list-with-bookmarks': optional_render_list,
        'latex-show-urls': lambda x: directives.choice(x, ('inline', 'footnote', 'no')),
    }

    def _check_links(self, links, timeout):
        for lid, title, url, source_file in links:
            try:
                req = urllib.request.Request(url, method='HEAD', headers={'User-Agent': 'Sphinx/XLinkChecker'})
                with urllib.request.urlopen(req, timeout=timeout) as response:
                    if response.status >= 400:
                        logger.warning(f"xlink: Broken link! ID: '{lid}' in {source_file} (Status: {response.status})")
            except Exception as e:
                logger.warning(f"xlink: Check Error! ID: '{lid}' in {source_file} ({str(e)})")

    def _parse_rst(self, text):
        rst = ViewList()
        text = text.replace('\\n', '\n')
        for i, line in enumerate(text.split('\n')):
            rst.append(line, '<xlink-description>', i)
        
        node = nodes.container()
        self.state.nested_parse(rst, 0, node)
        return node.children
        
    def _parse_nested_tags(self, tags_string):
        root = {}
        stack = [(root, False)] 
        current_dict = root
        current_cascade = False
        buffer = ""
        
        def process_buffer(buf, c_dict, c_cascade):
            raw_tag = buf.strip()
            if not raw_tag: return None, False
            
            hide_self = False
            cascade_children = False
            
            if raw_tag.startswith('!!'):
                hide_self = True
                cascade_children = True
                raw_tag = raw_tag[2:]
            elif raw_tag.startswith('!'):
                hide_self = True
                raw_tag = raw_tag[1:]
                
            if raw_tag.endswith('!!'):
                cascade_children = True
                raw_tag = raw_tag[:-2]
            elif raw_tag.endswith('!'):
                hide_self = True
                raw_tag = raw_tag[:-1]
                
            clean_tag = raw_tag.strip()
            
            if c_cascade:
                hide_self = True
                cascade_children = True
                
            c_dict[clean_tag] = {'children': {}, 'hide': hide_self, 'cascade': cascade_children}
            return clean_tag, cascade_children

        for char in tags_string:
            if char == '[':
                tag_name, cascade = process_buffer(buffer, current_dict, current_cascade)
                buffer = ""
                if tag_name:
                    stack.append((current_dict[tag_name]['children'], cascade))
                    current_dict = current_dict[tag_name]['children']
                    current_cascade = cascade
            elif char == ']':
                process_buffer(buffer, current_dict, current_cascade)
                buffer = ""
                if len(stack) > 1:
                    stack.pop()
                    current_dict, current_cascade = stack[-1]
            elif char == ',':
                process_buffer(buffer, current_dict, current_cascade)
                buffer = ""
            else:
                buffer += char
                
        process_buffer(buffer, current_dict, current_cascade)
        return root

    def _get_all_keys(self, tree):
        keys = set()
        for k, v in tree.items():
            keys.add(k)
            keys.update(self._get_all_keys(v['children']))
        return keys
        
    def _is_path_hidden(self, current_path, hidden_paths):
        for hp in hidden_paths:
            if len(current_path) >= len(hp):
                if current_path[-len(hp):] == hp:
                    return True
        return False

    def _build_bookmarks_html(self, tree, order, section_descriptions, hidden_paths, path_prefix=tuple(), indent_level=1):
        lines = []
        indent = "    " * indent_level
        now = int(datetime.datetime.now().timestamp())
        
        if '__links__' in tree:
            links = tree['__links__']
            links.sort(key=lambda x: x[1].lower(), reverse=(order == 'desc'))
            
            for lid, title, url, raw_tags in links:
                # Use the raw tags directly from the .xlink file
                tags_attr = ",".join(raw_tags) if raw_tags else ""
                lines.append(f'{indent}<DT><A HREF="{url}" ADD_DATE="{now}" TAGS="{tags_attr}">{title}</A>')

        keys = sorted([k for k in tree.keys() if k != '__links__'], reverse=(order == 'desc'))
        for k in keys:
            lines.append(f'{indent}<DT><H3 ADD_DATE="{now}" LAST_MODIFIED="{now}">{k}</H3>')
            
            current_path = path_prefix + (k,)
            desc = section_descriptions.get(k)
            if desc and not self._is_path_hidden(current_path, hidden_paths):
                clean_desc = desc.replace('\\n', ' ').strip()
                lines.append(f'{indent}<DD>{clean_desc}')
                
            lines.append(f'{indent}<DL><p>')
            lines.extend(self._build_bookmarks_html(tree[k], order, section_descriptions, hidden_paths, current_path, indent_level + 1))
            lines.append(f'{indent}</DL><p>')
                
        return lines

    def _build_sphinx_nodes(self, tree, custom_classes, show_icon, env, target_setting, sort_by, order, section_descriptions, hidden_paths, path_prefix=tuple()):
        nodes_list = []
        
        if '__links__' in tree:
            links = tree['__links__']
            links.sort(key=lambda x: x[0 if sort_by == 'id' else 1].lower(), reverse=(order == 'desc'))
            list_node = nodes.bullet_list()
            
            for lid, title, url, raw_tags in links:
                item = nodes.list_item()
                p = nodes.paragraph()
                if show_icon and env.app.builder.name == 'html':
                    p += nodes.inline(classes=['xlink-icon', 'fa-solid', 'fa-arrow-up-right-from-square'])
                    p += nodes.Text(' ')
                
                ref_node = xlink_reference('', title, refuri=url, classes=['xlink-link'], target='_blank')
                ref_node['xlink_latex_style'] = target_setting
                p += ref_node
                
                item += p
                list_node += item
                
            nodes_list.append(list_node)

        keys = sorted([k for k in tree.keys() if k != '__links__'], reverse=(order == 'desc'))
        for k in keys:
            section = nodes.section(ids=[nodes.make_id(k)])
            section['classes'].extend(custom_classes)
            section += nodes.title('', k)
            
            current_path = path_prefix + (k,)
            desc = section_descriptions.get(k)
            
            if desc and not self._is_path_hidden(current_path, hidden_paths):
                desc_container = nodes.container(classes=['xlink-tag-description'])
                desc_container.extend(self._parse_rst(desc))
                section += desc_container
            
            section.extend(self._build_sphinx_nodes(tree[k], custom_classes, show_icon, env, target_setting, sort_by, order, section_descriptions, hidden_paths, current_path))
            nodes_list.append(section)
            
        return nodes_list

    def run(self):
        env = self.state.document.settings.env
        config = env.config
        
        global_latex_style = getattr(config, 'xlink_latex_show_urls', 'no')
        target_setting = self.options.get('latex-show-urls', global_latex_style)
        
        source_directory = os.path.normpath(os.path.join(env.srcdir, config.xlink_directory))
        
        if not os.path.isdir(source_directory):
            return [self.state.document.reporter.warning(f"xlink directory not found: {source_directory}")]

        def resolve_tag(t):
            if t is None:
                return config.xlink_default_untagged_name, ""
            if config.xlink_allowed_tags and t in config.xlink_allowed_tags:
                val = config.xlink_allowed_tags[t]
                if isinstance(val, (list, tuple)):
                    return str(val[0]), str(val[1]) if len(val) > 1 else ""
                return str(val), ""
            return str(t), ""

        # Parse ID filters
        id_regexes = []
        id_regex_input = self.options.get('id-filter-regex') or self.options.get('id-starts-with')
        if id_regex_input:
            for p in id_regex_input.split(','):
                try:
                    id_regexes.append(re.compile(p.strip()))
                except re.error as e:
                    logger.warning(f"xlink: Invalid ID regex '{p.strip()}': {e}", location=(env.docname, self.lineno))

        # Parse URL filters
        url_regexes = []
        url_regex_input = self.options.get('url-filter-regex')
        if url_regex_input:
            for p in url_regex_input.split(','):
                try:
                    url_regexes.append(re.compile(p.strip()))
                except re.error as e:
                    logger.warning(f"xlink: Invalid URL regex '{p.strip()}': {e}", location=(env.docname, self.lineno))

        # Parse Title filters
        title_regexes = []
        title_regex_input = self.options.get('title-filter-regex')
        if title_regex_input:
            for p in title_regex_input.split(','):
                try:
                    title_regexes.append(re.compile(p.strip()))
                except re.error as e:
                    logger.warning(f"xlink: Invalid Title regex '{p.strip()}': {e}", location=(env.docname, self.lineno))

        # Parse allowed files and visibility modifiers
        allowed_files = None
        hidden_file_bases = set()
        if self.options.get('files'):
            allowed_files = []
            for f in self.options.get('files').split(','):
                f = f.strip()
                hide_file = False
                
                # Check for prefix bang! Only
                if f.startswith('!'):
                    f = f[1:].strip()
                    hide_file = True
                
                allowed_files.append(f)
                if hide_file:
                    hidden_file_bases.add(f)
        
        parsed_tags_filter = None
        all_allowed_tags = set()
        hidden_paths = set()
        tags_option = self.options.get('tags')
        
        if tags_option:
            parsed_tags_filter = self._parse_nested_tags(tags_option)
            all_allowed_tags = self._get_all_keys(parsed_tags_filter)
            
            def _populate_hidden_paths(node_dict, path_prefix=tuple()):
                for t_key, t_data in node_dict.items():
                    resolved_name, _ = resolve_tag(t_key)
                    current_path = path_prefix + (resolved_name,)
                    
                    if t_data['hide']:
                        hidden_paths.add(current_path)
                    _populate_hidden_paths(t_data['children'], current_path)
            
            _populate_hidden_paths(parsed_tags_filter)

        custom_classes = self.options.get('class', [])
        show_icon = self.options.get('render-link-icon', str(config.xlink_list_render_link_icon)).lower() == 'true'
        sort_by = self.options.get('sort-by', 'title')
        order = self.options.get('order', 'asc')
        
        group_by_raw = self.options.get('group-by', 'file' if 'group-by-file' in self.options else '')
        group_by_opts = [g.strip().lower() for g in group_by_raw.split(',')] if group_by_raw else []

        is_bookmark_mode = 'download-as-bookmarks' in self.options
        should_render_list = not is_bookmark_mode or 'render-list-with-bookmarks' in self.options

        tree_data = {}
        section_descriptions = {}  
        links_for_checking = []
        
        for filename in sorted(os.listdir(source_directory)):
            if filename.endswith('.xlink'):
                file_base = filename[:-6]
                if allowed_files is not None and file_base not in allowed_files:
                    continue

                filepath = os.path.join(source_directory, filename)
                env.note_dependency(filepath)
                file_section_name, _, file_desc = self._get_section_info(filepath)
                
                if file_desc:
                    section_descriptions[file_section_name] = file_desc
                if file_base in hidden_file_bases:
                    hidden_paths.add((file_section_name,))
                
                with open(filepath, "r", encoding="utf-8-sig") as f:
                    for line_num, line in enumerate(f, 1):
                        clean_line = line.strip()
                        if not clean_line or clean_line.startswith('#'):
                            continue

                        if " :: " in clean_line:
                            parts = [p.strip() for p in clean_line.split(" :: ", 3)]
                            if len(parts) in (3, 4):
                                lid, title, url = parts[:3]
                                raw_tags = [t.strip() for t in parts[3].split(',')] if len(parts) == 4 else []
                                
                                valid_tags = []
                                for t in raw_tags:
                                    if not t: continue
                                    if config.xlink_allowed_tags and t not in config.xlink_allowed_tags:
                                        warning_key = f"{filename}:{line_num}:tag:{t}"
                                        if warning_key not in _WARNED_ENTRIES:
                                            logger.warning(f"xlink: Unknown tag '{t}' in {filename}:{line_num}. Define the tag in conf.py:xlink_allowed_tags", location=(env.docname, self.lineno))
                                            _WARNED_ENTRIES.add(warning_key)
                                    else:
                                        valid_tags.append(t)
                                
                                if parsed_tags_filter is not None:
                                    valid_tags = [t for t in valid_tags if t in all_allowed_tags]
                                    if not valid_tags:
                                        continue
                                
                                # Apply Logical AND for all regex filters
                                id_match = not id_regexes or any(r.search(lid) for r in id_regexes)
                                url_match = not url_regexes or any(r.search(url) for r in url_regexes)
                                title_match = not title_regexes or any(r.search(title) for r in title_regexes)
                                
                                if id_match and url_match and title_match:
                                    links_for_checking.append((lid, title, url, filename))
                                    
                                    paths = []
                                    def _find_paths(node_dict, link_tags):
                                        hierarchical_paths = []
                                        for t_key, t_data in node_dict.items():
                                            if t_key in link_tags:
                                                p_name, p_desc = resolve_tag(t_key)
                                                if p_desc: section_descriptions[p_name] = p_desc
                                                
                                                if t_data['children']:
                                                    child_paths = _find_paths(t_data['children'], link_tags)
                                                    if child_paths:
                                                        for cp in child_paths:
                                                            hierarchical_paths.append((p_name,) + cp)
                                                    else:
                                                        hierarchical_paths.append((p_name,))
                                                else:
                                                    hierarchical_paths.append((p_name,))
                                        return hierarchical_paths

                                    def get_tag_paths(tags):
                                        if parsed_tags_filter is None:
                                            if not tags: 
                                                name, desc = resolve_tag(None)
                                                if desc: section_descriptions[name] = desc
                                                return [(name,)]
                                            
                                            res = []
                                            for t in tags:
                                                name, desc = resolve_tag(t)
                                                if desc: section_descriptions[name] = desc
                                                res.append((name,))
                                            return res
                                        
                                        return _find_paths(parsed_tags_filter, tags)

                                    if not group_by_opts:
                                        paths.append(tuple()) 
                                    elif group_by_opts == ['file']:
                                        paths.append((file_section_name,))
                                    elif group_by_opts == ['tag']:
                                        paths.extend(get_tag_paths(valid_tags))
                                    elif group_by_opts == ['file', 'tag']:
                                        for tp in get_tag_paths(valid_tags):
                                            paths.append((file_section_name,) + tp)
                                    elif group_by_opts == ['tag', 'file']:
                                        for tp in get_tag_paths(valid_tags):
                                            paths.append(tp + (file_section_name,))
                                    else:
                                        paths.append(tuple())

                                    for p in paths:
                                        current = tree_data
                                        for level in p:
                                            if level not in current:
                                                current[level] = {}
                                            current = current[level]
                                        if '__links__' not in current:
                                            current['__links__'] = []
                                        # Append the actual valid_tags to the tuple here!
                                        current['__links__'].append((lid, title, url, valid_tags))
                            else:
                                warning_key = f"{filename}:{line_num}"
                                if warning_key not in _WARNED_ENTRIES:
                                    logger.warning(f"xlink: Malformed entry in {filename}:{line_num} (Expected 3 or 4 parts). Check spaces around '::'. Line: '{clean_line}'", location=(env.docname, self.lineno))
                                    _WARNED_ENTRIES.add(warning_key)
                        else:
                            warning_key = f"{filename}:{line_num}"
                            if warning_key not in _WARNED_ENTRIES:
                                logger.warning(f"xlink: Malformed entry in {filename}:{line_num} (Missing ' :: ' delimiter). Line: '{clean_line}'", location=(env.docname, self.lineno))
                                _WARNED_ENTRIES.add(warning_key)

        if config.xlink_check_links:
            self._check_links(links_for_checking, config.xlink_check_timeout)

        bookmark_node = None
        if is_bookmark_mode:
            val = self.options.get('download-as-bookmarks')
            bookmark_folder = val if val else f"{getattr(config, 'project', 'Documentation')} Links"
            
            is_html_builder = getattr(env.app.builder, 'format', '') == 'html' or env.app.builder.name in ('html', 'dirhtml', 'singlehtml', 'readthedocs')
            
            if is_html_builder:
                bookmark_filename = f"bookmarks_{nodes.make_id(bookmark_folder)}.html"
                bookmark_path = os.path.join(env.srcdir, bookmark_filename)
                
                with open(bookmark_path, "w", encoding="utf-8") as bf:
                    bf.write('<!DOCTYPE NETSCAPE-Bookmark-file-1>\n')
                    bf.write('<META HTTP-EQUIV="Content-Type" CONTENT="text/html; charset=UTF-8">\n')
                    bf.write('<TITLE>Bookmarks</TITLE><H1>Bookmarks</H1>\n')
                    bf.write('<DL><p>\n')
                    
                    now = int(datetime.datetime.now().timestamp())
                    bf.write(f'    <DT><H3 ADD_DATE="{now}" LAST_MODIFIED="{now}">{bookmark_folder}</H3>\n')
                    bf.write('    <DL><p>\n')
                    
                    for line in self._build_bookmarks_html(tree_data, order, section_descriptions, hidden_paths, indent_level=2):
                        bf.write(line + '\n')
                        
                    bf.write('    </DL><p>\n')
                    bf.write('</DL><p>\n')
                
                bookmark_node = download_reference(bookmark_filename, '', reftarget='/' + bookmark_filename, classes=['xlink-bookmark-button'])
                bookmark_node += nodes.Text(f"Download {bookmark_folder} (.html)")
            else:
                ext_url = self.options.get('download-as-bookmarks-external-link')
                if ext_url:
                    bookmark_node = nodes.reference('', '', internal=False, refuri=ext_url, classes=['xlink-bookmark-button', 'external'])
                    bookmark_node += nodes.Text(f"Download {bookmark_folder} (.html)")

        list_container = None
        if should_render_list:
            list_container = nodes.container(classes=['xlink-list-container'] + custom_classes)
            if '__links__' in tree_data and len(tree_data) == 1:
                clean_tree = {'All Links': tree_data} if 'group-by' in self.options else tree_data
                list_container.extend(self._build_sphinx_nodes(clean_tree, custom_classes, show_icon, env, target_setting, sort_by, order, section_descriptions, hidden_paths))
            else:
                list_container.extend(self._build_sphinx_nodes(tree_data, custom_classes, show_icon, env, target_setting, sort_by, order, section_descriptions, hidden_paths))

        result_nodes = []
        button_pos = self.options.get('render-list-with-bookmarks', 'before')

        if button_pos == 'before':
            if bookmark_node: result_nodes.append(bookmark_node)
            if list_container: result_nodes.append(list_container)
        else:
            if list_container: result_nodes.append(list_container)
            if bookmark_node: result_nodes.append(bookmark_node)

        return result_nodes

    def _get_section_info(self, filepath):
        name = os.path.splitext(os.path.basename(filepath))[0]
        has_name = False
        desc_lines = []
        try:
            with open(filepath, "r", encoding="utf-8-sig") as f:
                for _ in range(20): 
                    line = f.readline()
                    if not line or (not line.startswith("#") and " :: " in line):
                        break
                    if line.startswith("# xlink-section-name:"):
                        name = line.replace("# xlink-section-name:", "").strip()
                        has_name = True
                    elif line.startswith("# xlink-section-description:"):
                        desc_lines.append(line.replace("# xlink-section-description:", "").strip())
        except Exception: pass
        
        description = "\n".join(desc_lines)
        return name, has_name, description