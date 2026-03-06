# sphinxcontrib-xlink

`sphinxcontrib-xlink` is a powerful Sphinx extension for managing, filtering, and structuring external hyperlinks through centralized data files. Instead of hardcoding URLs across your documentation, define them once in `.xlink` files and reference them dynamically to build inline links, nested lists, and browser-compatible bookmark files.

It also supercharges your authoring experience with a custom VSCode snippet engine that provides instant autocomplete for external links, glossary terms, document section headers, tags, files, and **Sphinx-Needs dynamic functions**.

## Features

* **Centralized Management**: Store URLs, titles, and tags in simple, structured text files (`.xlink`).
* **Deep Folder Structures**: Recursively organize your `.xlink` files into nested directories. Create a hidden `.xlink` folder containing `section-name.rst` and `section-description.rst` to seamlessly generate rich metadata for an entire directory tree.
* **Native Toctree Integration**: Automatically inject your generated link hierarchies directly into the Sphinx `toctree`, allowing them to appear in your sidebar navigation.
* **Collision-Proof Namespaces**: Safely handles duplicate filenames (e.g., `examples/example1.xlink` and `other/example1.xlink`) and identically named sections by automatically tracking relative paths and generating full-path HTML anchor IDs.
* **Python Expression Engine**: Filter your link database dynamically using a secure Python evaluation engine (e.g., `:query: "code" in tags and re.search('api', url)`).
* **N-Depth Tag Hierarchies**: Build complex, multi-level grouped lists using a powerful nested tag syntax (e.g., `manager[tracking[internal]]`).
* **Rich reST Descriptions**: Inject reStructuredText-formatted descriptions into your file and tag categories for annotated link directories.
* **Surgical Description Control**: Use `!file` and `!tag` modifiers to hide descriptions for specific files, tags, or entire sub-trees based on their hierarchy path.
* **Regex & Tag Filtering**: Dynamically pull subsets of links using regular expressions on IDs, URLs, Titles, or specific tag intersections.
* **Native Sphinx-Needs Support**: Integrates directly with `sphinx-needs` dynamic functions and `needs_string_links` to make external links clickable in metadata tables.
* **Glossary & Reference Autocomplete**: Automatically generates VSCode snippets for your Sphinx glossary terms and section headers, magically resolving them inline without requiring boilerplate `replace` directives.
* **Intelligent VSCode Snippets**: Automatically generates a `.vscode` snippet file customized to your project, resolving links, terms, section headers, tags, and files inline without requiring boilerplate `replace` directives.
* **Bookmark Generation**: Generate Netscape Bookmark HTML files with native browser tag support.
* **LaTeX/PDF URL Control**: Target how URLs are rendered in PDFs (inline, footnotes, or hidden).
* **Link Checking**: Verify that external links are still alive during the Sphinx build process.

---

## Installation

Install the package via pip:

```bash
pip install sphinxcontrib-xlink

```

Add the extension to your `conf.py`:

```python
extensions = [
    'sphinxcontrib.xlink',
    'sphinx_needs', # Optional: for dynamic function support
]

```

---

## Configuration (`conf.py`)

You don't need anything specific in your config to get started. Simply create an `xlinks` folder in your documentation `source` directory and create your first `.xlink` file (e.g., `test.xlink`).

```text
# xlink-section-name: Test File
# xlink-section-description: Here you can add a description, with\n\nline breaks **and** rst formatting.
test-mail :: Company Mail App :: https://companymail.example.com
```

Reference the new link in your `.rst` file:

```rst
:xlink:`test-mail`

```

### Full Configuration Options

Below you can find the available configuration options to customize `sphinxcontrib-xlink` to your needs:

