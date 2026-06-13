/**
 * inspectorTabs.js — Tabbed inspector panel with 7 tabs.
 *
 * Tabs: Overview, Relations, Provenance, Trust, Runtime, Source, Debug.
 * All data comes from the node inspector contract (get_node API call).
 */

'use strict';

const INSPECTOR_TABS = [
  { id: 'overview',    label: 'Overview' },
  { id: 'relations',   label: 'Relations' },
  { id: 'provenance',  label: 'Provenance' },
  { id: 'trust',       label: 'Trust' },
  { id: 'runtime',     label: 'Runtime' },
  { id: 'source',      label: 'Source' },
  { id: 'debug',       label: 'Debug' },
];

let _activeTab = 'overview';
let _currentNodeData = null;
let _inspectorSettings = {};

// Pass 10B graph inspector is read-only by default. Future approval-gated
// metadata edit surfaces can opt in explicitly without making graph styling or
// inspection imply node editing authority.
const GRAPH_INSPECTOR_METADATA_EDIT_ENABLED = window.GraphInspectorMetadataEditEnabled === true;

function setInspectorSettings(settings) {
  _inspectorSettings = settings || {};
  if (_inspectorSettings.default_tab) _activeTab = _inspectorSettings.default_tab;
}

function _visibleInspectorTabs() {
  return INSPECTOR_TABS.filter(tab => {
    if (tab.id === 'provenance' && _inspectorSettings.show_provenance_tab === false) return false;
    if (tab.id === 'debug' && _inspectorSettings.show_raw_metadata !== true) return false;
    return true;
  });
}

function _ensureVisibleActiveTab() {
  const visible = _visibleInspectorTabs();
  if (visible.some(tab => tab.id === _activeTab)) return visible;
  const fallback = _inspectorSettings.default_tab && visible.some(tab => tab.id === _inspectorSettings.default_tab)
    ? _inspectorSettings.default_tab
    : (visible[0] && visible[0].id) || 'overview';
  _activeTab = fallback;
  return visible;
}

// ── Tab header rendering ──────────────────────────────────────────────────────

function renderTabHeader(onTabSelect) {
  const header = document.getElementById('inspector-tabs');
  if (!header) return;

  header.innerHTML = '';
  for (const tab of _ensureVisibleActiveTab()) {
    const btn = document.createElement('button');
    btn.className = 'inspector-tab-btn' + (tab.id === _activeTab ? ' active' : '');
    btn.textContent = tab.label;
    btn.dataset.tabId = tab.id;
    btn.addEventListener('click', () => {
      _activeTab = tab.id;
      header.querySelectorAll('.inspector-tab-btn').forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      if (_currentNodeData) renderTabContent(_currentNodeData);
      if (onTabSelect) onTabSelect(tab.id);
    });
    header.appendChild(btn);
  }
}

// ── Main tab content dispatcher ───────────────────────────────────────────────

function renderTabContent(nodeData) {
  _currentNodeData = nodeData;
  const body = document.getElementById('inspector-tab-body');
  if (!body) return;
  _ensureVisibleActiveTab();

  switch (_activeTab) {
    case 'overview':
      body.innerHTML = _buildMetadataCard(nodeData);
      _loadOverviewContent(nodeData, body);
      _bindMetadataEditControls(nodeData, body);
      break;
    case 'relations':
      body.innerHTML = _renderRelations(nodeData);
      _wireRelationClicks(body);
      break;
    case 'provenance': body.innerHTML = _renderProvenance(nodeData); break;
    case 'trust':      body.innerHTML = _renderTrust(nodeData);      break;
    case 'runtime':    body.innerHTML = _renderRuntime(nodeData);    break;
    case 'source':     body.innerHTML = _renderSource(nodeData);     break;
    case 'debug':      body.innerHTML = _renderDebug(nodeData);      break;
    default:
      body.innerHTML = _buildMetadataCard(nodeData);
      _loadOverviewContent(nodeData, body);
      _bindMetadataEditControls(nodeData, body);
  }

  if (_activeTab === 'provenance') {
    _hydrateProvenance(nodeData, body);
  }
}

// ── Helpers ───────────────────────────────────────────────────────────────────

function _esc(str) {
  return String(str || '')
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;');
}

function _row(label, value) {
  if (value == null || value === '') return '';
  return `<div class="inspector-row"><span class="inspector-key">${_esc(label)}</span><span class="inspector-val">${_esc(String(value))}</span></div>`;
}

function _section(title, content) {
  if (!content) return '';
  return `<div class="inspector-section"><div class="inspector-section-title">${_esc(title)}</div>${content}</div>`;
}

function _compactRows(obj) {
  if (!obj || typeof obj !== 'object') return '';
  return Object.entries(obj)
    .filter(([_, v]) => v != null && v !== '' && !(Array.isArray(v) && !v.length))
    .map(([k, v]) => _row(k, typeof v === 'object' ? JSON.stringify(v) : v))
    .join('');
}

function _selectedNode(data) {
  return data.selected_node || data.node || data.data || data;
}

function _nodeProps(data) {
  return (_selectedNode(data).properties) || {};
}

function _nodeId(data) {
  const node = _selectedNode(data);
  return node.id || node.node_id || '';
}

function _nodePath(data) {
  const node = _selectedNode(data);
  const props = _nodeProps(data);
  return props.path || node.path || node.file_path || node.stable_key || '';
}

