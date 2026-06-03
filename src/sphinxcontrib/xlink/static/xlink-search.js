document.addEventListener('DOMContentLoaded', () => {
    const apps = document.querySelectorAll('.xlink-search-app');
    apps.forEach((app) => initXlinkSearch(app));
});

// Implement CMD-Shift-K / Ctrl-Shift-K to focus the Bookmark Search
document.addEventListener('keydown', (e) => {
    if ((e.metaKey || e.ctrlKey) && e.shiftKey && e.key.toLowerCase() === 'k') {
        const apps = document.querySelectorAll('.xlink-search-app');
        if (apps.length > 0) {
            e.preventDefault();
            let overlayToggled = false;
            apps.forEach(app => {
                if (app.classList.contains('xlink-is-overlay')) {
                    if (!app.classList.contains('show')) {
                        app.classList.add('show');
                    }
                    overlayToggled = true;
                    const input = app.querySelector('.xlink-search-input');
                    if (input) {
                        input.focus();
                        input.select();
                    }
                }
            });
            if (!overlayToggled) {
                // Default inline focus strategy
                const firstInput = document.querySelector('.xlink-search-input');
                if (firstInput) {
                    firstInput.focus();
                    firstInput.select();
                    firstInput.scrollIntoView({ behavior: 'smooth', block: 'center' });
                }
            }
        }
    }
});

document.addEventListener('keydown', (e) => {
    if ((e.metaKey || e.ctrlKey) && e.shiftKey && e.key.toLowerCase() === 'k') {
        const firstInput = document.querySelector('.xlink-search-input');
        if (firstInput) {
            e.preventDefault();
            firstInput.focus();
            firstInput.select();
            firstInput.scrollIntoView({ behavior: 'smooth', block: 'center' });
        }
    }
});