```python
# Directory containing .xlink files (Defaults to 'xlinks' relative to conf.py)
xlink_directory = '../xlinks'  

# Hierarchical Tagging & Rich Descriptions
# Defaults to {} to avoid arbitrary tags and typos. Making tags explicit is recommended.
# Format: 'tag-name': ('Section Heading', 'Section Description')
xlink_allowed_tags = {
    'engineer': ('Software Engineer', 'Resources for the **technical** staff.'),
    'manager': ('Project Management', 'Links for tracking *milestones* and budgets.'),
    'tracking': ('Tracking Tools', 'Centralized apps for project health.'),
    'internal': 'Internal Only',
    'external': 'Third-Party Services'
}

# Sphinx TOC Integration
# Define which builders automatically append lists to the Sphinx Document TOC tree.
xlink_add_to_toctree_builders = ['html', 'dirhtml', 'singlehtml', 'readthedocs']

# Sphinx-Needs Integration
# Specify which metadata fields should automatically use the xlink clickable mapping
# Defaults to ['xlink']
xlink_needs_string_link_options = ['xlink', 'documentation', 'python-docs']

# Fallback name for untagged links
# Defaults to 'Untagged'
xlink_default_untagged_name = 'Uncategorized Links'

# Developer Experience (VSCode)
# Defaults to True
xlink_generate_vscode_snippets = True

# Quality Assurance & URL Validation
# Defaults to False
xlink_check_links = False
# Defaults to 5.0 (seconds)
xlink_check_timeout = 5.0

# PDF/LaTeX Output Control ('no', 'inline', 'footnote')
xlink_latex_show_urls = 'no' 

# Visual Enhancements
# Defaults to True
xlink_render_link_icon = True
# Defaults to False
xlink_list_render_link_icon = False

```

---

## Deep Folder Structures & Toctree Integration

As your link database scales, you can organize your `.xlink` files into recursive subfolders. The extension tracks the **relative POSIX path** of each file, ensuring that identical filenames in different folders never collide.

### Example Directory Tree

```text
xlinks/
├── example1.xlink
├── examples/
│   ├── .xlink/
│   │   ├── section-name.rst         <-- E.g. "Engineering Examples"
│   │   └── section-description.rst  <-- E.g. "Links for the engineering team..."
│   ├── example1.xlink               <-- Addressed as 'examples/example1'
│   └── subxample/
│       └── example2.xlink           <-- Addressed as 'examples/subxample/example2'

```

### 1. Adding to the Toctree

If you want these folders and files to act like native chapters in your documentation (appearing in the sidebar), use the `:add-to-toctree:` flag.

```rst
.. xlink-list::
   :group-by: file
   :add-to-toctree:

```

*Note: Because `html` is in the `xlink_add_to_toctree_builders` config by default, you often don't even need to specify the flag manually for HTML builds! You can override this locally using `:no-add-to-toctree:`.*

### 2. Targeting Specific Nested Files

To target or hide specific files when dealing with complex directories, always use the **relative path**:

```rst
.. xlink-list::
   :group-by: file
   :files: example1, examples/example1, !examples/subxample/example2

```

*Prefixing a file with `!` (e.g., `!examples/subxample/example2`) will show the links inside it, but suppress the file's metadata description.*

### 3. Anchor Collision Protection

If you render multiple `xlink-list` directives on the same page grouped by the same parameters, Sphinx would normally generate colliding HTML IDs. `sphinxcontrib-xlink` automatically generates a unique `id-prefix` (e.g., `xlink-0-`, `xlink-1-`) combined with the full folder path to ensure all anchors and TOC links work flawlessly. You can also explicitly define your own:

```rst
.. xlink-list::
   :id-prefix: custom-prefix
   :group-by: file

```

---

## The VSCode Developer Experience

When `xlink_generate_vscode_snippets` is enabled, the extension generates a customized set of `.vscode/*.json.code-snippets` files during the build process (e.g., `make html`).

To prevent these snippets from popping up annoyingly while you type standard words, **all snippets require a deliberate intent prefix.**