function _renderMetadataEditShell(data) {
  const nodeId = _nodeId(data);
  const path = _nodePath(data);
  if (!nodeId && !path) return '';
  return `
    <div class="metadata-edit-drawer" data-metadata-edit-drawer style="display:none;">
      <div class="metadata-edit-head">
        <div>
          <div class="inspector-section-title">Metadata Edit</div>
          <div class="metadata-edit-boundary">approval-gated</div>
        </div>
        <button class="btn-secondary metadata-edit-refresh" data-metadata-edit-refresh>Refresh</button>
      </div>
      <div class="metadata-edit-form" data-metadata-edit-form></div>
      <div class="metadata-edit-actions">
        <button class="btn-secondary" data-metadata-edit-cancel>Cancel</button>
        <button class="btn-primary" data-metadata-edit-save>Queue Approval</button>
      </div>
      <div class="metadata-edit-status" data-metadata-edit-status></div>
    </div>
    <div class="metadata-edit-launch-row">
      <button class="btn-secondary" data-metadata-edit-open>Edit Metadata</button>
    </div>`;
}

function _metadataFieldInput(field, value) {
  const isLong = field === 'summary';
  const rendered = Array.isArray(value) ? value.join(', ') : (value == null ? '' : String(value));
  if (isLong) {
    return `<textarea data-metadata-field="${_esc(field)}" rows="3">${_esc(rendered)}</textarea>`;
  }
  return `<input data-metadata-field="${_esc(field)}" type="text" value="${_esc(rendered)}">`;
}

function _renderMetadataEditForm(model) {
  const fields = model.editable_fields || [];
  const current = model.current || {};
  return fields.map(field => `
    <label class="metadata-edit-row">
      <span>${_esc(field)}</span>
      ${_metadataFieldInput(field, current[field])}
    </label>`).join('');
}

async function _loadMetadataEditModel(data, body) {
  const drawer = body.querySelector('[data-metadata-edit-drawer]');
  const form = body.querySelector('[data-metadata-edit-form]');
  const status = body.querySelector('[data-metadata-edit-status]');
  const api = window.pywebview && window.pywebview.api;
  if (!drawer || !form || !api || !api.get_node_metadata_edit_model) return;
  if (status) status.textContent = 'Loading editable metadata...';
  try {
    const resp = await api.get_node_metadata_edit_model(_nodeId(data), _nodePath(data));
    if (!resp || !resp.ok) {
      const msg = (resp && resp.error && resp.error.message) || 'Metadata edit model unavailable.';
      if (status) status.textContent = msg;
      form.innerHTML = '';
      return;
    }
    data._metadata_edit_model = resp.data;
    form.innerHTML = _renderMetadataEditForm(resp.data);
    if (status) status.textContent = 'Changes will queue an approval request. Trust, provenance, canonical, generated, and runtime authority fields are locked.';
  } catch (err) {
    if (status) status.textContent = `Metadata model error: ${err.message}`;
  }
}

function _collectMetadataFields(body) {
  const fields = {};
  body.querySelectorAll('[data-metadata-field]').forEach(input => {
    const key = input.getAttribute('data-metadata-field');
    if (!key) return;
    fields[key] = input.value;
  });
  return fields;
}

async function _saveMetadataEdit(data, body) {
  const status = body.querySelector('[data-metadata-edit-status]');
  const api = window.pywebview && window.pywebview.api;
  if (!api || !api.update_node_metadata) {
    if (status) status.textContent = 'Metadata update API unavailable.';
    return;
  }
  if (status) status.textContent = 'Queueing metadata approval...';
  try {
    const resp = await api.update_node_metadata(_nodeId(data), _collectMetadataFields(body), _nodePath(data));
    if (resp && resp.status === 'requires_approval') {
      if (status) status.textContent = 'Approval queued.';
      if (window.ApprovalModal) {
        window.ApprovalModal.showApprovalModal(resp.approval, () => {
          if (window.WriteActions && window.WriteActions.refreshAfterApproval) {
            window.WriteActions.refreshAfterApproval();
          }
        });
      }
      return;
    }
    if (resp && resp.ok) {
      if (status) status.textContent = 'Metadata updated.';
      if (window.WriteActions && window.WriteActions.refreshAfterApproval) {
        window.WriteActions.refreshAfterApproval();
      }
      return;
    }
    const msg = (resp && resp.error && resp.error.message) || 'Metadata update blocked.';
    if (status) status.textContent = msg;
  } catch (err) {
    if (status) status.textContent = `Metadata update error: ${err.message}`;
  }
}

function _bindMetadataEditControls(data, body) {
  const openBtn = body.querySelector('[data-metadata-edit-open]');
  const drawer = body.querySelector('[data-metadata-edit-drawer]');
  if (!openBtn || !drawer) return;
  openBtn.addEventListener('click', () => {
    drawer.style.display = 'block';
    openBtn.style.display = 'none';
    _loadMetadataEditModel(data, body);
  });
  const cancelBtn = body.querySelector('[data-metadata-edit-cancel]');
  if (cancelBtn) {
    cancelBtn.addEventListener('click', () => {
      drawer.style.display = 'none';
      openBtn.style.display = '';
    });
  }
  const refreshBtn = body.querySelector('[data-metadata-edit-refresh]');
  if (refreshBtn) refreshBtn.addEventListener('click', () => _loadMetadataEditModel(data, body));
  const saveBtn = body.querySelector('[data-metadata-edit-save]');
  if (saveBtn) saveBtn.addEventListener('click', () => _saveMetadataEdit(data, body));
}

function refreshCurrentMetadata() {
  const body = document.getElementById('inspector-tab-body');
  if (!body || !_currentNodeData || _activeTab !== 'overview') return;
  const drawer = body.querySelector('[data-metadata-edit-drawer]');
  if (drawer && drawer.style.display !== 'none') {
    _loadMetadataEditModel(_currentNodeData, body);
  }
}

