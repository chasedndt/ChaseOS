/**
 * graphFilters.js - semantic graph filter UI helpers.
 *
 * UI-local only. Does not call the filesystem, StudioAPI write methods,
 * providers, connectors, workflows, or approval execution.
 */

'use strict';

let _lastChipRemoveHandler = null;
let _lastFilterRuleSaveHandler = null;

function _escHtml(str) {
  return String(str ?? '')
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;');
}

function _escAttr(str) {
  return String(str ?? '').replace(/'/g, '&#39;').replace(/"/g, '&quot;');
}

function _label(id) {
  return String(id || '').replace(/_/g, ' ').replace(/-/g, ' ').replace(/\b\w/g, ch => ch.toUpperCase());
}

function _itemId(item) {
  return typeof item === 'string' ? item : (item.id || item.edge_layer || item.value || 'unknown');
}

function _normalizeEdgeLayer(layer) {
  if (window.GraphStyles && window.GraphStyles.normalizeEdgeLayer) {
    return window.GraphStyles.normalizeEdgeLayer(layer);
  }
  const raw = String(layer || 'explicit').trim().toLowerCase().replace(/\s+/g, '_').replace(/-/g, '_');
  if (raw === 'runtime') return 'runtime_action';
  if (raw === 'suggested' || raw === 'semantic') return 'suggested_semantic';
  if (['explicit', 'structural', 'suggested_semantic', 'runtime_action'].includes(raw)) return raw;
  return 'explicit';
}

function _sourceClassFromPath(path) {
  const value = String(path || '').toLowerCase();
  if (!value) return 'unknown';
  if (value.includes('/07_logs/') || value.includes('\\07_logs\\')) return 'log';
  if (value.includes('/99_archive/') || value.includes('\\99_archive\\')) return 'archive';
  if (value.includes('/06_agents/') || value.includes('\\06_agents\\')) return 'agent-control';
  if (value.includes('/01_projects/') || value.includes('\\01_projects\\')) return 'project';
  if (value.startsWith('http://') || value.startsWith('https://')) return 'external';
  return 'markdown';
}

function _valueLegend(nodes, keyFn) {
  const counts = new Map();
  (nodes || []).forEach(node => {
    const data = node.data || node;
    const id = keyFn(data) || 'unknown';
    counts.set(id, (counts.get(id) || 0) + 1);
  });
  return Array.from(counts.entries())
    .sort((a, b) => String(a[0]).localeCompare(String(b[0])))
    .map(([id, count]) => ({ id, count }));
}

function _generatedCanonicalCategories(data) {
  const generatedState = String(data.generated_state || '').toLowerCase();
  const canonicalState = String(data.canonical_state || '').toLowerCase();
  const isGenerated = data.generated_origin === true
    || data.generated === true
    || generatedState.includes('generated')
    || data.trust_state === 'generated'
    || data.node_family === 'generated_artifact';
  const isCanonical = data.canonical === true
    || data.canonical_state === true
    || canonicalState === 'canonical'
    || canonicalState === 'active';
  return [
    isGenerated ? 'generated' : 'human-authored',
    isCanonical ? 'canonical' : 'non-canonical',
  ];
}

function _warningCategories(data) {
  const warnings = Array.isArray(data.warnings) ? data.warnings : [];
  const provenance = String(data.provenance_state || '').toLowerCase();
  const cats = [];
  if (warnings.length) cats.push('has-warnings');
  if (!provenance || ['missing', 'incomplete', 'unknown'].includes(provenance)) cats.push('missing-provenance');
  if (!cats.length) cats.push('clean');
  return cats;
}

function _confidenceCategory(data) {
  const raw = String(data.confidence || data.confidence_score || '').toLowerCase();
  const numeric = parseFloat(raw);
  if (Number.isFinite(numeric)) {
    if (numeric >= 0.8) return 'high';
    if (numeric >= 0.5) return 'medium';
    return 'low';
  }
  if (['verified', 'extracted', 'high'].includes(raw)) return 'high';
  if (['inferred', 'medium'].includes(raw)) return 'medium';
  if (['suggested', 'low'].includes(raw)) return 'low';
  return raw || 'unknown';
}

function _statusCategory(data) {
  return String(data.status || data.state || data.workflow_status || data.canonical_state || 'unknown').toLowerCase().replace(/\s+/g, '-');
}

function _recencyCategory(data) {
  const raw = data.modified_at || data.modified || data.last_modified || data.created || data.creation_date || '';
  const timestamp = Date.parse(raw);
  if (!Number.isFinite(timestamp)) return 'undated';
  const ageDays = (Date.now() - timestamp) / 86400000;
  if (ageDays <= 7) return 'last-7-days';
  if (ageDays <= 30) return 'last-30-days';
  if (ageDays <= 180) return 'last-180-days';
  return 'older';
}

function resetFilterState(state, sources) {
  state.nodeTypes = new Set((sources.nodeTypes || []).map(_itemId));
  state.nodeFamilies = new Set((sources.nodeFamilies || []).map(_itemId));
  state.nodeSubtypes = new Set((sources.nodeSubtypes || []).map(_itemId));
  state.trustStates = new Set((sources.trustStates || []).map(_itemId));
  state.domains = new Set((sources.domains || []).map(_itemId));
  state.projects = new Set((sources.projects || []).map(_itemId));
  state.sourceClasses = new Set((sources.sourceClasses || []).map(_itemId));
  state.confidence = new Set((sources.confidence || []).map(_itemId));
  state.statuses = new Set((sources.statuses || []).map(_itemId));
  state.recency = new Set((sources.recency || []).map(_itemId));
  state.relations = new Set((sources.relations || []).map(_itemId));
  state.edgeLayers = new Set((sources.edgeLayers || []).map(item => _normalizeEdgeLayer(_itemId(item))));
  state.generatedCanonical = new Set(['generated', 'canonical', 'human-authored', 'non-canonical']);
  state.warnings = new Set(['has-warnings', 'missing-provenance', 'clean']);
  state._filterDefaults = {
    nodeTypes: new Set(state.nodeTypes),
    nodeFamilies: new Set(state.nodeFamilies),
    nodeSubtypes: new Set(state.nodeSubtypes),
    trustStates: new Set(state.trustStates),
    domains: new Set(state.domains),
    projects: new Set(state.projects),
    sourceClasses: new Set(state.sourceClasses),
    confidence: new Set(state.confidence),
    statuses: new Set(state.statuses),
    recency: new Set(state.recency),
    relations: new Set(state.relations),
    edgeLayers: new Set(state.edgeLayers),
    generatedCanonical: new Set(state.generatedCanonical),
    warnings: new Set(state.warnings),
  };
  state.query = state.query || '';
}

function renderFilterGroup(containerId, values, activeSet, prefix, onChange) {
  const container = document.getElementById(containerId);
  if (!container) return;
  container.innerHTML = (values || []).map(item => {
    const id = _itemId(item);
    const count = typeof item === 'string' ? null : item.count;
    const inputId = `${prefix}-${String(id).replace(/[^a-zA-Z0-9_-]/g, '-')}`;
    activeSet.add(prefix === 'edge-layer' ? _normalizeEdgeLayer(id) : id);
    return (
      `<label class="filter-option" for="${_escAttr(inputId)}">` +
      `<input id="${_escAttr(inputId)}" type="checkbox" data-filter-kind="${_escAttr(prefix)}" data-filter-value="${_escAttr(id)}" checked>` +
      `<span>${_escHtml(_label(id))}${count === null ? '' : ' (' + _escHtml(String(count)) + ')'}</span>` +
      `</label>`
    );
  }).join('');

  container.querySelectorAll('[data-filter-kind]').forEach(input => {
    input.addEventListener('click', evt => {
      if (evt.shiftKey) {
        container.querySelectorAll('[data-filter-kind]').forEach(other => { other.checked = other === input; });
      }
      if (evt.altKey) {
        input.checked = false;
      }
    });
    input.addEventListener('change', evt => onChange(evt.target));
  });
}

function renderActiveFilterChips(state, onRemove, onSaveRule) {
  if (typeof onRemove === 'function') {
    _lastChipRemoveHandler = onRemove;
  }
  if (typeof onSaveRule === 'function') {
    _lastFilterRuleSaveHandler = onSaveRule;
  }
  const bar = document.getElementById('graph-active-filters');
  if (!bar) return;
  const chips = [];
  const defaults = state._filterDefaults || {};
  const sameSet = (a, b) => a && b && a.size === b.size && Array.from(a).every(value => b.has(value));
  const addChip = (kind, value, action, label) => {
    chips.push(`<button class="active-filter-chip" data-filter-kind="${_escAttr(kind)}" data-filter-value="${_escAttr(value)}" data-filter-action="${_escAttr(action || 'remove')}">${_escHtml(label || _label(value))}</button>`);
  };
  const addDeltaChips = (kind, active, defaultSet) => {
    if (!active || !defaultSet || sameSet(active, defaultSet)) return;
    const hidden = Array.from(defaultSet).filter(value => !active.has(value));
    const added = Array.from(active).filter(value => !defaultSet.has(value));
    if (hidden.length && hidden.length <= 12) {
      hidden.forEach(value => addChip(kind, value, 'restore', `Hidden: ${_label(value)}`));
    } else if (hidden.length) {
      addChip(kind, '__all__', 'reset-group', `${_label(kind)} filtered (${active.size}/${defaultSet.size})`);
    }
    added.forEach(value => addChip(kind, value, 'remove', `Only: ${_label(value)}`));
  };
  if (state.query) addChip('query', state.query, 'clear-query', `Search: ${state.query}`);
  addDeltaChips('node-type', state.nodeTypes, defaults.nodeTypes);
  addDeltaChips('node-family', state.nodeFamilies, defaults.nodeFamilies);
  addDeltaChips('node-subtype', state.nodeSubtypes, defaults.nodeSubtypes);
  addDeltaChips('trust-state', state.trustStates, defaults.trustStates);
  addDeltaChips('domain', state.domains, defaults.domains);
  addDeltaChips('project', state.projects, defaults.projects);
  addDeltaChips('source-class', state.sourceClasses, defaults.sourceClasses);
  addDeltaChips('confidence', state.confidence, defaults.confidence);
  addDeltaChips('status', state.statuses, defaults.statuses);
  addDeltaChips('recency', state.recency, defaults.recency);
  addDeltaChips('relation', state.relations, defaults.relations);
  addDeltaChips('edge-layer', state.edgeLayers, defaults.edgeLayers);
  addDeltaChips('generated-canonical', state.generatedCanonical, defaults.generatedCanonical);
  addDeltaChips('warning', state.warnings, defaults.warnings);
  bar.innerHTML = chips.slice(0, 24).join('');
  bar.querySelectorAll('.active-filter-chip').forEach(chip => {
    chip.addEventListener('click', () => {
      if (_lastChipRemoveHandler) {
        _lastChipRemoveHandler(chip.dataset.filterKind, chip.dataset.filterValue, chip.dataset.filterAction);
      }
    });
    chip.addEventListener('contextmenu', evt => {
      evt.preventDefault();
      if (_lastFilterRuleSaveHandler) {
        _lastFilterRuleSaveHandler(chip.dataset.filterKind, chip.dataset.filterValue, state);
      }
    });
  });
}

function renderGraphControls(options) {
  const contract = options.contract || {};
  const state = options.state;
  const viewModel = contract.view_model || {};
  const legend = viewModel.legend || {};
  const nodes = viewModel.nodes || [];
  const nodeTypes = (legend.node_types && legend.node_types.length) ? legend.node_types : _valueLegend(nodes, data => data.node_type || 'unknown');
  const nodeFamilies = (legend.node_families && legend.node_families.length) ? legend.node_families : _valueLegend(nodes, data => data.node_family || data.node_type || 'unknown');
  const nodeSubtypes = _valueLegend(nodes, data => data.node_subtype || data.node_type || 'unknown');
  const domains = options.buildDomainLegend(nodes);
  const projects = _valueLegend(nodes, data => data.project || 'unknown');
  const sourceClasses = _valueLegend(nodes, data => data.source_class || data.source_type || _sourceClassFromPath(data.source_path || data.path));
  const confidence = _valueLegend(nodes, data => _confidenceCategory(data));
  const statuses = _valueLegend(nodes, data => _statusCategory(data));
  const recency = _valueLegend(nodes, data => _recencyCategory(data));
  const relations = legend.relations || [];
  const edgeLayers = legend.edge_layers || Object.entries(options.edgeStyleFamilies || {}).map(([id, style]) => ({ id, ...style }));
  const trustStates = legend.trust_states || Object.keys(options.trustColors || {});
  const generatedCanonical = ['generated', 'human-authored', 'canonical', 'non-canonical'];
  const warnings = ['has-warnings', 'missing-provenance', 'clean'];
  const sources = { nodeTypes, nodeFamilies, nodeSubtypes, trustStates, domains, projects, sourceClasses, confidence, statuses, recency, relations, edgeLayers };

  resetFilterState(state, sources);

  const onChange = el => {
    const kind = el.dataset.filterKind;
    const rawValue = el.dataset.filterValue;
    const value = kind === 'edge-layer' ? _normalizeEdgeLayer(rawValue) : rawValue;
    const targetSet = kind === 'node-type' ? state.nodeTypes
      : kind === 'node-family' ? state.nodeFamilies
      : kind === 'node-subtype' ? state.nodeSubtypes
      : kind === 'trust-state' ? state.trustStates
      : kind === 'domain' ? state.domains
      : kind === 'project' ? state.projects
      : kind === 'source-class' ? state.sourceClasses
      : kind === 'confidence' ? state.confidence
      : kind === 'status' ? state.statuses
      : kind === 'recency' ? state.recency
      : kind === 'edge-layer' ? state.edgeLayers
      : kind === 'generated-canonical' ? state.generatedCanonical
      : kind === 'warning' ? state.warnings
      : state.relations;
    targetSet.clear();
    document.querySelectorAll(`[data-filter-kind="${_escAttr(kind)}"]`).forEach(input => {
      if (!input.checked) return;
      const inputValue = kind === 'edge-layer' ? _normalizeEdgeLayer(input.dataset.filterValue) : input.dataset.filterValue;
      targetSet.add(inputValue);
    });
    renderActiveFilterChips(state, removeFilter, options.saveFilterRule);
    options.applyGraphFilters();
  };

  const filterSetForKind = kind => kind === 'node-type' ? state.nodeTypes
    : kind === 'node-family' ? state.nodeFamilies
    : kind === 'node-subtype' ? state.nodeSubtypes
    : kind === 'trust-state' ? state.trustStates
    : kind === 'domain' ? state.domains
    : kind === 'project' ? state.projects
    : kind === 'source-class' ? state.sourceClasses
    : kind === 'confidence' ? state.confidence
    : kind === 'status' ? state.statuses
    : kind === 'recency' ? state.recency
    : kind === 'edge-layer' ? state.edgeLayers
    : kind === 'generated-canonical' ? state.generatedCanonical
    : kind === 'warning' ? state.warnings
    : kind === 'relation' ? state.relations
    : null;

  const defaultSetForKind = kind => {
    const defaults = state._filterDefaults || {};
    return kind === 'node-type' ? defaults.nodeTypes
    : kind === 'node-family' ? defaults.nodeFamilies
    : kind === 'node-subtype' ? defaults.nodeSubtypes
    : kind === 'trust-state' ? defaults.trustStates
    : kind === 'domain' ? defaults.domains
    : kind === 'project' ? defaults.projects
    : kind === 'source-class' ? defaults.sourceClasses
    : kind === 'confidence' ? defaults.confidence
    : kind === 'status' ? defaults.statuses
    : kind === 'recency' ? defaults.recency
    : kind === 'edge-layer' ? defaults.edgeLayers
    : kind === 'generated-canonical' ? defaults.generatedCanonical
    : kind === 'warning' ? defaults.warnings
    : kind === 'relation' ? defaults.relations
    : null;
  };

  const removeFilter = (kind, value, action) => {
    if (action === 'clear-query') {
      state.query = '';
      const search = document.getElementById('graph-search');
      if (search) search.value = '';
      renderActiveFilterChips(state, removeFilter, options.saveFilterRule);
      options.applyGraphFilters();
      return;
    }
    const targetSet = filterSetForKind(kind);
    if (targetSet && action === 'reset-group') {
      const defaults = defaultSetForKind(kind);
      targetSet.clear();
      if (defaults) defaults.forEach(item => targetSet.add(item));
      document.querySelectorAll(`[data-filter-kind="${_escAttr(kind)}"]`).forEach(input => { input.checked = true; });
      renderActiveFilterChips(state, removeFilter, options.saveFilterRule);
      options.applyGraphFilters();
      return;
    }
    if (targetSet && action === 'restore') {
      const normalizedValue = kind === 'edge-layer' ? _normalizeEdgeLayer(value) : value;
      targetSet.add(normalizedValue);
      document.querySelectorAll(`[data-filter-kind="${_escAttr(kind)}"][data-filter-value="${_escAttr(value)}"]`).forEach(input => { input.checked = true; });
      renderActiveFilterChips(state, removeFilter, options.saveFilterRule);
      options.applyGraphFilters();
      return;
    }
    if (targetSet) targetSet.delete(kind === 'edge-layer' ? _normalizeEdgeLayer(value) : value);
    document.querySelectorAll(`[data-filter-kind="${_escAttr(kind)}"][data-filter-value="${_escAttr(value)}"]`).forEach(input => { input.checked = false; });
    renderActiveFilterChips(state, removeFilter, options.saveFilterRule);
    options.applyGraphFilters();
  };

  renderFilterGroup('node-type-filters', nodeTypes, state.nodeTypes, 'node-type', onChange);
  renderFilterGroup('node-family-filters', nodeFamilies, state.nodeFamilies, 'node-family', onChange);
  renderFilterGroup('node-subtype-filters', nodeSubtypes, state.nodeSubtypes, 'node-subtype', onChange);
  renderFilterGroup('trust-state-filters', trustStates, state.trustStates, 'trust-state', onChange);
  renderFilterGroup('domain-filters', domains, state.domains, 'domain', onChange);
  renderFilterGroup('project-filters', projects, state.projects, 'project', onChange);
  renderFilterGroup('source-class-filters', sourceClasses, state.sourceClasses, 'source-class', onChange);
  renderFilterGroup('confidence-filters', confidence, state.confidence, 'confidence', onChange);
  renderFilterGroup('status-filters', statuses, state.statuses, 'status', onChange);
  renderFilterGroup('recency-filters', recency, state.recency, 'recency', onChange);
  renderFilterGroup('generated-canonical-filters', generatedCanonical, state.generatedCanonical, 'generated-canonical', onChange);
  renderFilterGroup('warning-filters', warnings, state.warnings, 'warning', onChange);
  renderFilterGroup('relation-filters', relations, state.relations, 'relation', onChange);
  renderFilterGroup('edge-layer-filters', edgeLayers, state.edgeLayers, 'edge-layer', onChange);
  renderActiveFilterChips(state, removeFilter, options.saveFilterRule);

  const reset = document.getElementById('graph-filter-reset');
  if (reset) {
    reset.onclick = () => {
      document.querySelectorAll('[data-filter-kind]').forEach(input => { input.checked = true; });
      resetFilterState(state, sources);
      state.query = '';
      const search = document.getElementById('graph-search');
      if (search) search.value = '';
      renderActiveFilterChips(state, removeFilter, options.saveFilterRule);
      options.applyGraphFilters();
    };
  }

  renderLegend({ nodeFamilies, edgeLayers, trustStates, trustColors: options.trustColors });
}

function renderLegend({ nodeFamilies, edgeLayers, trustStates, trustColors }) {
  const legendEl = document.getElementById('graph-legend');
  if (!legendEl) return;

  // Ensure the collapsible structure exists (toggle button + content wrapper).
  // The container itself is a transparent flex column; the legend swatches live
  // in #graph-legend-content which is hidden until #graph-legend has .expanded.
  // Never overwrite the whole container — that would destroy the toggle button.
  let toggleBtn = document.getElementById('graph-legend-toggle');
  let contentEl = document.getElementById('graph-legend-content');
  if (!toggleBtn || !contentEl) {
    legendEl.innerHTML =
      '<button id="graph-legend-toggle" class="graph-legend-toggle" type="button" aria-expanded="false" title="Toggle node/edge legend">Legend ▾</button>' +
      '<div id="graph-legend-content" class="graph-legend-content" aria-hidden="true"></div>';
    toggleBtn = document.getElementById('graph-legend-toggle');
    contentEl = document.getElementById('graph-legend-content');
  }

  const familyItems = (nodeFamilies || []).map(item =>
    `<span class="legend-item legend-node-family" data-legend-edit="node-family" data-legend-id="${_escAttr(item.id)}"><span class="legend-node-swatch" style="background:${_escAttr(item.fill_color || '#64748b')};border-color:${_escAttr(item.border_color || '#94a3b8')}"></span>${_escHtml(item.label || _label(item.id))}</span>`
  ).join('');
  const edgeItems = (edgeLayers || []).map(item => {
    const id = _itemId(item);
    const color = item.color || '#64748b';
    return `<span class="legend-item legend-edge-layer" data-legend-edit="edge-layer" data-legend-id="${_escAttr(id)}"><span class="legend-line ${_escAttr(id)}" style="background:${_escAttr(color)}"></span>${_escHtml(item.layer_label || item.label || _label(id))}</span>`;
  }).join('');
  const trustItems = (trustStates || []).map(item => {
    const id = _itemId(item);
    const color = typeof item === 'string' ? trustColors[id] : (item.ring_color || trustColors[id]);
    const label = typeof item === 'string' ? _label(id) : (item.label || _label(id));
    return `<span class="legend-item legend-trust-state" data-legend-edit="trust-state" data-legend-id="${_escAttr(id)}"><span class="legend-trust-ring" style="border-color:${_escAttr(color || '#94a3b8')}"></span>${_escHtml(label)}</span>`;
  }).join('');
  contentEl.innerHTML =
    `<div class="legend-section" data-legend-section="node-families">${familyItems}</div>` +
    `<div class="legend-section" data-legend-section="edge-layers">${edgeItems}</div>` +
    `<div class="legend-section" data-legend-section="trust-states">${trustItems}</div>`;
  contentEl.querySelectorAll('[data-legend-edit]').forEach(item => {
    item.addEventListener('click', () => {
      if (!window.openGraphSettings) return;
      const kind = item.dataset.legendEdit;
      const id = item.dataset.legendId;
      const tab = kind === 'edge-layer' ? 'edge_layers'
        : kind === 'trust-state' ? 'trust_states'
        : 'node_families';
      window.openGraphSettings({ tab, focusId: id });
    });
  });

  // Wire the collapsible toggle once (idempotent — guard with a dataset flag so
  // repeated renderLegend() calls don't stack duplicate listeners).
  if (toggleBtn && !toggleBtn.dataset.wired) {
    toggleBtn.dataset.wired = '1';
    toggleBtn.addEventListener('click', () => {
      const expanded = legendEl.classList.toggle('expanded');
      toggleBtn.setAttribute('aria-expanded', expanded ? 'true' : 'false');
      toggleBtn.textContent = expanded ? 'Legend ▴' : 'Legend ▾';
      contentEl.setAttribute('aria-hidden', expanded ? 'false' : 'true');
    });
  }
}

function nodeMatchesFilters(node, state) {
  const data = typeof node.data === 'function' ? node.data() : node;
  const query = state.query || '';
  const label = String(data.label || '').toLowerCase();
  const nodeFamily = data.node_family || data.node_type || 'unknown';
  const nodeSubtype = data.node_subtype || data.node_type || 'unknown';
  const project = data.project || 'unknown';
  const sourceClass = data.source_class || data.source_type || _sourceClassFromPath(data.source_path || data.path);
  // Empty Sets = "all pass" (same semantics as the app.js fallback filter).
  // This is critical for Phase 1 rendering, which calls applyGraphFilters() before
  // renderGraphControls() has populated the Sets — without these guards every node
  // fails every .has() check and 0 nodes appear in the graph.
  //
  // Tolerant membership: a node also passes a dimension if its value is NOT part of
  // that dimension's known (deselectable) vocabulary — the seeded default set. The
  // legend/contract vocabularies (node_types, confidence, status, etc.) are built from
  // the Phase 2 full-parse, but the rendered nodes are the Phase 1 fast-scan nodes,
  // which carry a coarser vocabulary (log_audit, build_log, fast_scan, unknown, ...).
  // A value the UI never displayed as a checkbox cannot have been deselected by the
  // user, so it must never be filtered out. Without this the whole graph went blank
  // immediately after "Graph ready" (1500 nodes -> 0).
  const defaults = state._filterDefaults || {};
  const dimPass = (value, activeSet, defaultSet) => {
    if (!activeSet || !activeSet.size) return true;          // empty = all pass
    if (activeSet.has(value)) return true;                   // currently selected
    if (defaultSet && defaultSet.size && !defaultSet.has(value)) return true; // out-of-vocab -> always show
    return false;                                            // known category, deselected
  };
  const generatedCanonicalMatch = !state.generatedCanonical || !state.generatedCanonical.size
    || _generatedCanonicalCategories(data).some(cat => state.generatedCanonical.has(cat));
  const warningMatch = !state.warnings || !state.warnings.size
    || _warningCategories(data).some(cat => state.warnings.has(cat));
  return (!query || label.includes(query))
    && dimPass(data.node_type || 'unknown', state.nodeTypes, defaults.nodeTypes)
    && dimPass(nodeFamily, state.nodeFamilies, defaults.nodeFamilies)
    && dimPass(nodeSubtype, state.nodeSubtypes, defaults.nodeSubtypes)
    && dimPass(data.trust_state || 'raw', state.trustStates, defaults.trustStates)
    && dimPass(data.domain || 'unknown', state.domains, defaults.domains)
    && dimPass(project, state.projects, defaults.projects)
    && dimPass(sourceClass, state.sourceClasses, defaults.sourceClasses)
    && dimPass(_confidenceCategory(data), state.confidence, defaults.confidence)
    && dimPass(_statusCategory(data), state.statuses, defaults.statuses)
    && dimPass(_recencyCategory(data), state.recency, defaults.recency)
    && generatedCanonicalMatch
    && warningMatch;
}

function applyGraphFilters(cy, state) {
  if (!cy) return;
  cy.nodes().forEach(node => {
    node.style('display', nodeMatchesFilters(node, state) ? 'element' : 'none');
  });
  cy.edges().forEach(edge => {
    const relation = edge.data('relation') || '';
    const layer = _normalizeEdgeLayer(edge.data('edge_layer') || edge.data('edge_family') || 'explicit');
    const pendingVisualLink = edge.data('pending_visual_link') === 'true';
    const visible = (pendingVisualLink || state.relations.has(relation))
      && state.edgeLayers.has(layer)
      && edge.source().style('display') !== 'none'
      && edge.target().style('display') !== 'none';
    edge.style('display', visible ? 'element' : 'none');
  });
}

function applyPresetFilters(state, filters) {
  if (!state || !filters) return false;
  const assign = (target, values, normalize) => {
    if (!target || !Array.isArray(values)) return;
    target.clear();
    values.forEach(value => target.add(normalize ? normalize(value) : value));
  };
  assign(state.nodeTypes, filters.node_types);
  assign(state.nodeFamilies, filters.node_families);
  assign(state.nodeSubtypes, filters.node_subtypes);
  assign(state.trustStates, filters.trust_states);
  assign(state.domains, filters.domains);
  assign(state.projects, filters.projects);
  assign(state.sourceClasses, filters.source_classes);
  assign(state.generatedCanonical, filters.generated_canonical);
  assign(state.confidence, filters.confidence);
  assign(state.statuses, filters.statuses);
  assign(state.recency, filters.recency);
  assign(state.relations, filters.relations);
  assign(state.edgeLayers, filters.edge_layers, _normalizeEdgeLayer);
  assign(state.warnings, filters.warnings);
  if (typeof filters.query === 'string') {
    state.query = filters.query;
    const search = document.getElementById('graph-search');
    if (search) search.value = filters.query;
  }
  document.querySelectorAll('[data-filter-kind]').forEach(input => {
    const kind = input.dataset.filterKind;
    const raw = input.dataset.filterValue;
    const value = kind === 'edge-layer' ? _normalizeEdgeLayer(raw) : raw;
    const targetSet = kind === 'node-type' ? state.nodeTypes
      : kind === 'node-family' ? state.nodeFamilies
      : kind === 'node-subtype' ? state.nodeSubtypes
      : kind === 'trust-state' ? state.trustStates
      : kind === 'domain' ? state.domains
      : kind === 'project' ? state.projects
      : kind === 'source-class' ? state.sourceClasses
      : kind === 'generated-canonical' ? state.generatedCanonical
      : kind === 'confidence' ? state.confidence
      : kind === 'status' ? state.statuses
      : kind === 'recency' ? state.recency
      : kind === 'edge-layer' ? state.edgeLayers
      : kind === 'relation' ? state.relations
      : null;
    if (targetSet) input.checked = targetSet.has(value);
  });
  renderActiveFilterChips(state);
  return true;
}

window.GraphFilters = {
  resetFilterState,
  renderFilterGroup,
  renderActiveFilterChips,
  renderGraphControls,
  nodeMatchesFilters,
  applyGraphFilters,
  applyPresetFilters,
};