* **`ddxl-` (Links)**: Autocomplete an external link from your `.xlink` files.
* **`ddxt-` (Terms)**: Autocomplete a glossary term.
* **`ddxr-` (Refs)**: Autocomplete an internal cross-reference to any section header.
* **`ddxn-` (Needs)**: Autocomplete a dynamic `[[ xlink('id') ]]` function for `sphinx-needs`.
* **`ddxtag-` (Tags)**: Autocomplete an allowed tag (shows description in the pop-up).
* **`ddxfile-` (Files)**: Autocomplete a valid `.xlink` relative file path (shows file metadata in the pop-up).

> **Pro-Tip**: You can also use `ddxl-list-simple` to instantly scaffold out fully-configured `.. xlink-list::` directives with pre-filled dropdown menus for your valid tags and files!

---

## Advanced Filtering: The Python Query Engine

As your link database grows, standard filter lists are no longer enough. The `.. xlink-list::` directive includes a powerful `:query:` option that evaluates a **Python expression** against every link in your database.

The engine injects the following variables into the evaluation context:

* `link_id` (str)
* `title` (str)
* `url` (str)
* `tags` (**set**) — *Exposed as a Python Set for easy intersection/subset operations!*
* `filename` (str) — *The relative path of the `.xlink` file (e.g., `examples/example1`)*
* `section_name` (str)
* `section_desc` (str)
* `re` (module) — *For regex matching*

### Exhaustive Query Examples

Here is how you can achieve complex filtering logic using natural Python syntax:

```rst
.. xlink-list::
   :query: <insert-expression-here>

```

| Goal | Python `:query:` Expression |
| --- | --- |
| **All links** | `True` |
| **Tags that start with 'role:'** | `any(t.startswith('role:') for t in tags)` |
| **Exclude the 'engineer' tag** | `"engineer" not in tags` |
| **Exclude both 'code' and 'manager'** | `not {"code", "manager"}.intersection(tags)` |
| **Tags containing specific regex** | `any(re.search('.*eat-mod.*', t) for t in tags)` |
| **Tags NOT containing specific regex** | `not any(re.search('.*:arch:.*', t) for t in tags)` |
| **Filter by file section name** | `re.search('.*Tools.*', section_name)` |
| **Desc matches 'local' OR ID matches 'iki'** | `re.search('.*local', section_desc) or re.search('.*iki.*', link_id)` |
| **Has BOTH 'code' AND 'manager' tags** | `{"code", "manager"}.issubset(tags)` |
| **Has EITHER 'code' OR 'engineer' tag** | `bool({"code", "engineer"}.intersection(tags))` |
| **Tag is 'code' AND Title ends in 'repo'** | `"code" in tags and re.search('.*repo$', title)` |
| **('code' OR 'engineer') AND URL matches** | `bool({"code", "engineer"}.intersection(tags)) and re.search('github\\.com', url)` |
| **Exclude 'code' AND (Title OR ID matches)** | `"code" not in tags and (re.search('.*repo$', title) or re.search('^api-', link_id))` |
| **Start with 'role:' from specific files** | `any(t.startswith('role:') for t in tags) and filename in ['example1', 'examples/example2']` |
| **'code' AND specific Section Names** | `"code" in tags and (re.search('.*-model', section_name) or re.search('To.*', section_name))` |

*(Note: Sorting should be handled via the `:sort-by:` and `:order:` directive options rather than inside the Python query.)*

---

## Usage Examples

### 1. Inline Links

Type `ddxl-` in VSCode to select a link, or write it manually:

* **Default Label**: `:xlink:`example-repo` ` renders using the title from the `.xlink` file.
* **Custom Label**: `:xlink:`Our Code <example-repo>` ` renders as "Our Code".

### 2. Sphinx-Needs Metadata Tables

Using the `xlink` dynamic function allows you to pull URLs from your `.xlink` files directly into a needs metadata table. By default, `sphinxcontrib-xlink` registers a mapping that makes these links clickable in the frontend.

**Single Link:**

```rst
.. dr:: My decision
   :id: DR-0001
   :xlink: [[ xlink('example-repo') ]]

```

**Multiple Links:**
You can pass multiple IDs as a comma-separated string.

