# sphinxcontrib-xlink

`sphinxcontrib-xlink` is a powerful Sphinx extension for managing, filtering, and structuring external hyperlinks through centralized data files. Instead of hardcoding URLs across your documentation, define them once in `.xlink` files and reference them dynamically to build inline links, nested lists, and browser-compatible bookmark files.

It also supercharges your authoring experience with a custom VSCode snippet engine that provides instant autocomplete for external links, glossary terms, document section headers, tags, files, and **Sphinx-Needs dynamic functions**.

---

## 🔍 Interactive Bookmark Search (HTML only)

> **⚠️ Important**: The search feature only works with **HTML output** (`html`, `dirhtml`, `singlehtml`, `readthedocs` builders). It renders a client-side JavaScript widget that is not available in LaTeX/PDF or other non-HTML builders.

The `.. xlink-search::` directive embeds a fully interactive, real-time search interface directly into your documentation. Readers can instantly search, filter, and navigate your entire link database without leaving the page.

### Key Capabilities

* **Instant fuzzy search** across link titles, IDs, tags, and URLs
* **Smart tag filtering** with `tag:` prefix — matches against tag slugs, display names, *and* descriptions
* **Tag exclusion** with `-tag:` or `!tag:` prefix
* **URL filtering** with `inurl:` and exclusion with `-inurl:` or `!inurl:`
* **Autocomplete dropdown** for tag names as you type `tag:`
* **Match context highlights** showing *why* a tag matched (displays the tag's display name and description with the matching term highlighted)
* **Full keyboard navigation** — Arrow keys, Tab, Enter to open links, Shift+Enter to copy `:xlink:` role to clipboard
* **Global keyboard shortcut** — `⌘+⇧+K` (Mac) / `Ctrl+Shift+K` (Windows/Linux) to focus or open search
* **Configurable results per page** with persistent localStorage preference
* **Overlay mode** — renders as a modal dialog triggered by keyboard shortcut
* **Custom styling** via CSS classes

### Basic Usage

```rst
.. xlink-search::
```

This renders a full-width search bar with a paginated results table containing all links from your `.xlink` files.

### Configuration Examples

**Custom title and page sizes:**

```rst
.. xlink-search::
   :title: Project Bookmark Search
   :results: 5, 10, 25, 50
```

**Overlay mode** (hidden by default, opened via `⌘+⇧+K`):

```rst
.. xlink-search::
   :overlay:
   :title: Quick Link Finder
   :results: 10, 25, 50, 100
```

**Custom CSS class for styling:**

```rst
.. xlink-search::
   :class: my-custom-search
   :title: Engineering Links
   :results: 20, 50
```

### Search Syntax

Users can combine multiple search operators in a single query:

| Syntax | Description | Example |
| --- | --- | --- |
| `<text>` | Free-text search on title and ID | `api docs` |
| `tag:<term>` | Include links with matching tag (slug, name, or description) | `tag:engineer` |
| `-tag:<term>` or `!tag:<term>` | Exclude links with matching tag | `-tag:internal` |
| `inurl:<term>` | Include links whose URL contains the term | `inurl:github.com` |
| `-inurl:<term>` or `!inurl:<term>` | Exclude links whose URL contains the term | `-inurl:internal.corp` |

**Combined example**: `api tag:engineer -tag:internal inurl:github.com` finds links with "api" in the title, tagged with something matching "engineer", excluding "internal" tags, and whose URL contains "github.com".

### Keyboard Shortcuts (within the search widget)

| Key | Action |
| --- | --- |
| `⌘+⇧+K` / `Ctrl+Shift+K` | Focus search input (or open overlay) |
| `↓` / `↑` | Navigate results table |
| `Tab` / `Shift+Tab` | Move selection forward/backward |
| `Enter` | Open selected link in new tab |
| `Shift+Enter` | Copy `:xlink:\`id\`` to clipboard |
| `Escape` | Clear search / deselect / close overlay |
| Type any letter (while table focused) | Return focus to search input |

### Directive Options

| Option | Type | Description |
| --- | --- | --- |
| `:title:` | String | Header text displayed above the search bar |
| `:results:` | Comma-separated integers | Page size options for the dropdown (default: `10, 25, 50, 100`) |
| `:overlay:` | Flag | Renders as a hidden overlay/modal, toggled via keyboard shortcut |
| `:class:` | String | Custom CSS classes on the container |

---

## Features

* **Centralized Management**: Store URLs, titles, and tags in simple, structured text files (`.xlink`).
* **Deep Folder Structures**: Recursively organize your `.xlink` files into nested directories. Create a hidden `.xlink` folder containing `section-name.rst` and `section-description.rst` to seamlessly generate rich metadata for an entire directory tree.
* **Interactive Search** *(HTML only)*: Embed a real-time, keyboard-navigable search interface with tag autocomplete and fuzzy matching.
* **Native Toctree Integration**: Automatically inject your generated link hierarchies directly into the Sphinx `toctree`, allowing them to appear in your sidebar navigation.
* **Collision-Proof Namespaces**: Safely handles duplicate filenames (e.g., `examples/example1.xlink` and `other/example1.xlink`) and identically named sections by automatically tracking relative paths and generating full-path HTML anchor IDs.
* **Python Expression Engine**: Filter your link database dynamically using a secure Python evaluation engine (e.g., `:query: "code" in tags and re.search('api', url)`).
* **N-Depth Tag Hierarchies**: Build complex, multi-level grouped lists using a powerful nested tag syntax (e.g., `manager[tracking[internal]]`).
* **Rich reST Descriptions**: Inject reStructuredText-formatted descriptions into your file and tag categories for annotated link directories.
* **Surgical Description Control**: Use `!file` and `!tag` modifiers to hide descriptions for specific files, tags, or entire sub-trees based on their hierarchy path.
* **Native Sphinx-Needs Support**: Integrates directly with `sphinx-needs` dynamic functions and `needs_string_links` to make external links clickable in metadata tables.
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
    'sphinx_needs',  # Optional: for dynamic function support
]
```

---

## Configuration (`conf.py`)

You don't need anything specific in your config to get started. Simply create an `xlinks` folder in your documentation `source` directory and create your first `.xlink` file (e.g., `test.xlink`).

```text
# xlink-section-name: Test File
# xlink-section-description: Here you can add a description, with\n\nline breaks **and** rst formatting.

