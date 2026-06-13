/**
 * markdownRenderer.js — ChaseOS Studio
 *
 * Full pipeline: raw markdown → rendered HTML with:
 *   • [[WikiLink]] / [[target|alias]] → clickable purple <a class="wikilink">
 *   • ![[embed]] → blockquote placeholder
 *   • marked.js GFM rendering (tables, strikethrough, task-lists)
 *   • highlight.js syntax-highlighted code blocks
 *   • Tables wrapped in .table-wrapper with a "Copy" button
 *   • Code blocks with a per-block "Copy" button
 *
 * Usage:
 *   const html = window.MarkdownRenderer.render(rawText);
 *   container.innerHTML = html;
 *   window.MarkdownRenderer.wireAll(container, onWikilinkClick);
 *
 * wireAll() is shorthand for calling _wireWikilinks + _postprocessTables + _wireCodeCopy.
 */

window.MarkdownRenderer = (() => {
  'use strict';

  // ------------------------------------------------------------------
  // Internal helpers
  // ------------------------------------------------------------------

  /** Escape HTML for embedding raw text safely. */
  function _esc(s) {
    return String(s)
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;');
  }

  // Regex matching [[target]], [[target|alias]], and ![[embed]]
  // Captures: (1) optional "!" prefix, (2) target, (3) optional alias
  const WIKILINK_RE = /(!?)?\[\[([^\]\n|]{1,500})(?:\|([^\]\n]+))?\]\]/g;

  // Placeholder tag that survives markdown parsing
  const WL_OPEN = '\x02wl\x03';
  const WL_CLOSE = '\x02/wl\x03';

  // ------------------------------------------------------------------
  // Step 1 — pre-process [[WikiLinks]] before markdown parsing
  // ------------------------------------------------------------------

  function _preprocessWikilinks(text) {
    return text.replace(WIKILINK_RE, (match, bang, target, alias) => {
      const display = alias ? alias.trim() : target.trim();
      const t = target.trim();
      if (bang === '!') {
        // Embed — render an embed placeholder that _hydrateMarkdownEmbeds() fills in.
        return `\n<div class="markdown-embed" data-embed-target="${_esc(t)}"><span>Embed</span><strong>${_esc(display)}</strong></div>\n`;
      }
      // Encode as placeholder that won't be mangled by the markdown parser
      // We use base64 to survive link-detection heuristics
      const encoded = btoa(unescape(encodeURIComponent(t)));
      return `${WL_OPEN}data-target="${_esc(encoded)}"${WL_CLOSE}${_esc(display)}${WL_OPEN}/wl${WL_CLOSE}`;
    });
  }

  // ------------------------------------------------------------------
  // Step 2 — configure and run marked.js
  // ------------------------------------------------------------------

  function _configureMarked() {
    if (typeof marked === 'undefined') return;

    // highlight.js integration
    marked.use({
      renderer: (() => {
        const renderer = new marked.Renderer();
        renderer.code = function (token) {
          // token may be a string (older marked) or an object {text, lang, ...}
          const code = typeof token === 'string' ? token : (token.text || '');
          const lang = typeof token === 'string' ? '' : (token.lang || '');
          let highlighted;
          try {
            if (lang && typeof hljs !== 'undefined' && hljs.getLanguage(lang)) {
              highlighted = hljs.highlight(code, { language: lang, ignoreIllegals: true }).value;
            } else if (typeof hljs !== 'undefined') {
              highlighted = hljs.highlightAuto(code).value;
            } else {
              highlighted = _esc(code);
            }
          } catch (e) {
            highlighted = _esc(code);
          }
          const langLabel = lang ? `<span class="code-lang-label">${_esc(lang)}</span>` : '';
          return `<pre class="hljs">${langLabel}<code class="hljs language-${_esc(lang)}">${highlighted}</code></pre>`;
        };
        return renderer;
      })(),
      gfm: true,
      breaks: false,
    });
  }

  let _markedConfigured = false;

  function _render(preprocessed) {
    if (typeof marked === 'undefined') {
      // Fallback: return escaped plain text in a <pre>
      return `<pre>${_esc(preprocessed)}</pre>`;
    }
    if (!_markedConfigured) {
      _configureMarked();
      _markedConfigured = true;
    }
    try {
      return marked.parse(preprocessed);
    } catch (e) {
      return `<pre>${_esc(preprocessed)}</pre>`;
    }
  }

  // ------------------------------------------------------------------
  // Public: render(rawText) → HTML string
  // ------------------------------------------------------------------

  function render(rawText, _options = {}) {
    if (!rawText) return '';
    const preprocessed = _preprocessWikilinks(rawText);
    let html = _render(preprocessed);

    // Replace wikilink placeholders with real <a> tags
    // WL_OPEN = \x02wl\x03   WL_CLOSE = \x02/wl\x03
    html = html.replace(
      /\x02wl\x03data-target="([^"]+)"\x02\/wl\x03([\s\S]*?)\x02wl\x03\/wl\x02\/wl\x03/g,
      (_m, encoded, display) => {
        let target = encoded;
        try { target = decodeURIComponent(escape(atob(encoded))); } catch (_e) { /* keep as-is */ }
        return `<a class="wikilink" href="#" data-wikilink-target="${_esc(target)}" title="Open: ${_esc(target)}">${display}</a>`;
      }
    );

    // Catch any remaining open/close placeholders (malformed nesting)
    html = html.replace(/\x02wl\x03[^\x02]*\x02\/wl\x03/g, '');

    return html;
  }

  // ------------------------------------------------------------------
  // Post-processing: tables
  // ------------------------------------------------------------------

  function _postprocessTables(container) {
    container.querySelectorAll('table').forEach(table => {
      if (table.parentElement && table.parentElement.classList.contains('table-wrapper')) return;
      const wrapper = document.createElement('div');
      wrapper.className = 'table-wrapper';
      table.parentNode.insertBefore(wrapper, table);
      wrapper.appendChild(table);

      const btn = document.createElement('button');
      btn.className = 'copy-table-btn';
      btn.textContent = 'Copy';
      btn.addEventListener('click', () => {
        // Copy as TSV
        const rows = Array.from(table.querySelectorAll('tr'));
        const tsv = rows.map(r => Array.from(r.querySelectorAll('th,td')).map(c => c.textContent.trim()).join('\t')).join('\n');
        navigator.clipboard.writeText(tsv).then(() => {
          btn.textContent = 'Copied!';
          setTimeout(() => { btn.textContent = 'Copy'; }, 1500);
        }).catch(() => { btn.textContent = 'Error'; });
      });
      wrapper.appendChild(btn);
    });
  }

  // ------------------------------------------------------------------
  // Post-processing: WikiLink click wiring
  // ------------------------------------------------------------------

  function _wireWikilinks(container, onWikilinkClick) {
    container.querySelectorAll('a.wikilink').forEach(a => {
      a.addEventListener('click', e => {
        e.preventDefault();
        const target = a.getAttribute('data-wikilink-target') || '';
        if (onWikilinkClick) onWikilinkClick(target, a);
      });
    });
  }

  // ------------------------------------------------------------------
  // Post-processing: code block copy buttons
  // ------------------------------------------------------------------

  function _wireCodeCopy(container) {
    container.querySelectorAll('pre.hljs').forEach(pre => {
      if (pre.querySelector('.copy-code-btn')) return; // already wired
      const btn = document.createElement('button');
      btn.className = 'copy-code-btn';
      btn.textContent = 'Copy';
      btn.addEventListener('click', () => {
        const code = pre.querySelector('code');
        const text = code ? code.textContent : pre.textContent;
        navigator.clipboard.writeText(text).then(() => {
          btn.textContent = 'Copied!';
          setTimeout(() => { btn.textContent = 'Copy'; }, 1500);
        }).catch(() => { btn.textContent = 'Error'; });
      });
      pre.appendChild(btn);
    });
  }

  // ------------------------------------------------------------------
  // Convenience: wire everything at once
  // ------------------------------------------------------------------

  function wireAll(container, onWikilinkClick) {
    _wireWikilinks(container, onWikilinkClick);
    _postprocessTables(container);
    _wireCodeCopy(container);
  }

  // ------------------------------------------------------------------
  // Public API
  // ------------------------------------------------------------------

  return {
    render,
    wireAll,
    _preprocessWikilinks,
    _postprocessTables,
    _wireWikilinks,
    _wireCodeCopy,
  };
})();