function initXlinkSearch(appContainer) {
    // Retrieve matching datablock
    const elementId = appContainer.id.replace('xsa-', '');
    const dataScript = document.getElementById(`xsd-${elementId}`);

    if (!dataScript) return;

    // Make container focusable to capture keyboard events properly when input is blurred
    appContainer.setAttribute('tabindex', '-1');
    appContainer.style.outline = 'none';
    
    // Close overlay if background is clicked
    if (appContainer.classList.contains('xlink-is-overlay')) {
        appContainer.addEventListener('mousedown', (e) => {
            if (e.target === appContainer) {
                appContainer.classList.remove('show');
            }
        });
    }

    let payload;
    try {
        payload = JSON.parse(dataScript.textContent);
    } catch (e) {
        console.error("Failed to parse xlink search data:", e);
        return;
    }

    const allLinks = payload.links || [];
    const allTags = payload.tags || [];
    const tagDefs = payload.tag_defs || {};

    // Stop words ignored in tag: searches to prevent overly broad matching
    const STOP_WORDS = new Set([
        'the', 'and', 'or', 'a', 'an', 'in', 'on', 'at', 'to', 'for',
        'of', 'with', 'by', 'from', 'is', 'it', 'as', 'be', 'are',
        'was', 'were', 'been', 'has', 'have', 'had', 'do', 'does',
        'did', 'but', 'not', 'so', 'if', 'no', 'nor', 'up', 'out',
        'this', 'that', 'these', 'those', 'then', 'than', 'too',
        'very', 'can', 'will', 'just', 'into', 'also', 'about'
    ]);

    // Precompute a searchable text index for each tag: slug + display name + description
    const tagSearchIndex = {};
    for (const tag of allTags) {
        const def = tagDefs[tag] || {};
        const parts = [tag, def.name || '', def.desc || ''];
        tagSearchIndex[tag] = parts.join(' ').toLowerCase();
    }

    const input = appContainer.querySelector('.xlink-search-input');
    const autocomplete = appContainer.querySelector('.xlink-autocomplete-dropdown');
    const pageSizeSelect = appContainer.querySelector('.xlink-search-pagesize');
    const tbody = appContainer.querySelector('tbody');
    const info = appContainer.querySelector('.xlink-search-info');
    const toast = appContainer.querySelector('.xlink-search-toast');

    try {
        const LOCAL_STORAGE_KEY = 'xlink-search-pagesize';
        const savedPageSize = localStorage.getItem(LOCAL_STORAGE_KEY);
        if (savedPageSize) {
            const optionExists = Array.from(pageSizeSelect.options).some(opt => opt.value === savedPageSize);
            if (optionExists) {
                pageSizeSelect.value = savedPageSize;
            }
        }

        let pageSize = parseInt(pageSizeSelect.value, 10);
        let filteredLinks = [...allLinks];
        let tagMatchContext = new Map(); // link object -> [{tag, name, desc, term}]
        let selectedRowIndex = -1; // global index
        let pageStartIndex = 0;
        let acSelectedIndex = -1;

        // Focus input on page load whenever the element is inserted or visible.
        // SetTimeout helps if the script fires before display is properly calculated
        setTimeout(() => input.focus(), 100);

        function showToast(msg) {
            toast.textContent = msg;
            toast.style.display = 'block';
            toast.classList.add('show');
            setTimeout(() => {
                toast.classList.remove('show');
                setTimeout(() => { toast.style.display = 'none'; }, 300);
            }, 2000);
        }

        function renderTable() {
            tbody.innerHTML = '';
            const pageLinks = filteredLinks.slice(pageStartIndex, pageStartIndex + pageSize);
            const endViewing = Math.min(pageStartIndex + pageSize, filteredLinks.length);
            
            if (filteredLinks.length === 0) {
                info.textContent = `Showing 0 of 0 results`;
            } else {
                info.textContent = `Showing ${pageStartIndex + 1}-${endViewing} of ${filteredLinks.length} results`;
            }

            if (pageLinks.length === 0) {
                tbody.innerHTML = '<tr><td colspan="3" class="xlink-search-empty">No results found</td></tr>';
                return;
            }

            pageLinks.forEach((link, idx) => {
                const globalIndex = pageStartIndex + idx;
                const tr = document.createElement('tr');
                tr.className = 'xlink-search-row';
                tr.dataset.index = globalIndex;
                tr.dataset.lid = link.id;
                tr.dataset.url = link.url;

                // Name column
                const tdName = document.createElement('td');
                tdName.className = 'xlink-td-name';
                tdName.textContent = link.title || link.id;

                // Tags column
                const tdTags = document.createElement('td');
                tdTags.className = 'xlink-td-tags';
                const contexts = tagMatchContext.get(link);
                const contextByTag = {};
                if (contexts) {
                    for (const ctx of contexts) {
                        contextByTag[ctx.tag.toLowerCase()] = ctx;
                    }
                }
                if (link.tags && link.tags.length > 0) {
                    link.tags.forEach(t => {
                        const span = document.createElement('span');
                        span.className = 'xlink-tag-badge';
                        span.textContent = t;
                        tdTags.appendChild(span);

                        // Show match context if this tag matched via name/description
                        const ctx = contextByTag[t.toLowerCase()];
                        if (ctx) {
                            const hint = document.createElement('div');
                            hint.className = 'xlink-tag-match-context';
                            // Build context text: "Display Name — description" with search term highlighted
                            const parts = [];
                            if (ctx.name) parts.push(ctx.name);
                            if (ctx.desc) parts.push(ctx.desc);
                            const contextText = parts.join(' \u2014 ');
                            if (ctx.term && contextText.toLowerCase().includes(ctx.term)) {
                                // Highlight the matching term
                                const regex = new RegExp('(' + ctx.term.replace(/[.*+?^${}()|[\]\\]/g, '\\$&') + ')', 'gi');
                                hint.innerHTML = contextText.replace(regex, '<mark class="xlink-match-highlight">$1</mark>');
                            } else {
                                hint.textContent = contextText;
                            }
                            tdTags.appendChild(hint);
                        }
                    });
                } else {
                    tdTags.textContent = '';
                }

                // Link column
                const tdLink = document.createElement('td');
                tdLink.className = 'xlink-td-link';
                const a = document.createElement('a');
                a.href = link.url;
                a.target = '_blank';
                a.textContent = link.url;
                a.tabIndex = -1; // disable natural tabbing to enforce custom arrow nav
                tdLink.appendChild(a);

                tr.appendChild(tdName);
                tr.appendChild(tdTags);
                tr.appendChild(tdLink);

                // Click interaction
                tr.addEventListener('click', () => {
                    window.open(link.url, '_blank');
                });

                tbody.appendChild(tr);
            });

            // Re-apply selection state
            updateRowSelection();
        }

        function updateRowSelection() {
            const rows = tbody.querySelectorAll('tr.xlink-search-row');
            rows.forEach((r, idx) => {
                const globalIndex = pageStartIndex + idx;
                if (globalIndex === selectedRowIndex) {
                    r.classList.add('selected');
                    r.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
                } else {
                    r.classList.remove('selected');
                }
            });
        }
        
        function ensureGlobalSelectionVisible() {
            let rendered = false;
            
            // If selection wrapped from bottom -> 0
            if (selectedRowIndex === 0 && pageStartIndex !== 0) {
                pageStartIndex = 0;
                renderTable();
                rendered = true;
            } 
            // If selection wrapped from 0 -> bottom
            else if (selectedRowIndex === filteredLinks.length - 1 && pageStartIndex < Math.max(0, filteredLinks.length - pageSize)) {
                pageStartIndex = Math.max(0, filteredLinks.length - pageSize);
                renderTable();
                rendered = true;
            }
            // Scrolling down past view boundary
            else if (selectedRowIndex !== -1 && selectedRowIndex >= pageStartIndex + pageSize) {
                pageStartIndex = Math.min(
                    pageStartIndex + pageSize,
                    Math.max(0, filteredLinks.length - pageSize)
                );
                renderTable();
                rendered = true;
            } 
            // Scrolling up past view boundary
            else if (selectedRowIndex !== -1 && selectedRowIndex < pageStartIndex) {
                pageStartIndex = Math.max(0, pageStartIndex - pageSize);
                renderTable();
                rendered = true;
            }
            // If we lost selection completely and we're not at top, reset view
            else if (selectedRowIndex === -1 && pageStartIndex !== 0) {
                pageStartIndex = 0;
                renderTable();
                rendered = true;
            }
            
            if (!rendered) {
                updateRowSelection();
            }
        }

        function doSearch() {
            const query = input.value.trim();
            tagMatchContext = new Map();

            if (!query) {
                filteredLinks = [...allLinks];
            } else {
                const tokens = query.split(/\s+/);
                const reqTags = [];
                const excTags = [];
                const reqUrls = [];
                const excUrls = [];
                const terms = [];

                tokens.forEach(tok => {
                    if (tok.startsWith('tag:')) {
                        const t = tok.substring(4).toLowerCase();
                        if (t) reqTags.push(t);
                    } else if (tok.startsWith('-tag:')) {
                        const t = tok.substring(5).toLowerCase();
                        if (t) excTags.push(t);
                    } else if (tok.startsWith('!tag:')) {
                        const t = tok.substring(5).toLowerCase();
                        if (t) excTags.push(t);
                    } else if (tok.startsWith('inurl:')) {
                        const t = tok.substring(6).toLowerCase();
                        if (t) reqUrls.push(t);
                    } else if (tok.startsWith('-inurl:') || tok.startsWith('!inurl:')) {
                        const t = tok.substring(7).toLowerCase();
                        if (t) excUrls.push(t);
                    } else {
                        terms.push(tok.toLowerCase());
                    }
                });

                filteredLinks = [];
                for (const link of allLinks) {
                    const linkLabel = ((link.title || '') + ' ' + (link.id || '')).toLowerCase();
                    const linkTags = link.tags ? link.tags.map(t => t.toLowerCase()) : [];

                    // Check text terms
                    let pass = true;
                    for (const t of terms) {
                        if (!linkLabel.includes(t)) { pass = false; break; }
                    }
                    if (!pass) continue;

                    // Check required tags (AND logic) — matches against slug, name, and description
                    // Also capture match context when a tag matched via its definition
                    const linkContexts = [];
                    let tagPass = true;
                    for (const rt of reqTags) {
                        if (STOP_WORDS.has(rt)) continue;
                        let matched = false;
                        for (const t of linkTags) {
                            const searchText = tagSearchIndex[t] || t;
                            if (searchText.includes(rt)) {
                                matched = true;
                                // If the match was NOT via the slug directly, record context
                                if (!t.includes(rt)) {
                                    const origTag = (link.tags || []).find(ot => ot.toLowerCase() === t) || t;
                                    const def = tagDefs[origTag] || tagDefs[t] || {};
                                    linkContexts.push({
                                        tag: origTag,
                                        name: def.name || '',
                                        desc: def.desc || '',
                                        term: rt
                                    });
                                }
                                break;
                            }
                        }
                        if (!matched) { tagPass = false; break; }
                    }
                    if (!tagPass) continue;

                    // Check excluded tags (NOT logic) — matches against slug, name, and description
                    let excPass = true;
                    for (const et of excTags) {
                        if (STOP_WORDS.has(et)) continue;
                        if (linkTags.some(t => {
                            const searchText = tagSearchIndex[t] || t;
                            return searchText.includes(et);
                        })) { excPass = false; break; }
                    }
                    if (!excPass) continue;

                    const linkUrl = (link.url || '').toLowerCase();
                    // Check required URLs
                    let urlPass = true;
                    for (const ru of reqUrls) {
                        if (!linkUrl.includes(ru)) { urlPass = false; break; }
                    }
                    if (!urlPass) continue;

                    // Check excluded URLs
                    let excUrlPass = true;
                    for (const eu of excUrls) {
                        if (linkUrl.includes(eu)) { excUrlPass = false; break; }
                    }
                    if (!excUrlPass) continue;

                    // Link passed all filters
                    if (linkContexts.length > 0) {
                        tagMatchContext.set(link, linkContexts);
                    }
                    filteredLinks.push(link);
                }
            }

            selectedRowIndex = -1; // reset selection
            pageStartIndex = 0;
            renderTable();
        }

        pageSizeSelect.addEventListener('change', (e) => {
            localStorage.setItem(LOCAL_STORAGE_KEY, e.target.value);
            pageSize = parseInt(e.target.value, 10);
            selectedRowIndex = -1;
            pageStartIndex = 0;
            renderTable();
        });

        // --- Autocomplete Logic ---

        function updateAutocomplete() {
            const val = input.value;
            const cursorPosition = input.selectionStart;
            // We only show autocomplete if we are currently typing a tag: or -tag:
            const substringToCursor = val.substring(0, cursorPosition);
            const words = substringToCursor.split(/\s+/);
            const currentWord = words[words.length - 1] || "";

            let isTagMatch = currentWord.startsWith('tag:');
            let isNegTagMatch = currentWord.startsWith('-tag:') || currentWord.startsWith('!tag:');

            let prefixToStrip = "";
            if (isTagMatch) prefixToStrip = "tag:";
            else if (currentWord.startsWith('-tag:')) prefixToStrip = "-tag:";
            else if (currentWord.startsWith('!tag:')) prefixToStrip = "!tag:";

            if (isTagMatch || isNegTagMatch) {
                const typedTag = currentWord.substring(prefixToStrip.length).toLowerCase();
                const matchingTags = allTags.filter(t => {
                    const searchText = tagSearchIndex[t] || t.toLowerCase();
                    return searchText.includes(typedTag);
                });

                if (matchingTags.length > 0) {
                    autocomplete.style.display = 'block';
                    autocomplete.innerHTML = '';
                    matchingTags.forEach((t, idx) => {
                        const div = document.createElement('div');
                        div.className = 'xlink-ac-item';
                        if (idx === acSelectedIndex) div.classList.add('selected');
                        div.textContent = prefixToStrip + t;

                        div.addEventListener('click', () => {
                            applyAutocomplete(currentWord, prefixToStrip + t);
                        });

                        autocomplete.appendChild(div);
                    });
                } else {
                    autocomplete.style.display = 'none';
                    acSelectedIndex = -1;
                }
            } else {
                autocomplete.style.display = 'none';
                acSelectedIndex = -1;
            }
        }

        function applyAutocomplete(replacedWord, resultingWord) {
            const val = input.value;
            const cursorPosition = input.selectionStart;
            const substringToCursor = val.substring(0, cursorPosition);
            const words = substringToCursor.split(/\s+/);
            words[words.length - 1] = resultingWord;

            const newSubstringToCursor = words.join(" ") + " "; // add trailing space
            const remaining = val.substring(cursorPosition);

            input.value = newSubstringToCursor + remaining;
            input.focus();
            input.setSelectionRange(newSubstringToCursor.length, newSubstringToCursor.length);

            autocomplete.style.display = 'none';
            acSelectedIndex = -1;
            doSearch();
        }

        input.addEventListener('input', () => {
            acSelectedIndex = -1;
            doSearch();
            updateAutocomplete();
        });

        input.addEventListener('click', updateAutocomplete);

        document.addEventListener('click', (e) => {
            if (!appContainer.contains(e.target)) {
                autocomplete.style.display = 'none';
            }
        });

        // --- Keyboard Navigation ---
        appContainer.addEventListener('keydown', (e) => {
            const totalRows = filteredLinks.length;
            const isTableFocused = selectedRowIndex >= 0;
            const acVisible = autocomplete.style.display === 'block';

            if (acVisible) {
                const acItemsCount = autocomplete.querySelectorAll('.xlink-ac-item').length;
                if (e.key === 'ArrowDown') {
                    e.preventDefault();
                    acSelectedIndex = (acSelectedIndex + 1) % acItemsCount;
                    updateAutocomplete();
                    return;
                } else if (e.key === 'ArrowUp') {
                    e.preventDefault();
                    acSelectedIndex = (acSelectedIndex - 1 + acItemsCount) % acItemsCount;
                    updateAutocomplete();
                    return;
                } else if (e.key === 'Enter' || e.key === 'Tab') {
                    if (acSelectedIndex >= 0) {
                        e.preventDefault();
                        autocomplete.querySelectorAll('.xlink-ac-item')[acSelectedIndex].click();
                    } else if (e.key === 'Tab' && acItemsCount > 0) {
                        // default to first item if none selected but tab pressed
                        e.preventDefault();
                        autocomplete.querySelectorAll('.xlink-ac-item')[0].click();
                    }
                    return;
                } else if (e.key === 'Escape') {
                    autocomplete.style.display = 'none';
                    return;
                }
            }

            if (e.key === 'ArrowDown') {
                e.preventDefault();
                if (totalRows > 0) {
                    if (selectedRowIndex < totalRows - 1) {
                        selectedRowIndex += 1;
                    } else {
                        selectedRowIndex = 0; // Wrap to first
                    }
                    appContainer.focus();
                    ensureGlobalSelectionVisible();
                }
            } else if (e.key === 'ArrowUp') {
                if (isTableFocused && totalRows > 0) {
                    e.preventDefault();
                    if (selectedRowIndex > 0) {
                        selectedRowIndex -= 1;
                    } else {
                        selectedRowIndex = totalRows - 1; // Wrap to last
                    }
                    ensureGlobalSelectionVisible();
                }
            } else if (e.key === 'Tab') {
                if (document.activeElement === input && totalRows > 0 && !e.shiftKey) {
                    e.preventDefault();
                    selectedRowIndex = 0;
                    appContainer.focus();
                    ensureGlobalSelectionVisible();
                } else if (document.activeElement === input && totalRows > 0 && e.shiftKey) {
                    e.preventDefault();
                    selectedRowIndex = totalRows - 1;
                    appContainer.focus();
                    ensureGlobalSelectionVisible();
                } else if (isTableFocused && !e.shiftKey) {
                    e.preventDefault();
                    if (selectedRowIndex < totalRows - 1) {
                        selectedRowIndex += 1;
                    } else {
                        selectedRowIndex = 0; // Wrap to first
                    }
                    ensureGlobalSelectionVisible();
                } else if (isTableFocused && e.shiftKey) {
                    e.preventDefault();
                    if (selectedRowIndex > 0) {
                        selectedRowIndex -= 1;
                    } else {
                        selectedRowIndex = totalRows - 1; // Wrap to last
                    }
                    ensureGlobalSelectionVisible();
                }
            } else if (e.key === 'Enter') {
                if (isTableFocused && selectedRowIndex !== -1) {
                    e.preventDefault();
                    // retrieve exact link from global filtered list, not DOM, since DOM might not be accurately matched if user hit enter before render completed
                    const link = filteredLinks[selectedRowIndex];
                    if (link) {
                        const lid = link.id;
                        const url = link.url;

                        if (e.shiftKey) {
                            // Copy to clipboard
                            const textToCopy = "\\:xlink:\\`" + lid + "\\`";
                            navigator.clipboard.writeText(textToCopy).then(() => {
                                showToast(`Copied ${textToCopy}`);
                            }).catch(err => {
                                console.error('Failed to copy: ', err);
                                showToast('Failed to copy');
                            });
                        } else {
                            // Open link
                            window.open(url, '_blank');
                        }
                    }
                }
            } else if (e.key === 'Escape') {
                if (selectedRowIndex === -1 && input.value === '') {
                    if (appContainer.classList.contains('xlink-is-overlay')) {
                        appContainer.classList.remove('show');
                    }
                } else {
                    selectedRowIndex = -1;
                    updateRowSelection();
                    if (document.activeElement === input && input.value !== '') {
                        input.value = '';
                        doSearch();
                    }
                    input.focus();
                }
            } else if (document.activeElement !== input && !e.ctrlKey && !e.metaKey && !e.altKey && e.key.length === 1) {
                // Typing letters while table is focused bumps focus back to input
                selectedRowIndex = -1;
                updateRowSelection();
                input.focus();
            }
        });

        // Initial render
        renderTable();
    } catch (err) {
        if (tbody) {
            tbody.innerHTML = `<tr><td colspan="3" style="color:red">JS Error: ${err.message}</td></tr>`;
        } else {
            appContainer.innerHTML = `<div style="color:red">JS Error: ${err.message}</div>`;
        }
    }
}