unique-id :: Link Title :: Link Location :: tag1, tag2, taggroup1:sub1, taggroup1:sub2, taggroup2:sub1, taggroup2:sub2,
test-mail :: Company Mail App :: https://companymail.example.com :: tool:mail, dept:communications
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
    'tool:mail': ('Mail Tools', 'Communication Suite, SMTP Tooling'),
    'internal': 'Internal Only',
    'external': 'Third-Party Services'
}

# Dynamic Tag Patterns (regex-based validation)
# For identifier-style tags that follow a pattern but vary in their specific value.
# Uses re.fullmatch() — patterns must match the entire tag string.
# Format: r'regex-pattern': ('Category Name', 'Description')
xlink_allowed_tag_patterns = {
    r'DR-\d{4}': ('Decision Record', 'Architecture decision record identifiers.'),
    r'ADR\d{4}': ('ADR', 'Architecture decision records (compact format).'),
    r'KEY-\d+': ('JIRA Key', 'JIRA issue identifiers.'),
    r'\d{2}\.\d{2}': ('Version', 'Version identifiers (e.g. 11.21).'),
}

# Sphinx TOC Integration
# Define which builders automatically append lists to the Sphinx Document TOC tree.
xlink_add_to_toctree_builders = ['html', 'dirhtml', 'singlehtml', 'readthedocs']

# Sphinx-Needs Integration
# Specify which metadata fields should automatically use the xlink clickable mapping
xlink_needs_string_link_options = ['xlink', 'documentation', 'python-docs']

# Fallback name for untagged links
xlink_default_untagged_name = 'Uncategorized Links'

# Developer Experience (VSCode snippets generation)
xlink_generate_vscode_snippets = True

# Quality Assurance & URL Validation
xlink_check_links = False
xlink_check_timeout = 5.0

# PDF/LaTeX Output Control ('no', 'inline', 'footnote')
xlink_latex_show_urls = 'no'