async function _hydrateProvenance(data, body) {
  if (data._provenance_loaded || data._provenance_loading) return;
  const path = _nodePath(data);
  const nodeId = _nodeId(data);
  const api = window.pywebview && window.pywebview.api;
  if ((!path && !nodeId) || !api) {
    return;
  }
  data._provenance_loading = true;
  const status = body.querySelector('[data-provenance-status]');
  if (status) status.textContent = 'Checking graph provenance chain...';
  try {
    if (api.get_graph_node_provenance) {
      const resp = await api.get_graph_node_provenance(nodeId, path, 500);
      data.graph_provenance = resp && resp.ok ? resp.data : {
        ok: false,
        provenance_status: 'unavailable',
        error: (resp && resp.error && resp.error.message) || 'graph provenance API unavailable',
      };
      data.provenance = (data.graph_provenance || {}).provenance || data.provenance || {};
    } else if (path && api.get_provenance) {
      const resp = await api.get_provenance(path);
      data.provenance = resp && resp.ok ? resp.data : { ok: false, error: 'provenance API unavailable' };
    }
  } catch (err) {
    data.graph_provenance = { ok: false, provenance_status: 'error', error: err.message || 'graph provenance lookup failed' };
    data.provenance = { ok: false, error: err.message || 'provenance lookup failed' };
  }
  data._provenance_loading = false;
  data._provenance_loaded = true;
  if (_activeTab === 'provenance') body.innerHTML = _renderProvenance(data);
}

// ── Tab renderers ─────────────────────────────────────────────────────────────

/**
 * Build the compact metadata card HTML (synchronous, no API call).
 * Returns a full overview shell with a skeleton content area.
 */
function _buildMetadataCard(data) {
  const n = _selectedNode(data);
  const props = _nodeProps(data);
  const tags = Array.isArray(n.tags) ? n.tags : (n.tags ? [n.tags] : []);
  const tagChips = tags.map(t => `<span class="meta-tag">${_esc(t)}</span>`).join('');

  const metaFields = [
    n.node_type   && `<div class="meta-field"><span class="meta-label">Type</span><span class="meta-value">${_esc(n.node_type)}</span></div>`,
    n.node_family && `<div class="meta-field"><span class="meta-label">Family</span><span class="meta-value">${_esc(n.node_family)}</span></div>`,
    (n.domain || props.domain) && `<div class="meta-field"><span class="meta-label">Domain</span><span class="meta-value">${_esc(n.domain || props.domain)}</span></div>`,
    n.confidence  && `<div class="meta-field"><span class="meta-label">Confidence</span><span class="meta-value">${_esc(n.confidence)}</span></div>`,
    (n.modified || n.last_modified || props.modified) && `<div class="meta-field"><span class="meta-label">Modified</span><span class="meta-value">${_esc(n.modified || n.last_modified || props.modified)}</span></div>`,
    _nodePath(data) && `<div class="meta-field meta-field--full"><span class="meta-label">Path</span><span class="meta-value meta-value--path">${_esc(_nodePath(data))}</span></div>`,
    tagChips       && `<div class="meta-field meta-field--full"><span class="meta-label">Tags</span><span class="meta-tags">${tagChips}</span></div>`,
  ].filter(Boolean).join('');

  const metaCard = metaFields
    ? `<div class="node-metadata-card">${metaFields}</div>`
    : '';

  // Content area starts with loading skeleton; _loadOverviewContent replaces it
  const contentArea = `<div id="node-content-area" class="node-content-area">
    <div class="panel-loading">Loading content…</div>
  </div>`;

  const editShell = GRAPH_INSPECTOR_METADATA_EDIT_ENABLED ? _renderMetadataEditShell(data) : '';
  return metaCard + contentArea + editShell;
}

/**
 * Async: fetches full file content and renders markdown into #node-content-area.
 * Falls back to source_excerpt if get_node_full_content is unavailable or fails.
 */
async function _loadOverviewContent(data, body) {
  const area = body.querySelector('#node-content-area');
  if (!area) return;

  const nodeId = _nodeId(data);
  const fallbackText = (data.source_excerpt || {}).text || '';

  // No API bridge available – use 4KB excerpt only
  if (!window.pywebview || !window.pywebview.api || !window.pywebview.api.get_node_full_content) {
    _renderContentIntoArea(area, fallbackText, false);
    return;
  }

  try {
    const resp = await window.pywebview.api.get_node_full_content(nodeId);
    if (resp && resp.ok && resp.data && resp.data.available && resp.data.text) {
      _renderContentIntoArea(area, resp.data.text, resp.data.truncated);
    } else {
      // Node has no file path or file not found — use excerpt
      _renderContentIntoArea(area, fallbackText, false);
    }
  } catch (err) {
    _renderContentIntoArea(area, fallbackText, false);
  }
}

function _renderContentIntoArea(area, text, truncated) {
  if (!text) {
    area.innerHTML = '<div class="inspector-empty-tab">No content available.</div>';
    return;
  }

  let html = '';
  if (window.MarkdownRenderer) {
    html = window.MarkdownRenderer.render(text);
  } else {
    html = `<pre>${_esc(text)}</pre>`;
  }

  const notice = truncated
    ? '<div class="truncation-notice">Showing first 32 KB — open in editor for full content.</div>'
    : '';

  area.innerHTML = notice + `<div class="node-content-rendered">${html}</div>`;

  if (window.MarkdownRenderer) {
    const rendered = area.querySelector('.node-content-rendered');
    if (rendered) {
      window.MarkdownRenderer.wireAll(rendered, _openWikilinkTarget);
    }
  }
}

/**
 * Navigate to a node referenced by a [[WikiLink]] target string.
 * Searches the live graph data (_graphAllNodes) for a label/path match.
 */
function _openWikilinkTarget(rawTarget) {
  if (!rawTarget) return;
  const target = rawTarget.trim().toLowerCase();

  // Prefer the graph node list exposed by app.js
  const allNodes = window._graphAllNodes || [];
  const match = allNodes.find(n => {
    const label = (n.label || '').toLowerCase();
    const path  = ((n.properties || {}).path || n.path || '').toLowerCase();
    return label === target || path.endsWith(target) || label.replace(/\s+/g, '-') === target.replace(/\s+/g, '-');
  });

  if (match) {
    openNodeTab(match, { source: 'wikilink', navigate: true });
    // Switch to Node Inspector panel
    if (typeof window.showPanel === 'function') window.showPanel('node-inspector');
  } else {
    // Soft toast
    _showToast(`Node not found: "${rawTarget}"`);
  }
}