```rst
.. dr:: Complex decision
   :id: DR-0002
   :xlink: [[ xlink('example-repo, example-mail') ]]

```

### 3. Hierarchical Tag Grouping

Create deeply nested structures. Use `!tag` (Single) and `tag!!` (Cascade) to control description visibility. Prefix files with `!file` to hide file descriptions.

```rst
.. xlink-list::
   :files: !example1, examples/example2
   :tags: !engineer[code, productivity-apps], manager!![tracking[internal]]
   :group-by: tag

```

**Modifier Logic:**

* **`!engineer`**: Hides the description for "engineer" only.
* **`manager!!`**: Shows "manager" description, but hides descriptions for all children (`tracking`, `internal`).
* **`!example1`**: Hides the file description for `example1`.

### 4. Bookmark Export

Generate a browser-compatible Netscape Bookmark `.html` file.

```rst
.. xlink-list::
   :group-by: tag, file
   :download-as-bookmarks: Project Reference Links
   :download-as-bookmarks-external-link: https://docs.example.com/bookmarks.html
   :render-list-with-bookmarks: after

```

### 5. Glossary Autocomplete & Auto-Resolution

`sphinxcontrib-xlink` completely eliminates the boilerplate of referencing Glossary Terms. Type `ddxt-` in VSCode and select your term. The extension natively transforms the placeholder into a cross-reference—no `.. |replace|` directives required!

* `|xlink-term-smap|` ➔ Renders as: [SMAP](https://www.google.com/search?q=%23)
* `|xlink-term-smap-full|` ➔ Renders as: [Supervisor Mode Access Prevention (SMAP)](https://www.google.com/search?q=%23)

### 6. Document Reference Autocomplete

The extension automatically assigns a normalized anchor label to **every section header** in your entire project. Type `ddxr-` in VSCode and select it.

* `|xlink-ref-file-filtering|` ➔ Renders as: [File filtering](https://www.google.com/search?q=%23)

---

## Directive Options Reference

| Option | Value Type | Description |
| --- | --- | --- |
| `:query:` | **Python Expr.** | Filter links using a Python expression (`tags`, `link_id`, `url`, `filename`, etc.). |
| `:files:` | Comma-separated | Restrict to specific relative paths (e.g. `examples/example1`). Prefix `!` to hide desc. |
| `:tags:` | Hierarchy string | Filter by tags and define N-depth grouping (e.g., `a[b, !c]`). |
| `:id-filter-regex:` | Regex Patterns | *(Legacy)* Include links matching specific ID patterns. |
| `:id-starts-with:` | String | *(Legacy)* Simpler alternative to regex for matching link ID prefixes. |
| `:url-filter-regex:` | Regex Patterns | *(Legacy)* Include links matching specific URL patterns. |
| `:title-filter-regex:` | Regex Patterns | *(Legacy)* Include links matching specific Title patterns. |
| `:group-by:` | String | Grouping strategy: `file`, `tag`, `file, tag`, or `tag, file`. |
| `:sort-by:` | `id` or `title` | Sort links within their group. |
| `:order:` | `asc` or `desc` | Sort direction. |
| `:download-as-bookmarks:` | String | Generates a downloadable bookmark `.html` file. |
| `:download-as-bookmarks-external-link:` | URL | Fallback URL for the bookmark file. |
| `:render-list-with-bookmarks:` | `before` / `after` | Position of the download button relative to the list. |
| `:latex-show-urls:` | `inline`, `footnote`, `no` | LaTeX/PDF URL rendering style for this list. |
| `:render-link-icon:` | `true` or `false` | Override the global icon config for this specific list. |
| `:class:` | String | Inject custom CSS classes into the generated list container. |
| `:add-to-toctree:` | Flag | Append list sections to the Sphinx document TOC directly. |
| `:no-add-to-toctree:` | Flag | Prevents TOC integration (overrides `conf.py` default). |
| `:id-prefix:` | String | Custom prefix for HTML anchor IDs. Defaults to an auto-incrementing ID. |