# Visual Enhancements
xlink_render_link_icon = True
xlink_list_render_link_icon = False
```

### Configuration Examples by Use Case

**Minimal setup** (just links, no tags):

```python
extensions = ['sphinxcontrib.xlink']
xlink_directory = 'xlinks'
```

**Strict tag governance** (prevents typos, enables search descriptions):

```python
xlink_allowed_tags = {
    'frontend': ('Frontend', 'UI frameworks and component libraries'),
    'backend': ('Backend', 'Server-side APIs and microservices'),
    'devops': ('DevOps', 'CI/CD, containers, and infrastructure'),
}
xlink_generate_vscode_snippets = True  # Tags appear in autocomplete
```

**PDF-optimized output** (show URLs as footnotes in LaTeX):

```python
xlink_latex_show_urls = 'footnote'
xlink_render_link_icon = False  # Icons don't render in PDF
```

**CI/CD link validation** (check for broken links during build):

```python
xlink_check_links = True
xlink_check_timeout = 10.0
```

---

## Dynamic Tag Patterns (Regex-Based Validation)

When working with documentation bound to structured identifiers — decision records (`DR-0001`), JIRA keys (`KEY-42`), version numbers (`11.21`), or architecture decision records (`ADR0001`) — listing every possible tag in `xlink_allowed_tags` becomes impractical.

The `xlink_allowed_tag_patterns` config value lets you define **regex patterns** that validate tags dynamically, while keeping the same strict governance over what's allowed.

### How It Works

1. When a tag is encountered in a `.xlink` file, it is first checked against `xlink_allowed_tags` (exact match).
2. If no exact match is found, it is tested against each pattern in `xlink_allowed_tag_patterns` using `re.fullmatch()`.
3. If neither matches, a warning is emitted (just like with unknown static tags).

`re.fullmatch()` ensures the **entire tag** must match the pattern — partial matches are rejected. For example, `DR-\d{4}` matches `DR-0001` but not `XDR-0001`, `DR-00011`, or `DR-01`.

### Configuration

```python
# Static tags (exact match, unchanged behavior)
xlink_allowed_tags = {
    'general': ('General', 'General purpose links.'),
    'project:dawn': ('Project Dawn', 'Links for the Dawn initiative.'),
}

# Dynamic tag patterns (regex-based)
xlink_allowed_tag_patterns = {
    r'DR-\d{4}':    ('Decision Record', 'Architecture decision record identifiers (DR-0001 through DR-9999).'),
    r'ADR\d{4}':    ('ADR', 'Architecture decision records in compact format.'),
    r'KEY-\d+':     ('JIRA Key', 'JIRA issue identifiers (any number of digits).'),
    r'\d{2}\.\d{2}': ('Version', 'Two-part version identifiers like 11.21 or 03.07.'),
    r'RFC-\d+':     ('RFC', 'Internal Request for Comments identifiers.'),
    r'EPIC-[A-Z]{2,6}-\d+': ('Epic', 'Cross-team epic identifiers.'),
}
```

### .xlink File Usage

With the configuration above, these tags are all valid without being listed individually:

```text
# xlink-section-name: Architecture Decisions
dr-pg :: Use PostgreSQL :: https://wiki.example.com/dr/0001 :: DR-0001
dr-rest :: Use REST API :: https://wiki.example.com/dr/0002 :: DR-0002, general
dr-micro :: Adopt Microservices :: https://wiki.example.com/dr/0003 :: ADR0003

# xlink-section-name: Sprint Links
ticket-auth :: Auth Refactor :: https://jira.example.com/KEY-1234 :: KEY-1234
ticket-perf :: Performance Fix :: https://jira.example.com/KEY-5678 :: KEY-5678, project:dawn

# xlink-section-name: Release Notes
release-nov :: November Release :: https://releases.example.com/11.21 :: 11.21
release-dec :: December Release :: https://releases.example.com/12.01 :: 12.01
```

### Display Name Resolution

When grouped by tag, pattern-matched tags use their **literal value** as the section heading:

```rst
.. xlink-list::
   :group-by: tag