function _showToast(msg) {
  const old = document.getElementById('_inspector-toast');
  if (old) old.remove();
  const toast = document.createElement('div');
  toast.id = '_inspector-toast';
  toast.className = 'inspector-toast';
  toast.textContent = msg;
  document.body.appendChild(toast);
  setTimeout(() => { toast.classList.add('visible'); }, 10);
  setTimeout(() => { toast.classList.remove('visible'); setTimeout(() => toast.remove(), 300); }, 2500);
}

function _renderRelations(data) {
  const ctx = data.edge_context || {};
  const edges = data.relations || data.edges || [];
  const maxRelations = _inspectorSettings.max_relation_display || 50;

  if (ctx.incoming_edges || ctx.outgoing_edges) {
    function buildEdgeRows(items, getLabel, getId) {
      if (!items || !items.length) return '';
      return items.slice(0, maxRelations).map(e => {
        const label = getLabel(e);
        const nid = getId(e);
        const cls = nid ? 'inspector-edge-row clickable-row' : 'inspector-edge-row';
        const idAttr = nid ? ` data-node-id="${_esc(nid)}" data-node-label="${_esc(label)}"` : '';
        return `<div class="${cls}"${idAttr}>` +
          `<span class="inspector-edge-relation">${_esc(e.relation || '')}</span>` +
          `<span class="inspector-edge-target">${_esc(label)}</span>` +
          `</div>`;
      }).join('');
    }

    function contextGroup(items, label, getLabel, getId) {
      if (!items || !items.length) return '';
      const rows = buildEdgeRows(items, getLabel, getId);
      return `<div class="inspector-edge-group">` +
        `<div class="inspector-edge-group-label">${_esc(label)}</div>${rows}</div>`;
    }

    const outgoing = contextGroup(
      ctx.outgoing_edges, 'Links to',
      e => (e.properties && e.properties.raw_target) || e.target_label || e.target || '',
      e => e.target || ''
    );
    const incoming = contextGroup(
      ctx.incoming_edges, 'Linked from',
      e => (e.stable_key && e.stable_key.split('#')[0]) || e.source_label || e.source || '',
      e => e.source || ''
    );
    const relationCounts = Object.entries(ctx.relation_counts || {})
      .map(([k, v]) => _row(k, v))
      .join('');

    return (outgoing + incoming + _section('Relation Counts', relationCounts)) ||
      '<div class="inspector-empty-tab">No relations</div>';
  }

  if (!edges.length) return '<div class="inspector-empty-tab">No relations</div>';

  const curNodeId = (data.node || {}).id;
  const incoming = edges.filter(e => e.direction === 'in' || e.target === curNodeId).slice(0, maxRelations);
  const outgoing = edges.filter(e => e.direction === 'out' || e.source === curNodeId).slice(0, maxRelations);
  const other = edges.filter(e => !incoming.includes(e) && !outgoing.includes(e));

  function edgeList(items, label) {
    if (!items.length) return '';
    const rows = items.map(e => {
      const lbl = e.label || e.target || e.source || '';
      const nid = e.target || e.source || '';
      const cls = nid ? 'inspector-edge-row clickable-row' : 'inspector-edge-row';
      const idAttr = nid ? ` data-node-id="${_esc(nid)}" data-node-label="${_esc(lbl)}"` : '';
      return `<div class="${cls}"${idAttr}>` +
        `<span class="inspector-edge-relation">${_esc(e.relation || e.relation_type || '')}</span>` +
        `<span class="inspector-edge-target">${_esc(lbl)}</span>` +
        `</div>`;
    }).join('');
    return `<div class="inspector-edge-group">` +
      `<div class="inspector-edge-group-label">${_esc(label)}</div>${rows}</div>`;
  }

  return edgeList(outgoing, 'Links to') + edgeList(incoming, 'Linked from') + edgeList(other, 'Other');
}

function _wireRelationClicks(body) {
  body.querySelectorAll('.inspector-edge-row.clickable-row').forEach(row => {
    row.addEventListener('click', () => {
      const nid = row.dataset.nodeId;
      if (!nid) return;
      if (typeof window.inspectNode === 'function') {
        window.inspectNode(nid, row.dataset.nodeLabel || nid);
      }
    });
  });
}

