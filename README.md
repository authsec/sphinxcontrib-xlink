# sphinxcontrib-xlink

`sphinxcontrib-xlink` is a powerful Sphinx extension for managing, filtering, and structuring external hyperlinks through centralized data files. Instead of hardcoding URLs across your documentation, define them once in `.xlink` files and reference them dynamically to build inline links, nested lists, and browser-compatible bookmark files.

It also supercharges your authoring experience with a custom VSCode snippet engine that provides instant autocomplete for external links, glossary terms, document section headers, and **Sphinx-Needs dynamic functions**.

## Features

* **Centralized Management**: Store URLs, titles, and tags in simple, structured text files (`.xlink`).
* **N-Depth Tag Hierarchies**: Build complex, multi-level grouped lists using a powerful nested tag syntax (e.g., `manager[tracking[internal]]`).
* **Rich reST Descriptions**: Inject reStructuredText-formatted descriptions into your file and tag categories for annotated link directories.
* **Surgical Description Control**: Use `!file` and `!tag` modifiers to hide descriptions for specific files, tags, or entire sub-trees based on their hierarchy path.
* **Regex & Tag Filtering**: Dynamically pull subsets of links using regular expressions on IDs, URLs, Titles, or specific tag intersections.
* **Native Sphinx-Needs Support**: Integrates directly with `sphinx-needs` dynamic functions and `needs_string_links` to make external links clickable in metadata tables.
* **Glossary & Reference Autocomplete**: Automatically generates VSCode snippets for your Sphinx glossary terms and section headers, magically resolving them inline without requiring boilerplate `replace` directives.
* **Bookmark Generation**: Generate Netscape Bookmark HTML files with native browser tag support.
* **Intelligent VSCode Snippets**: Automatically generates a `.vscode` snippet file customized to your project, carefully designed to prevent popup pollution while writing standard prose.
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

### Sample Configuration Block

You don't need anything specific in your config to get started (if you're not using tags from the beginning).

Simply create an `xlink` folder in the default `source` folder (where `conf.py` lives) and create your first `.xlink` file, e.g. `test.xlink` file.

Add the following content:

```
# xlink-section-name: Test File
# xlink-section-description: Here you can add a description, with\n\nline breaks **and** rst formatting.
test-mail :: Company Mail App :: https://companymail.example.com
```
and reference the new xlink with:

```rst
:xlink:`test-mail`
```

in your `.rst` file.

Below you can find the available configuration options, to customize `sphinxcontrib-xlink` to your needs.

```python
# Defaults to 'xlinks' relative to the 'source' directory
xlink_directory = '../xlinks'  # move out of 'source' directory

# Hierarchical Tagging & Rich Descriptions
# Defaults to {} to avoid arbitraty tags and typos, defining them, make tags explicit
# Format is:
# 'tag-name': 'Section Heading when rendering as xlink-list'
# 'tag-name': ('Section Heading in xlink-list', 'Section Description when rendering as xlink-list')
xlink_allowed_tags = {
    'engineer': ('Software Engineer', 'Resources for the **technical** staff.'),
    'manager': ('Project Management', 'Links for tracking *milestones* and budgets.'),
    'tracking': ('Tracking Tools', 'Centralized apps for project health.'),
    'internal': 'Internal Only',
    'external': 'Third-Party Services'
}

# Sphinx-Needs Integration (Optional)
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

# PDF/LaTeX Output Control
# Defaults to 'no'
xlink_latex_show_urls = 'no' # or 'inline', 'footnote'

# Visual Enhancements
# Defaults to True
xlink_render_link_icon = True
# Defaults to False
xlink_list_render_link_icon = False

```

---

## The VSCode Developer Experience

When `xlink_generate_vscode_snippets` is enabled, the extension generates a customized set of `.vscode/*.json.code-snippets` files during the build process (e.g., `make html`).

To prevent these snippets from popping up annoyingly while you type standard words, **all snippets require a deliberate intent prefix.** You can search by **ID/Slug** OR by **Human-Readable Title**.

* **`ddxl-` (Links)**: Autocomplete an external link from your `.xlink` files.
* **`ddxt-` (Terms)**: Autocomplete a glossary term.
* **`ddxr-` (Refs)**: Autocomplete an internal cross-reference to any section header.
* **`ddxn-` (Needs)**: Autocomplete a dynamic `[[ xlink('id') ]]` function for `sphinx-needs`.

> 
> **Pro-Tip**: You can also use `ddxl-list` to instantly scaffold out fully-configured `.. xlink-list::` directives with pre-filled dropdown menus for your valid tags and files!
> 
> 

---

## Data Format (`.xlink` files)

Create files with the `.xlink` extension inside your configured `xlink_directory`. Define human-readable section names and multi-line reST descriptions at the top. Use `::` as the link delimiter (spaces required).

**Example (`xlinks/example.xlink`):**