```

This produces sections headed by the actual identifiers (e.g., "DR-0001", "DR-0002", "KEY-1234") rather than the generic category name. This is intentional — each identifier is unique and semantically meaningful.

Static tags continue to use their configured display name (e.g., `'general'` renders as "General").

### Pattern Examples

| Pattern | Matches | Does NOT Match |
| --- | --- | --- |
| `r'DR-\d{4}'` | `DR-0001`, `DR-9999` | `DR-1`, `DR-00001`, `XDR-0001` |
| `r'KEY-\d+'` | `KEY-1`, `KEY-12345` | `KEY-`, `KEY`, `MYKEY-1` |
| `r'ADR\d{4}'` | `ADR0001`, `ADR1234` | `ADR-0001`, `ADR12345`, `XADR0001` |
| `r'\d{2}\.\d{2}'` | `11.21`, `03.07` | `1.21`, `111.21`, `11.2` |
| `r'RFC-\d+'` | `RFC-1`, `RFC-9999` | `RFC-`, `rfc-1`, `XRFC-1` |
| `r'v\d+\.\d+\.\d+'` | `v1.0.0`, `v12.3.45` | `v1.0`, `V1.0.0`, `1.0.0` |
| `r'EPIC-[A-Z]{2,6}-\d+'` | `EPIC-BE-1`, `EPIC-FRONT-42` | `EPIC-X-1`, `EPIC-be-1` |
| `r'(feat|fix|chore)/[a-z0-9-]+'` | `feat/auth-flow`, `fix/null-ptr` | `feature/x`, `FEAT/x` |

### Combining with Tag Filters

Pattern-matched tags work seamlessly with the `:tags:` directive option:

```rst
.. xlink-list::
   :tags: DR-0001, DR-0002, KEY-1234
   :group-by: tag
```

And with the `:query:` engine:

```rst
.. xlink-list::
   :query: any(re.match(r'DR-\d{4}', t) for t in tags)
```

### Invalid Pattern Handling

If a pattern in `xlink_allowed_tag_patterns` contains invalid regex syntax, a warning is emitted at build startup and the pattern is skipped:

```python
# This will emit: "xlink: Invalid regex in xlink_allowed_tag_patterns: '[invalid': ..."
xlink_allowed_tag_patterns = {
    r'[invalid': ('Bad Pattern', 'This will be skipped.'),
    r'DR-\d{4}': ('Decision Record', 'This still works.'),
}
```

### Migration from Static Tags

If you previously listed every identifier manually:

```python
# Before: verbose and hard to maintain
xlink_allowed_tags = {
    'DR-0001': ('DR-0001', 'Decision Record'),
    'DR-0002': ('DR-0002', 'Decision Record'),
    'DR-0003': ('DR-0003', 'Decision Record'),
    # ... hundreds more
}
```

Replace with a single pattern:

```python
# After: one pattern covers all current and future DRs
xlink_allowed_tag_patterns = {
    r'DR-\d{4}': ('Decision Record', 'Architecture decision record identifiers.'),
}
```

Existing static tags in `xlink_allowed_tags` continue to work unchanged — both systems coexist.

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

Safe builtins available: `any`, `all`, `bool`, `set`, `len`.

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

Additional dynamic functions are also registered:
* `[[ xlink_url('id') ]]` — returns only the URL
* `[[ xlink_title('id') ]]` — returns only the title

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

* `|xlink-term-smap|` ➔ Renders as: [SMAP](#)
* `|xlink-term-smap-full|` ➔ Renders as: [Supervisor Mode Access Prevention (SMAP)](#)

### 6. Document Reference Autocomplete

The extension automatically assigns a normalized anchor label to **every section header** in your entire project. Type `ddxr-` in VSCode and select it.

* `|xlink-ref-file-filtering|` ➔ Renders as: [File filtering](#)

### 7. Interactive Search Widget (HTML only)

Add a searchable, filterable table of all your links:

```rst
.. xlink-search::
   :title: Find a Bookmark
   :results: 10, 25, 50
```

Or as a hidden overlay triggered by `⌘+⇧+K`:

```rst
.. xlink-search::
   :overlay:
   :title: Quick Search