function _renderProvenance(data) {
  const node = _selectedNode(data);
  const props = _nodeProps(data);
  const graphProv = data.graph_provenance || {};
  const prov = graphProv.provenance || data.provenance || {};
  const chain = prov.chain || {};
  const sourceExcerpt = data.source_excerpt || {};
  const sourceGraph = data.source_graph || {};
  let html = '';
  const derived = [
    _row('Node Source', node.source || 'derived_from_graph_contract'),
    _row('Stable Key', node.stable_key),
    _row('Path', _nodePath(data)),
    _row('Node Type', node.node_type),
    _row('Confidence', node.confidence),
    _row('Bytes Read', props.bytes_read),
    _row('Truncated', props.truncated),
    _row('Source Graph', sourceGraph.surface),
    _row('Graph Model', sourceGraph.model_version),
  ].join('');
  html += _section('Derived Graph Provenance', derived);

  const excerpt = [
    _row('Excerpt Available', sourceExcerpt.available),
    _row('Excerpt Path', sourceExcerpt.path),
    _row('Excerpt Bytes', sourceExcerpt.bytes_read),
    _row('Excerpt Truncated', sourceExcerpt.truncated),
    _row('Excerpt Reason', sourceExcerpt.reason),
  ].join('');
  if (_inspectorSettings.show_source_excerpt !== false) {
    html += _section('Bounded Source Excerpt', excerpt);
  }

  if (graphProv && Object.keys(graphProv).length) {
    html += renderGraphProvenanceInspector(graphProv);
  }

  if (prov && Object.keys(prov).length) {
    const sidecar = [
      _row('Sidecar Status', graphProv.provenance_status || (prov.ok === true ? 'found' : 'not found')),
      _row('File Name', prov.file_name),
      _row('Sidecar Path', prov.sidecar_path),
      _row('Source Platform', chain.source_platform || prov.source_platform || prov.source),
      _row('Capture Method', chain.capture_method || prov.capture_method),
      _row('Captured At', chain.captured_at || prov.capture_date),
      _row('Origin Kind', chain.origin_kind || prov.origin_kind),
      _row('SHA-256', chain.content_sha256 || prov.sha256),
      _row('Capture ID', chain.capture_id || prov.capture_id),
      _row('Injection Scan', prov.injection_scan || chain.injection_scan),
      _row('Promotion Status', prov.promotion_status || chain.promotion_status),
      _row('Dedup Status', prov.dedup_status),
      _row('Trust State', prov.trust_state),
      _row('Error', prov.error),
    ].join('');
    html += _section('Sidecar Provenance', sidecar);
  } else if (_nodePath(data)) {
    html += '<div class="inspector-provenance-status" data-provenance-status="pending">Checking graph provenance chain...</div>';
  }

  if (prov.extra_metadata && Object.keys(prov.extra_metadata).length) {
    const extras = Object.entries(prov.extra_metadata)
      .map(([k, v]) => _row(k, typeof v === 'object' ? JSON.stringify(v) : v))
      .join('');
    html += _section('Extra Metadata', extras);
  }
  return html || '<div class="inspector-empty-tab">No provenance data</div>';
}

function renderGraphProvenanceInspector(graphProv) {
  const steps = graphProv.chain_steps || [];
  const sections = graphProv.chain_sections || {};
  let html = '';
  html += _section('Graph Provenance Inspector', [
    _row('Status', graphProv.provenance_status),
    _row('Ready', (graphProv.readiness || {}).graph_provenance_inspector_ready),
    _row('Missing Tolerated', (graphProv.readiness || {}).missing_provenance_tolerated),
    _row('Malformed Tolerated', (graphProv.readiness || {}).malformed_sidecar_tolerated),
    _row('Next', (graphProv.readiness || {}).next_recommended_pass),
  ].join(''));
  if (steps.length) {
    html += _section('Graph Provenance Chain', `<div class="graph-provenance-chain">${
      steps.map(step =>
        `<div class="graph-provenance-step graph-provenance-step--${_esc(step.state || 'unknown')}">
          <span class="graph-provenance-step-label">${_esc(step.label || step.id)}</span>
          <span class="graph-provenance-step-state">${_esc(step.state || 'unknown')}</span>
          <span class="graph-provenance-step-summary">${_esc(step.summary || '')}</span>
        </div>`
      ).join('')
    }</div>`);
  }
  html += _section('Capture Chain', _compactRows(sections.capture));
  html += _section('Quarantine Chain', _compactRows(sections.quarantine));
  html += _section('Promotion Chain', _compactRows(sections.promotion));
  html += _section('Generated vs Canonical', _compactRows(sections.content_state));
  html += _section('Dedup / Audit', _compactRows({ ...(sections.dedup || {}), ...(sections.audit || {}) }));
  return `<div class="graph-provenance-inspector" data-graph-provenance-inspector="mounted">${html}</div>`;
}

function _renderTrust(data) {
  const n = _selectedNode(data);
  const props = _nodeProps(data);
  const trust = n.trust_state || props.trust_state || ((data.provenance || {}).trust_state) || 'unknown';
  const TRUST_COLORS = {
    raw: '#94a3b8', quarantined: '#f97316', suggested: '#facc15',
    promoted: '#22c55e', canonical: '#3b82f6', archived: '#6b7280',
    disputed: '#ef4444', generated: '#a855f7',
  };
  const color = TRUST_COLORS[trust] || '#94a3b8';
  let html = `<div class="trust-badge-large" style="background:${color}">${_esc(trust.toUpperCase())}</div>`;
  html += _row('Trust State', trust);
  html += _row('Promoted By', n.promoted_by);
  html += _row('Promotion Date', n.promotion_date);
  html += _row('Disputed Reason', n.disputed_reason);
  const history = n.trust_history || [];
  if (history.length) {
    const rows = history.map(h => `<div class="inspector-row">${_esc(h.date || '')} → ${_esc(h.state || '')}</div>`).join('');
    html += _section('Trust History', rows);
  }
  return html || '<div class="inspector-empty-tab">No trust data</div>';
}

function _renderRuntime(data) {
  const n = _selectedNode(data);
  const props = _nodeProps(data);
  let html = '';
  html += _row('Runtime Node', n.runtime_node || props.runtime_node);
  html += _row('Workflow', n.workflow || props.workflow);
  html += _row('Task ID', n.task_id || props.task_id);
  html += _row('Agent', n.agent || props.agent);
  html += _row('AOR Stage', n.aor_stage || props.aor_stage);
  html += _row('Execution ID', n.execution_id || props.execution_id);
  return _section('Runtime Context', html) || '<div class="inspector-empty-tab">No runtime data</div>';
}

function _renderSource(data) {
  const n = _selectedNode(data);
  const props = _nodeProps(data);
  const prov = data.provenance || {};
  const chain = prov.chain || {};
  let html = '';
  html += _row('Source Platform', chain.source_platform || prov.source_platform || n.source_platform);
  html += _row('Original URL', chain.source_url || prov.original_url || n.original_url);
  html += _row('Domain Hint', chain.domain_hint || prov.domain_hint || n.domain_hint || props.domain);
  html += _row('Project Hint', chain.project_hint || prov.project_hint || n.project_hint || props.project);
  html += _row('Workspace Hint', chain.workspace_hint || prov.workspace_hint || n.workspace_hint);
  html += _row('File Path', _nodePath(data));
  return _section('Source Info', html) || '<div class="inspector-empty-tab">No source data</div>';
}