```text
# xlink-section-name: Developer Tools
# xlink-section-description: Tools required for local development.\n\nPlease install **all** of these.

example-repo :: Internal Gitlab :: https://code.example.com :: engineer, code
example-mail :: Support Mail :: https://mail.example.com :: productivity, manager

```

---

## Usage Examples

### 1. Inline Links

Type `ddxl-` in VSCode to select a link, or write it manually:

* **Default Label**: ``:xlink:`example-repo` `` renders using the title from the `.xlink` file.
* **Custom Label**: ``:xlink:`Our Code <example-repo>` `` renders as "Our Code".

### 2. Sphinx-Needs Metadata Tables

`sphinxcontrib-xlink` supports `sphinx-needs`. 

Using the `xlink` dynamic function allows you to pull URLs from your `.xlink` files directly into a needs metadata. By default, `sphinxcontrib-xlink` registers a mapping that makes these links clickable in the frontend.

The concept is shown with a Decision Record (dr) example, that needs to be set up with sphinx-need first.

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

### 3. Regex Filtering (`:url-filter-regex:`, `:title-filter-regex:`, `:id-filter-regex:`)

Pull specific links based on their properties using regular expressions. Multiple filters act as a logical `AND`.

```rst
.. xlink-list::
   :id-filter-regex: ^api-, .*?-docs$
   :url-filter-regex: github\.com
   :sort-by: id

```

### 4. Hierarchical Tag Grouping

Create deeply nested structures. Use `!tag` (Single) and `tag!!` (Cascade) to control description visibility. Prefix files with `!file` to hide file descriptions.

```rst
.. xlink-list::
   :files: !example1, example2
   :tags: !engineer[code, productivity-apps], manager!![tracking[internal]]
   :group-by: tag

```

**Modifier Logic:**

* **`!engineer`**: Hides the description for "engineer" only.
* **`manager!!`**: Shows "manager" description, but hides descriptions for all children (`tracking`, `internal`).
* **`!example1`**: Hides the file description for `example1`.

### 5. Bookmark Export

Generate a browser-compatible Netscape Bookmark `.html` file.

```rst
.. xlink-list::
   :group-by: tag, file
   :download-as-bookmarks: Project Reference Links
   :download-as-bookmarks-external-link: https://docs.example.com/bookmarks.html
   :render-list-with-bookmarks: after

```

### 6. Glossary Autocomplete & Auto-Resolution

`sphinxcontrib-xlink` completely eliminates the boilerplate of referencing Glossary Terms.

**1. Define your Glossary:**

```rst
.. glossary::

   Supervisor Mode Access Prevention (SMAP)
      A CPU security feature...

```

**2. Autocomplete in VSCode:**
Type `ddxt-` and select your term. The extension natively transforms the placeholder into a cross-reference—no `.. |replace|` directives required! (Umlauts and special characters are safely normalized).

* `|xlink-term-smap|` ➔ Renders as: [SMAP](https://www.google.com/search?q=%23)
* `|xlink-term-smap-full|` ➔ Renders as: [Supervisor Mode Access Prevention (SMAP)](https://www.google.com/search?q=%23)

### 7. Document Reference Autocomplete

The extension automatically assigns a normalized anchor label to **every section header** in your entire project.

If you have a header named `File filtering`, simply type `ddxr-` in VSCode and select it.

* `|xlink-ref-file-filtering|` ➔ Renders as: [File filtering](https://www.google.com/search?q=%23)

---

## Directive Options Reference

| Option | Value Type | Description |
| --- | --- | --- |
| `:files:` | Comma-separated | Restrict to specific (`.xlink`) files. Prefix `!` to hide descriptions.|
| `:tags:` | Hierarchy string | Filter by tags and define N-depth grouping (e.g., `a[b, !c]`).|
| `:id-filter-regex:` | Regex Patterns | Include links matching specific ID patterns.|
| `:id-starts-with:` | String | Simpler alternative to regex for matching link ID prefixes.|
| `:url-filter-regex:` | Regex Patterns | Include links matching specific URL patterns.|
| `:title-filter-regex:` | Regex Patterns | Include links matching specific Title patterns.|
| `:group-by:` | String | Grouping strategy: `file`, `tag`, `file, tag`, or `tag, file`.|
| `:sort-by:` | `id` or `title` | Sort links within their group.|
| `:order:` | `asc` or `desc` | Sort direction.|
| `:download-as-bookmarks:` | String | Generates a downloadable bookmark `.html` file.|
| `:download-as-bookmarks-external-link:` | URL | Fallback URL for the bookmark file.|
| `:render-list-with-bookmarks:` | `before` or `after` | Position of the download button relative to the list.|
| `:latex-show-urls:` | `inline`, `footnote`, `no` | LaTeX/PDF URL rendering style for this list.|
| `:render-link-icon:` | `true` or `false` | Override the global icon config for this specific list.|
| `:class:` | String | Inject custom CSS classes into the generated list container.|