```

---

## Directive Options Reference

### `.. xlink-list::` Options

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
| `:download-as-bookmarks-external-link:` | URL | Fallback URL for the bookmark file (used in non-HTML builders). |
| `:render-list-with-bookmarks:` | `before` / `after` | Position of the download button relative to the list. |
| `:latex-show-urls:` | `inline`, `footnote`, `no` | LaTeX/PDF URL rendering style for this list. |
| `:render-link-icon:` | `true` or `false` | Override the global icon config for this specific list. |
| `:class:` | String | Inject custom CSS classes into the generated list container. |
| `:add-to-toctree:` | Flag | Append list sections to the Sphinx document TOC directly. |
| `:no-add-to-toctree:` | Flag | Prevents TOC integration (overrides `conf.py` default). |
| `:id-prefix:` | String | Custom prefix for HTML anchor IDs. Defaults to an auto-incrementing ID. |

### `.. xlink-search::` Options (HTML only)

| Option | Value Type | Description |
| --- | --- | --- |
| `:title:` | String | Header text displayed above the search bar. |
| `:results:` | Comma-separated integers | Page size options for the results dropdown (default: `10, 25, 50, 100`). |
| `:overlay:` | Flag | Render as a hidden modal overlay, toggled via `⌘+⇧+K` / `Ctrl+Shift+K`. |
| `:class:` | String | Custom CSS classes applied to the search container. |

### `:xlink:` Role

| Syntax | Result |
| --- | --- |
| `` :xlink:`link-id` `` | Renders with the title defined in the `.xlink` file |
| `` :xlink:`Custom Text <link-id>` `` | Renders with "Custom Text" as the label |

---

## BibTeX File Generation

`sphinxcontrib-xlink` can automatically generate a `.bib` (BibTeX) file from your `.xlink` entries. This is useful when your documentation references academic papers, standards, books, or online resources that you also want to cite in LaTeX documents or integrate with tools like `sphinxcontrib-bibtex`.

### How It Works

BibTeX metadata is encoded directly in the tag field of `.xlink` entries using the `bib:field:value` convention. Any entry tagged with `bib:type:<entrytype>` is collected and exported to a `.bib` file during the Sphinx build.

The xlink entry's **ID** becomes the BibTeX cite key, **title** becomes the `title` field, and **url** becomes the `url` field — these are inherited automatically and do not need to be repeated as tags.

### Quick Start

**1. Enable in `conf.py`:**

```python
extensions = ['sphinxcontrib.xlink']

xlink_generate_bib = 'references.bib'  # Output path (relative to source dir)