function _renderDebug(data) {
  const json = JSON.stringify(data, null, 2);
  return `<div class="inspector-debug"><pre>${_esc(json)}</pre></div>`;
}

// ── Exports ───────────────────────────────────────────────────────────────────

// ── Node workspace tab state (multi-node browsing) ───────────────────────────

const INSPECTOR_NODE_TAB_STORAGE_KEY = 'chaseos_node_inspector_bookmarked_tabs_v1';
let _nodeTabs = [];         // { tabId, nodeId, label, path, type, pinned, bookmarked, linkedWithGraph, lastOpenedAt }
let _activeNodeTabId = null;

function _updateTabCountBadge() {
  const el = document.getElementById('node-inspector-tab-count');
  if (!el) return;
  const count = _nodeTabs.length;
  el.textContent = count;
  el.hidden = count === 0;
}

function openNodeTab(nodeLike, options = {}) {
  if (!nodeLike) return;
  const nodeId   = nodeLike.id || nodeLike.nodeId || String(nodeLike);
  const label    = nodeLike.label || nodeLike.title || nodeId;
  const path     = (nodeLike.properties || {}).path || nodeLike.path || '';
  const nodeType = nodeLike.node_type || nodeLike.type || '';
  const tabType  = nodeId.startsWith('markdown:') || nodeType === 'markdown_doc' ? 'markdown_doc' : nodeType;

  // Focus existing tab if already open
  const existing = _nodeTabs.find(t => t.nodeId === nodeId);
  if (existing) {
    _activeNodeTabId = existing.tabId;
    renderNodeTabStrip();
    if (options.navigate) _navigateToNodeInspector(nodeId, label);
    return;
  }

  const tabId = (tabType === 'markdown_doc' ? 'doc:' : 'node:') + nodeId;
  _nodeTabs.push({ tabId, nodeId, label, path, type: tabType,
    pinned: false, bookmarked: false, linkedWithGraph: false,
    lastOpenedAt: new Date().toISOString() });
  _activeNodeTabId = tabId;
  renderNodeTabStrip();
  _updateTabCountBadge();
  if (options.navigate) _navigateToNodeInspector(nodeId, label);
}

function _navigateToNodeInspector(nodeId, label) {
  const tab = _nodeTabs.find(t => t.nodeId === nodeId);
  if (tab && tab.type === 'markdown_doc' && typeof window.openMarkdownDocument === 'function') {
    window.openMarkdownDocument(tab.path || nodeId.replace(/^markdown:/, ''), { skipTab: true });
    return;
  }
  // Call the global inspectNode if available (wired in app.js)
  if (typeof window.inspectNode === 'function') {
    window.inspectNode(nodeId, label);
  }
}

function closeNodeTab(tabId, options = {}) {
  const tab = _nodeTabs.find(t => t.tabId === tabId);
  if (!tab) return;
  if (tab.pinned && !options.force) return; // pinned tabs require force
  _nodeTabs = _nodeTabs.filter(t => t.tabId !== tabId);
  if (_activeNodeTabId === tabId) {
    _activeNodeTabId = _nodeTabs.length ? _nodeTabs[_nodeTabs.length - 1].tabId : null;
    if (_activeNodeTabId) {
      const active = _nodeTabs.find(t => t.tabId === _activeNodeTabId);
      if (active) _navigateToNodeInspector(active.nodeId, active.label);
    } else if (typeof window.clearActiveDocumentState === 'function') {
      // Final tab closed — clear stale document/markdown content.
      window.clearActiveDocumentState();
    }
  }
  _persistBookmarkedTabs();
  renderNodeTabStrip();
  _updateTabCountBadge();
}

function closeOtherNodeTabs(tabId) {
  _nodeTabs = _nodeTabs.filter(t => t.tabId === tabId || t.bookmarked || t.pinned);
  _activeNodeTabId = tabId;
  _persistBookmarkedTabs();
  renderNodeTabStrip();
  _updateTabCountBadge();
}

function closeAllNodeTabs(options = {}) {
  if (options.force) {
    _nodeTabs = [];
  } else {
    _nodeTabs = _nodeTabs.filter(t => t.bookmarked || t.pinned);
  }
  _activeNodeTabId = _nodeTabs.length ? _nodeTabs[0].tabId : null;
  if (!_activeNodeTabId && typeof window.clearActiveDocumentState === 'function') {
    window.clearActiveDocumentState();
  }
  _persistBookmarkedTabs();
  renderNodeTabStrip();
  _updateTabCountBadge();
}

function togglePinNodeTab(tabId) {
  const tab = _nodeTabs.find(t => t.tabId === tabId);
  if (tab) { tab.pinned = !tab.pinned; renderNodeTabStrip(); }
}

function toggleBookmarkNodeTab(tabId) {
  const tab = _nodeTabs.find(t => t.tabId === tabId);
  if (tab) {
    tab.bookmarked = !tab.bookmarked;
    _persistBookmarkedTabs();
    renderNodeTabStrip();
  }
}

function toggleLinkWithGraph(tabId) {
  const tab = _nodeTabs.find(t => t.tabId === tabId);
  if (tab) { tab.linkedWithGraph = !tab.linkedWithGraph; renderNodeTabStrip(); }
}

function getOpenNodeTabCount() { return _nodeTabs.length; }