# Allow bib: tags via pattern matching
xlink_allowed_tag_patterns = {
    r'bib:[a-z]+:.*': ('BibTeX', 'BibTeX metadata tags.'),
}
```

**2. Add BibTeX metadata to your `.xlink` files:**

```text
# xlink-section-name: References
nist-csf :: NIST Cybersecurity Framework :: https://example.com/nist-csf :: bib:type:online, bib:author:Zeeshan Haider, bib:year:2021, bib:urldate:2026-07-10, general
moore-bio :: HD Moore Biography :: https://example.com/moore :: bib:type:book, bib:author:Harold David Moore, bib:year:2019, bib:publisher:Tech Press
```

**3. Build your docs:**

```bash
make html
```

A `references.bib` file is generated in your source directory:

```bibtex
@book{moore-bio,
  author = {Harold David Moore},
  title = {HD Moore Biography},
  url = {https://example.com/moore},
  year = {2019},
  publisher = {Tech Press},
}

@online{nist-csf,
  author = {Zeeshan Haider},
  title = {NIST Cybersecurity Framework},
  url = {https://example.com/nist-csf},
  year = {2021},
  urldate = {2026-07-10},
}
```

### Tag Convention

All BibTeX metadata tags use the `bib:field:value` format:

| Tag | Purpose |
| --- | --- |
| `bib:type:online` | BibTeX entry type (required to trigger export) |
| `bib:author:John Smith` | Author field |
| `bib:author:"van Beethoven, Ludwig"` | Author with comma (quoted) |
| `bib:year:2021` | Year field |
| `bib:publisher:O'Reilly` | Publisher field |
| `bib:journal:IEEE Security` | Journal field |
| `bib:booktitle:Proc. USENIX` | Booktitle field |
| `bib:institution:MIT` | Institution field |
| `bib:doi:https://doi.org/10.1000/xyz` | DOI (colons in value are fine) |
| `bib:urldate:2026-07-10` | URL access date |
| `bib:howpublished:Self-Published` | How published field |
| `bib:note:Accessed via VPN` | Note field |

**Important notes:**

- The `bib:type:*` tag is **required** — entries without it are ignored by the bib generator.
- `title` and `url` are automatically derived from the xlink entry itself (no need to repeat them as tags). If you explicitly set `bib:title:...` or `bib:url:...`, the explicit tag takes priority.
- Colons in values are handled correctly because the field/value split uses only the **first** colon after the `bib:` prefix.
- Entries are sorted alphabetically by cite key for deterministic output.

### Handling Commas in Values (Quote-Aware Parsing)

If a field value contains a comma (common in author names like "Last, First"), wrap it in double quotes:

```text
beethoven-bio :: Biography of Beethoven :: https://example.com/beethoven :: bib:type:book, bib:author:"van Beethoven, Ludwig", bib:year:1900, bib:publisher:Classic Books
```

The quotes prevent the comma from being treated as a tag separator. In the generated `.bib` file, the quotes are stripped:

```bibtex
@book{beethoven-bio,
  author = {van Beethoven, Ludwig},
  title = {Biography of Beethoven},
  url = {https://example.com/beethoven},
  year = {1900},
  publisher = {Classic Books},
}
```

This quote-aware parsing applies to **all** tags, not just bib tags. Any tag value containing commas can be quoted.

### Supported Entry Types

The following BibTeX entry types are supported with default required field validation:

| Entry Type | Required Fields |
| --- | --- |
| `article` | author, title, journal, year |
| `book` | author, title, publisher, year |
| `inproceedings` | author, title, booktitle, year |
| `manual` | title |
| `misc` | *(none)* |
| `online` | author, title, year, url |
| `techreport` | author, title, institution, year |

If required fields are missing, a **warning** is emitted during build (non-fatal):

```
WARNING: xlink-bib: Entry 'my-entry' (type 'article') is missing required fields: author, journal, year
```

### Configuration Options

```python
# Path to the generated .bib file (relative to srcdir, or absolute).
# Set to False to disable generation entirely.
xlink_generate_bib = 'references.bib'

# Customize required fields per entry type.
# Override the defaults or add new entry types.
xlink_bib_required_fields = {
    'article': ['author', 'title', 'journal', 'year'],
    'book': ['author', 'title', 'publisher', 'year'],
    'inproceedings': ['author', 'title', 'booktitle', 'year'],
    'manual': ['title'],
    'misc': [],
    'online': ['author', 'title', 'year', 'url'],
    'techreport': ['author', 'title', 'institution', 'year'],
}
```

### Mixing BibTeX and Regular Tags

Entries can have both `bib:` tags and regular tags simultaneously. Regular tags are used for filtering and grouping in `xlink-list` directives, while `bib:` tags drive the `.bib` file generation:

```text
nist-csf :: NIST Cybersecurity Framework :: https://example.com/nist-csf :: bib:type:online, bib:author:Zeeshan Haider, bib:year:2021, security, standards, general
```

This entry will:
1. Appear in `.bib` output as an `@online` entry
2. Appear under "security", "standards", and "general" tag groups in `xlink-list`

### Listing Only BibTeX Entries

Use the `:query:` engine to filter your link list to only show entries that have a `bib:type:*` tag:

```rst
.. xlink-list::
   :query: any(t.startswith('bib:type:') for t in tags)
   :group-by: tag
   :sort-by: title
   :order: asc
```

Or filter by specific BibTeX entry type:

```rst
.. Only books
.. xlink-list::
   :query: 'bib:type:book' in tags
   :sort-by: title

.. Only online resources
.. xlink-list::
   :query: 'bib:type:online' in tags
   :sort-by: title
```

### Sorting BibTeX Entries by Author

While the `.bib` file itself is sorted alphabetically by cite key, you can sort the rendered list by title (which often correlates with author for bibliographic entries):

```rst
.. xlink-list::
   :query: any(t.startswith('bib:type:') for t in tags)
   :sort-by: title
   :order: asc
```

To group by author using tag-based grouping, you can filter on `bib:author:` tags:

```rst
.. xlink-list::
   :query: any(t.startswith('bib:author:') for t in tags)
   :tags: bib:author:Zeeshan Haider, bib:author:Harold David Moore
   :group-by: tag
```

This creates separate sections per author, each listing their referenced works.

### Grouping by Entry Type

```rst
.. xlink-list::
   :query: any(t.startswith('bib:type:') for t in tags)
   :tags: bib:type:online, bib:type:book, bib:type:article
   :group-by: tag
   :sort-by: title
```

This renders sections like "bib:type:online", "bib:type:book", etc., each containing the relevant entries.

### Combining with `sphinxcontrib-bibtex`

If you also use `sphinxcontrib-bibtex` for citation rendering, point it at the generated `.bib` file:

```python
# conf.py
extensions = ['sphinxcontrib.xlink', 'sphinxcontrib.bibtex']

xlink_generate_bib = 'references.bib'
bibtex_bibfiles = ['references.bib']
```

Now you can use standard `.. bibliography::` directives and `:cite:` roles while managing all your references in `.xlink` files.

### Complete Example

**`conf.py`:**

```python
extensions = ['sphinxcontrib.xlink']

xlink_directory = 'xlinks'
xlink_generate_bib = 'references.bib'

xlink_allowed_tags = {
    'security': ('Security', 'Cybersecurity resources.'),
    'standards': ('Standards', 'Industry standards and frameworks.'),
    'general': ('General', 'General purpose links.'),
}

xlink_allowed_tag_patterns = {
    r'bib:[a-z]+:.*': ('BibTeX', 'BibTeX metadata tags.'),
}

xlink_generate_vscode_snippets = True
```

**`xlinks/references.xlink`:**

```text
# xlink-section-name: Academic References
# xlink-section-description: Papers, books, and standards referenced in this project.
nist-csf :: NIST Cybersecurity Framework :: https://www.nist.gov/cyberframework :: bib:type:online, bib:author:National Institute of Standards and Technology, bib:year:2018, bib:urldate:2026-07-10, security, standards
mitre-attack :: MITRE ATT&CK Framework :: https://attack.mitre.org :: bib:type:online, bib:author:MITRE Corporation, bib:year:2015, bib:urldate:2026-07-10, security
anderson-sec :: Security Engineering :: https://www.cl.cam.ac.uk/~rja14/book.html :: bib:type:book, bib:author:Ross Anderson, bib:year:2020, bib:publisher:Wiley, security
beethoven-opus :: Beethoven Complete Works :: https://example.com/beethoven :: bib:type:book, bib:author:"van Beethoven, Ludwig", bib:year:1827, bib:publisher:Classic Archive
rfc-tls13 :: TLS 1.3 Specification :: https://www.rfc-editor.org/rfc/rfc8446 :: bib:type:techreport, bib:author:Eric Rescorla, bib:year:2018, bib:institution:IETF, bib:doi:https://doi.org/10.17487/RFC8446, security, standards
```

**`docs/references.rst`:**

```rst
References
==========

All References (Rendered)
-------------------------

.. xlink-list::
   :query: any(t.startswith('bib:type:') for t in tags)
   :sort-by: title
   :order: asc

Grouped by Type
---------------

.. xlink-list::
   :query: any(t.startswith('bib:type:') for t in tags)
   :tags: bib:type:book, bib:type:online, bib:type:techreport
   :group-by: tag
   :sort-by: title

Security References Only
------------------------

.. xlink-list::
   :query: any(t.startswith('bib:type:') for t in tags) and 'security' in tags
   :sort-by: title
```

**Generated `references.bib`:**

```bibtex
@book{anderson-sec,
  author = {Ross Anderson},
  title = {Security Engineering},
  url = {https://www.cl.cam.ac.uk/~rja14/book.html},
  year = {2020},
  publisher = {Wiley},
}

@book{beethoven-opus,
  author = {van Beethoven, Ludwig},
  title = {Beethoven Complete Works},
  url = {https://example.com/beethoven},
  year = {1827},
  publisher = {Classic Archive},
}

@online{mitre-attack,
  author = {MITRE Corporation},
  title = {MITRE ATT&CK Framework},
  url = {https://attack.mitre.org},
  year = {2015},
  urldate = {2026-07-10},
}

@online{nist-csf,
  author = {National Institute of Standards and Technology},
  title = {NIST Cybersecurity Framework},
  url = {https://www.nist.gov/cyberframework},
  year = {2018},
  urldate = {2026-07-10},
}

@techreport{rfc-tls13,
  author = {Eric Rescorla},
  title = {TLS 1.3 Specification},
  url = {https://www.rfc-editor.org/rfc/rfc8446},
  year = {2018},
  institution = {IETF},
  doi = {https://doi.org/10.17487/RFC8446},
}
```