function _persistBookmarkedTabs() {
  try {
    const toSave = _nodeTabs.filter(t => t.bookmarked).map(t => ({
      tabId: t.tabId, nodeId: t.nodeId, label: t.label, path: t.path,
      type: t.type, bookmarked: true, pinned: false, linkedWithGraph: false,
      lastOpenedAt: t.lastOpenedAt
    }));
    localStorage.setItem(INSPECTOR_NODE_TAB_STORAGE_KEY, JSON.stringify(toSave));
  } catch (_) {}
}

function restoreBookmarkedNodeTabs() {
  try {
    const raw = localStorage.getItem(INSPECTOR_NODE_TAB_STORAGE_KEY);
    if (!raw) return;
    const saved = JSON.parse(raw);
    if (!Array.isArray(saved)) return;
    for (const tab of saved) {
      if (!_nodeTabs.find(t => t.tabId === tab.tabId)) {
        _nodeTabs.push({ ...tab, pinned: false });
      }
    }
    renderNodeTabStrip();
    _updateTabCountBadge();
  } catch (_) {}
}

// ── Durable session: persist ALL open tabs + bookmarks + active to disk so they
// survive closing/reopening ChaseOS (localStorage is not reliably persisted in the
// Qt webview profile). Backed by save_docs_session / load_docs_session. ───────────
let _docsSessionSaveTimer = null;
let _docsSessionRestored = false;
function _persistDocsSession() {
  if (!_docsSessionRestored) return;  // don't overwrite before we've restored
  clearTimeout(_docsSessionSaveTimer);
  _docsSessionSaveTimer = setTimeout(() => {
    try {
      const tabs = _nodeTabs.map(t => ({
        nodeId: t.nodeId, label: t.label, path: t.path, type: t.type,
        pinned: !!t.pinned, bookmarked: !!t.bookmarked,
      }));
      window.pywebview?.api?.save_docs_session?.({ tabs, active_node_id: _activeNodeTabId });
    } catch (_) {}
  }, 450);
}

async function restoreDocsSession() {
  if (_docsSessionRestored) return;
  _docsSessionRestored = true;
  try {
    if (_nodeTabs.length) return;  // tabs already present this session
    const resp = await window.pywebview?.api?.load_docs_session?.();
    const data = (resp && resp.ok && resp.data) ? resp.data : (resp || {});
    const tabs = Array.isArray(data.tabs) ? data.tabs : [];
    if (!tabs.length) return;
    for (const t of tabs) {
      if (!t || !t.nodeId) continue;
      const tabId = (t.type === 'markdown_doc' ? 'doc:' : 'node:') + t.nodeId;
      if (_nodeTabs.find(x => x.tabId === tabId)) continue;
      _nodeTabs.push({
        tabId, nodeId: t.nodeId, label: t.label || t.nodeId, path: t.path || '',
        type: t.type || 'markdown_doc', pinned: !!t.pinned, bookmarked: !!t.bookmarked,
        linkedWithGraph: false, lastOpenedAt: new Date().toISOString(),
      });
    }
    if (!_nodeTabs.length) return;
    _activeNodeTabId = (data.active_node_id && _nodeTabs.find(t => t.tabId === data.active_node_id))
      ? data.active_node_id : _nodeTabs[_nodeTabs.length - 1].tabId;
    renderNodeTabStrip();
    _updateTabCountBadge();
    const active = _nodeTabs.find(t => t.tabId === _activeNodeTabId);
    if (active) _navigateToNodeInspector(active.nodeId, active.label);
  } catch (_) {}
}

function renderNodeTabStrip() {
  _persistDocsSession();  // durable session: open tabs + bookmarks + active
  const strip = document.getElementById('node-tab-strip');
  if (!strip) return;
  if (_nodeTabs.length === 0) { strip.innerHTML = ''; return; }

  strip.innerHTML = _nodeTabs.map(tab => {
    const active = tab.tabId === _activeNodeTabId ? ' active' : '';
    const pinIcon = tab.pinned ? '<span class="tab-pin" title="Pinned">📌</span>' : '';
    const bookIcon = tab.bookmarked ? '<span class="tab-bookmark" title="Bookmarked">🔖</span>' : '';
    return `<div class="node-inspector-tab${active}" data-tab-id="${_esc(tab.tabId)}" title="${_esc(tab.label)}">
      ${pinIcon}${bookIcon}
      <span class="tab-label">${_esc(tab.label)}</span>
      <button class="tab-close" data-close-tab="${_esc(tab.tabId)}" title="Close">×</button>
    </div>`;
  }).join('');

  // Wire tab clicks
  strip.querySelectorAll('.node-inspector-tab').forEach(el => {
    el.addEventListener('click', e => {
      if (e.target.closest('.tab-close')) return;
      const tabId = el.dataset.tabId;
      _activeNodeTabId = tabId;
      const tab = _nodeTabs.find(t => t.tabId === tabId);
      if (tab) _navigateToNodeInspector(tab.nodeId, tab.label);
      renderNodeTabStrip();
    });
    // Right-click context menu
    el.addEventListener('contextmenu', e => {
      e.preventDefault();
      _showTabContextMenu(e, el.dataset.tabId);
    });
  });

  // Wire close buttons
  strip.querySelectorAll('.tab-close').forEach(btn => {
    btn.addEventListener('click', e => {
      e.stopPropagation();
      closeNodeTab(btn.dataset.closeTab);
    });
  });
}

function _showTabContextMenu(e, tabId) {
  // Remove existing menu
  const old = document.getElementById('_tab-ctx-menu');
  if (old) old.remove();

  const tab = _nodeTabs.find(t => t.tabId === tabId);
  if (!tab) return;

  const menu = document.createElement('div');
  menu.id = '_tab-ctx-menu';
  menu.className = 'node-action-menu';
  menu.style.cssText = `position:fixed;visibility:hidden;z-index:10000;`;

  const docActions = window.ChaseDocsInspectorActions || {};
  const isMarkdownDoc = tab.type === 'markdown_doc';
  const items = isMarkdownDoc ? [
    { label: 'Close', action: () => closeNodeTab(tabId) },
    { label: 'Close others', action: () => closeOtherNodeTabs(tabId) },
    { label: 'Close all', action: () => closeAllNodeTabs() },
    null,
    { label: tab.pinned ? 'Unpin' : 'Pin', action: () => togglePinNodeTab(tabId) },
    { label: tab.bookmarked ? 'Remove bookmark' : 'Bookmark', action: () => toggleBookmarkNodeTab(tabId) },
    { label: 'View backlinks', action: () => docActions.viewBacklinks && docActions.viewBacklinks() },
    { label: 'View links', action: () => docActions.viewLinks && docActions.viewLinks() },
    { label: 'Reading view', action: () => docActions.setMode && docActions.setMode('reading') },
    { label: 'Edit (live preview)', action: () => docActions.setMode && docActions.setMode('edit') },
    { label: 'Source mode', action: () => docActions.setMode && docActions.setMode('source') },
    null,
    { label: 'Rename…', action: () => docActions.renameActiveDocument && docActions.renameActiveDocument() },
    { label: 'Move file to…', action: () => docActions.moveActiveDocument && docActions.moveActiveDocument() },
    { label: 'Add file property', action: () => docActions.addProperty && docActions.addProperty() },
    { label: 'Export to PDF', action: () => docActions.exportToPdf && docActions.exportToPdf() },
    null,
    { label: 'Find…', action: () => docActions.find && docActions.find() },
    { label: 'Replace…', action: () => docActions.replace && docActions.replace() },
    null,
    { label: 'Copy path', action: () => docActions.copyPath && docActions.copyPath() },
    { label: 'Copy wiki link', action: () => docActions.copyWikiLink && docActions.copyWikiLink() },
    { label: 'Copy markdown link', action: () => docActions.copyMarkdownLink && docActions.copyMarkdownLink() },
    { label: 'Reveal in file explorer', action: () => docActions.revealInFileTree && docActions.revealInFileTree() },
    { label: 'Open in default app', action: () => docActions.openInDefaultApp && docActions.openInDefaultApp() },
    { label: 'Show in system explorer', action: () => docActions.showInSystemExplorer && docActions.showInSystemExplorer() },
    null,
    { label: 'Delete file', disabled: true, destructive: true, action: () => {} },
  ] : [
    { label: 'Close',          action: () => closeNodeTab(tabId) },
    { label: 'Close others',   action: () => closeOtherNodeTabs(tabId) },
    { label: 'Close all',      action: () => closeAllNodeTabs() },
    null, // separator
    { label: tab.pinned ? 'Unpin' : 'Pin',
      action: () => togglePinNodeTab(tabId) },
    { label: tab.bookmarked ? 'Remove bookmark' : 'Bookmark',
      action: () => toggleBookmarkNodeTab(tabId) },
    { label: tab.linkedWithGraph ? 'Unlink from graph' : 'Link with graph',
      action: () => toggleLinkWithGraph(tabId) },
    null,
    { label: 'Open in File Explorer', action: () => {
        if (window.pywebview && tab.nodeId) {
          if (tab.type === 'markdown_doc' && window.pywebview.api.reveal_markdown_document) {
            window.pywebview.api.reveal_markdown_document(tab.path || tab.nodeId.replace(/^markdown:/, ''));
          } else {
            window.pywebview.api.reveal_node_in_file_explorer(tab.nodeId);
          }
        }
      }
    },
  ];

  // Append buttons directly so their click listeners are preserved.
  // (Previously this cloned a group via cloneNode(true), which strips listeners
  // and left every button above the last separator dead.)
  let group = document.createElement('div');
  group.className = 'node-action-menu-group';
  const flush = () => { if (group.childNodes.length) { menu.appendChild(group); group = document.createElement('div'); group.className = 'node-action-menu-group'; } };
  items.forEach(item => {
    if (!item) {
      flush();
      const sep = document.createElement('div');
      sep.className = 'node-action-menu-separator';
      menu.appendChild(sep);
      return;
    }
    const btn = document.createElement('button');
    btn.type = 'button';
    btn.textContent = item.label;
    if (item.disabled) btn.disabled = true;
    if (item.destructive) btn.classList.add('destructive');
    if (!item.disabled) btn.addEventListener('click', () => { menu.remove(); try { item.action(); } catch (err) { console.error('tab menu action failed', err); } });
    group.appendChild(btn);
  });
  flush();
  document.body.appendChild(menu);
  if (typeof window._positionContextMenu === 'function') {
    window._positionContextMenu(menu, e.clientX, e.clientY);
  } else {
    menu.style.left = e.clientX + 'px'; menu.style.top = e.clientY + 'px'; menu.style.visibility = 'visible';
  }

  const dismiss = () => { menu.remove(); document.removeEventListener('click', dismiss); document.removeEventListener('keydown', onKey); };
  const onKey = ev => { if (ev.key === 'Escape') dismiss(); };
  setTimeout(() => { document.addEventListener('click', dismiss); document.addEventListener('keydown', onKey); }, 0);
}

window.InspectorTabs = {
  INSPECTOR_TABS,
  setInspectorSettings,
  renderTabHeader,
  renderTabContent,
  refreshCurrentMetadata,
  // Node workspace tab API
  openNodeTab,
  closeNodeTab,
  closeOtherNodeTabs,
  closeAllNodeTabs,
  togglePinNodeTab,
  toggleBookmarkNodeTab,
  toggleLinkWithGraph,
  getOpenNodeTabCount,
  restoreBookmarkedNodeTabs,
  restoreDocsSession,
  renderNodeTabStrip,
  get activeTab() { return _activeTab; },
  set activeTab(id) { _activeTab = id; },
  get activeNodeTabId() { return _activeNodeTabId; },
};
