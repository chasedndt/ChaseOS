/**
 * settings.js - graph settings modal rendering helpers.
 *
 * UI-local only. The caller owns API save/reset calls. This module only
 * renders editable Studio preference controls and updates the in-memory
 * settings object supplied by app.js.
 */

'use strict';

const GRAPH_SETTINGS_TABS = [
  { id: 'performance', label: '⚡ Performance' },
  { id: 'appearance', label: 'Appearance' },
  { id: 'node_families', label: 'Node Types' },
  { id: 'edge_layers', label: 'Edge Layers' },
  { id: 'trust_states', label: 'Trust States' },
  { id: 'node_scope', label: 'Node Scope' },
  { id: 'layout', label: 'Layout' },
  { id: 'filters', label: 'Filters' },
  { id: 'presets', label: 'Presets' },
  { id: 'accessibility', label: 'Accessibility' },
  { id: 'inspector', label: 'Inspector' },
  { id: 'advanced', label: 'Advanced' },
];

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

function _toggle(label, key, section, tabId, nestedId) {
  const checked = section[key] !== false ? 'checked' : '';
  const nested = nestedId ? ` data-settings-nested="${_escAttr(nestedId)}"` : '';
  return `<label class="settings-row"><span>${_escHtml(label)}</span><input type="checkbox" data-settings-tab="${_escAttr(tabId)}" data-settings-key="${_escAttr(key)}"${nested} ${checked}></label>`;
}

function _number(label, key, section, tabId, min, max, step, nestedId) {
  const val = section[key] != null ? section[key] : '';
  const stepAttr = step ? `step="${step}"` : '';
  const nested = nestedId ? ` data-settings-nested="${_escAttr(nestedId)}"` : '';
  return `<label class="settings-row"><span>${_escHtml(label)}</span><input type="number" min="${min}" max="${max}" ${stepAttr} value="${_escAttr(String(val))}" data-settings-tab="${_escAttr(tabId)}" data-settings-key="${_escAttr(key)}"${nested}></label>`;
}

function _select(label, key, section, tabId, options, nestedId) {
  const val = section[key] || '';
  const nested = nestedId ? ` data-settings-nested="${_escAttr(nestedId)}"` : '';
  const opts = options.map(o => `<option value="${_escAttr(o)}"${o === val ? ' selected' : ''}>${_escHtml(_label(o))}</option>`).join('');
  return `<label class="settings-row"><span>${_escHtml(label)}</span><select data-settings-tab="${_escAttr(tabId)}" data-settings-key="${_escAttr(key)}"${nested}>${opts}</select></label>`;
}

function _color(label, key, section, tabId, fallback, nestedId) {
  const val = section[key] || fallback || '#64748b';
  const nested = nestedId ? ` data-settings-nested="${_escAttr(nestedId)}"` : '';
  return `<label class="settings-row"><span>${_escHtml(label)}</span><input type="color" value="${_escAttr(val)}" data-settings-tab="${_escAttr(tabId)}" data-settings-key="${_escAttr(key)}"${nested}></label>`;
}

function _text(label, key, section, tabId, fallback, nestedId) {
  const val = section[key] != null ? section[key] : (fallback || '');
  const nested = nestedId ? ` data-settings-nested="${_escAttr(nestedId)}"` : '';
  return `<label class="settings-row"><span>${_escHtml(label)}</span><input type="text" value="${_escAttr(String(val))}" data-settings-tab="${_escAttr(tabId)}" data-settings-key="${_escAttr(key)}"${nested}></label>`;
}

function _actionButton(label, action, targetId) {
  const target = targetId ? ` data-settings-target-id="${_escAttr(targetId)}"` : '';
  return `<button type="button" class="settings-action-btn" data-settings-action="${_escAttr(action)}"${target}>${_escHtml(label)}</button>`;
}

function _actionBar(buttons) {
  return `<div class="settings-action-row">${buttons.join('')}</div>`;
}

function renderSettingsTabs({ settings, activeTab, onTabSelect, onInputChange, onAction }) {
  const tabsEl = document.getElementById('settings-tabs');
  const bodyEl = document.getElementById('settings-body');
  if (!tabsEl || !bodyEl) return;
  tabsEl.innerHTML = GRAPH_SETTINGS_TABS.map(t =>
    `<button class="settings-tab-btn${t.id === activeTab ? ' active' : ''}" data-tab="${_escAttr(t.id)}">${_escHtml(t.label)}</button>`
  ).join('');
  tabsEl.querySelectorAll('.settings-tab-btn').forEach(btn => {
    btn.addEventListener('click', () => onTabSelect(btn.dataset.tab));
  });
  renderSettingsTabContent({ tabId: activeTab, settings, onInputChange, onAction });
}

function renderSettingsTabContent({ tabId, settings, onInputChange, onAction }) {
  const bodyEl = document.getElementById('settings-body');
  if (!bodyEl) return;
  const section = settings[tabId] || {};
  const registry = (window.GraphStyles && window.GraphStyles.getRegistry && window.GraphStyles.getRegistry()) || {};
  let html = '<div class="settings-section">';

  if (tabId === 'performance') {
    html += `<div class="settings-note">Choose a quality preset or tune individual renderer settings. Lower quality reduces GPU/CPU load on less powerful hardware. Changes take effect after saving — the graph will reinitialise with the new settings.</div>`;
    html += `<div class="settings-subsection"><div class="settings-subsection-title">Quality Preset</div>`;
    html += _select('Preset', 'quality_preset', section, tabId, ['ultra', 'balanced', 'performance', 'minimal']);
    html += `<div class="settings-note perf-preset-hint" id="perf-preset-description"></div>`;
    html += `</div>`;
    html += `<div class="settings-subsection"><div class="settings-subsection-title">Renderer</div>`;
    html += _number('Device pixel ratio (0 = auto)', 'device_pixel_ratio', section, tabId, 0, 4, 0.5);
    html += _number('Dimensions (2 = flat/fast, 3 = full 3D)', 'num_dimensions', section, tabId, 2, 3, 1);
    html += `</div>`;
    html += `<div class="settings-subsection"><div class="settings-subsection-title">Physics Engine</div>`;
    html += _toggle('Physics enabled (uncheck = static layout)', 'physics_enabled', section, tabId);
    html += _number('Warmup ticks (0 = instant render)', 'warmup_ticks', section, tabId, 0, 500, 10);
    html += _number('Cooldown ticks (–1 = run forever)', 'cooldown_ticks', section, tabId, -1, 5000, 100);
    html += _number('Alpha decay (lower = slower/smoother)', 'd3_alpha_decay', section, tabId, 0.001, 0.5, 0.005);
    html += _number('Velocity decay / damping', 'd3_velocity_decay', section, tabId, 0.05, 0.99, 0.05);
    html += `</div>`;
    html += _actionBar([
      _actionButton('Apply preset: Ultra', 'apply-quality-ultra'),
      _actionButton('Apply preset: Balanced', 'apply-quality-balanced'),
      _actionButton('Apply preset: Performance', 'apply-quality-performance'),
      _actionButton('Apply preset: Minimal', 'apply-quality-minimal'),
    ]);
  } else if (tabId === 'appearance') {
    html += _select('Theme', 'theme', section, tabId, ['system', 'light', 'dark', 'custom']);
    html += _color('Background', 'background_color', section, tabId, '#0f172a');
    html += _toggle('Grid', 'grid', section, tabId);
    html += _toggle('Node labels', 'show_labels', section, tabId);
    html += _number('Label fade threshold', 'label_fade_threshold', section, tabId, 0, 1, 0.05);
    html += _number('Node size base', 'node_size_base', section, tabId, 8, 80, 1);
    html += _toggle('Node size by degree', 'node_size_by_degree', section, tabId);
    html += _number('Link thickness', 'link_thickness', section, tabId, 0.25, 12, 0.25);
    html += _toggle('Arrowheads', 'arrowheads', section, tabId);
    html += _toggle('Mini-map', 'minimap', section, tabId);
  } else if (tabId === 'node_families') {
    html += renderNodeFamilySettings(settings.node_families || {}, registry.node_families || {});
  } else if (tabId === 'edge_layers') {
    html += renderEdgeLayerSettings(settings.edge_layers || {}, registry.edge_layers || {});
  } else if (tabId === 'trust_states') {
    html += renderTrustStateSettings(settings.trust_states || {}, registry.trust_states || {});
  } else if (tabId === 'node_scope') {
    html += _toggle('Files / pages', 'files_pages', section, tabId);
    html += _toggle('Headings', 'headings', section, tabId);
    html += _toggle('Blocks', 'blocks', section, tabId);
    html += _toggle('Tasks', 'tasks', section, tabId);
    html += _toggle('External resources', 'show_external_resources', section, tabId);
    html += _number('Max visible nodes', 'max_nodes', section, tabId, 10, 5000, 50);
    html += _number('Max visible edges', 'max_edges', section, tabId, 10, 15000, 50);
    html += _number('Max visible labels', 'max_labels_visible', section, tabId, 10, 1000, 10);
  } else if (tabId === 'layout') {
    html += _select('Algorithm', 'algorithm', section, tabId, ['cose', 'grid', 'circle', 'concentric', 'breadthfirst', 'random']);
    html += _number('Repel force', 'node_repulsion', section, tabId, 1000, 1000000, 1000);
    html += _number('Link distance', 'ideal_edge_length', section, tabId, 20, 400, 5);
    html += _toggle('Cluster by domain', 'cluster_by_domain', section, tabId);
    html += _toggle('Cluster by project', 'cluster_by_project', section, tabId);
    html += _toggle('Cluster by trust state', 'cluster_by_trust_state', section, tabId);
    html += _number('Local graph depth', 'local_graph_depth', section, tabId, 0, 6, 1);
    html += _number('Focus radius', 'focus_radius', section, tabId, 0, 8, 1);
    html += _actionBar([
      _actionButton('Pin selected node', 'pin-selected-node'),
      _actionButton('Clear pinned nodes', 'clear-pinned-nodes'),
      _actionButton('Reset layout', 'reset-graph-layout'),
    ]);
  } else if (tabId === 'filters') {
    html += '<div class="settings-note">Filter chips are UI-local and saved through graph presets. Supported dimensions: node family, subtype, trust, generated/canonical, domain, project, source class, edge layer, confidence, status, date, warnings, and missing provenance.</div>';
  } else if (tabId === 'presets') {
    html += '<div class="settings-note">Built-in graph workspaces are inspectable presets. User preset files are stored under Studio user settings, never inside the opened vault. Use the preset bar to save or delete user graph views.</div>';
  } else if (tabId === 'accessibility') {
    html += _toggle('High contrast', 'high_contrast', section, tabId);
    html += _toggle('Colorblind-safe palette', 'colorblind_safe_palette', section, tabId);
    html += _select('Colorblind mode', 'colorblind_mode', section, tabId, ['none', 'deuteranopia', 'protanopia', 'tritanopia']);
    html += _toggle('Reduce motion', 'motion_reduce', section, tabId);
    html += _toggle('Large labels', 'large_labels', section, tabId);
    html += _toggle('Shape-first mode', 'shape_first_mode', section, tabId);
    html += _toggle('Pattern-first trust rings', 'pattern_first_trust_rings', section, tabId);
    html += _number('Minimum edge width', 'min_edge_width', section, tabId, 0.25, 12, 0.25);
    html += _toggle('Keyboard navigation', 'keyboard_navigation', section, tabId);
  } else if (tabId === 'inspector') {
    html += _select('Default tab', 'default_tab', section, tabId, ['overview', 'relations', 'provenance', 'trust', 'runtime', 'source', 'debug']);
    html += _toggle('Show provenance tab', 'show_provenance_tab', section, tabId);
    html += _toggle('Show source excerpt', 'show_source_excerpt', section, tabId);
    html += _number('Source excerpt length', 'source_excerpt_length', section, tabId, 0, 10000, 100);
    html += _toggle('Show raw JSON/debug tab', 'show_raw_metadata', section, tabId);
    html += _toggle('Show warnings', 'show_warnings', section, tabId);
    html += _toggle('Show related nodes', 'show_related_nodes', section, tabId);
    html += _toggle('Show relation counts', 'show_relation_counts', section, tabId);
  } else if (tabId === 'advanced') {
    html += '<div class="settings-note">Settings are schema-versioned, atomically written to Studio user state, and do not mutate markdown, node IDs, trust state, provenance, or canonical ChaseOS truth.</div>';
    html += _actionBar([
      _actionButton('Export settings JSON', 'export-settings'),
      _actionButton('Import settings JSON', 'import-settings'),
    ]);
  }

  html += '</div>';
  bodyEl.innerHTML = html;
  bodyEl.querySelectorAll('[data-settings-key]').forEach(input => {
    input.addEventListener('change', () => onInputChange(input));
  });
  bodyEl.querySelectorAll('[data-settings-action]').forEach(btn => {
    btn.addEventListener('click', () => {
      if (typeof onAction === 'function') onAction(btn);
    });
  });
}

function renderNodeFamilySettings(section, families) {
  const headerActions = _actionBar([
    _actionButton('Reset all node styles', 'reset-all-node-styles'),
    _actionButton('Export node style map', 'export-node-style-map'),
  ]);
  return Object.entries(families).map(([family, defaults]) => {
    const cfg = section[family] || {};
    return `<div class="settings-subsection" data-settings-target="${_escAttr(family)}">
      <div class="settings-subtitle">${_escHtml(defaults.label || _label(family))}</div>
      ${_actionBar([
        _actionButton('Reset this type', 'reset-node-family', family),
        _actionButton('Duplicate style', 'duplicate-node-style', family),
        _actionButton('Export style', 'export-node-style', family),
      ])}
      ${_select('Shape', 'shape', { shape: cfg.shape || defaults.shape || 'ellipse' }, 'node_families', ['ellipse','rectangle','round-rectangle','cut-rectangle','barrel','rhomboid','diamond','hexagon','pentagon','octagon','star','tag','vee'], family)}
      ${_color('Fill color', 'fill_color', cfg, 'node_families', defaults.fill_color, family)}
      ${_color('Border color', 'border_color', cfg, 'node_families', defaults.border_color, family)}
      ${_number('Border width', 'border_width', cfg, 'node_families', 0, 12, 1, family)}
      ${_text('Icon / badge', 'badge', cfg, 'node_families', defaults.badge || '', family)}
      ${_text('Label prefix', 'label_prefix', cfg, 'node_families', '', family)}
      ${_text('Label suffix', 'label_suffix', cfg, 'node_families', '', family)}
      ${_number('Default size', 'size_base', cfg, 'node_families', 8, 80, 1, family)}
      ${_toggle('Visible', 'visible', cfg, 'node_families', family)}
      ${_toggle('Show in legend', 'show_in_legend', cfg, 'node_families', family)}
    </div>`;
  }).join('').replace(/^/, headerActions);
}

function renderEdgeLayerSettings(section, layers) {
  return Object.entries(layers).map(([layer, defaults]) => {
    const cfg = section[layer] || {};
    return `<div class="settings-subsection" data-settings-target="${_escAttr(layer)}">
      <div class="settings-subtitle">${_escHtml(defaults.label || _label(layer))}</div>
      ${_toggle('Visible', 'visible', cfg, 'edge_layers', layer)}
      ${_color('Color', 'color', cfg, 'edge_layers', defaults.color, layer)}
      ${_select('Line style', 'line_style', { line_style: cfg.line_style || defaults.line_style || 'solid' }, 'edge_layers', ['solid','dashed','dotted'], layer)}
      ${_number('Width', 'width', cfg, 'edge_layers', 0.25, 12, 0.25, layer)}
      ${_number('Opacity', 'opacity', cfg, 'edge_layers', 0.05, 1, 0.05, layer)}
      ${_select('Arrowhead', 'arrow', { arrow: cfg.arrow || defaults.arrow || 'triangle' }, 'edge_layers', ['triangle','triangle-backcurve','vee','tee','circle','none'], layer)}
      ${_select('Label mode', 'label_mode', { label_mode: cfg.label_mode || 'hidden' }, 'edge_layers', ['hidden','relation','layer','confidence'], layer)}
      ${_toggle('Animation', 'animation', cfg, 'edge_layers', layer)}
      ${_number('Confidence threshold', 'confidence_threshold', cfg, 'edge_layers', 0, 1, 0.05, layer)}
    </div>`;
  }).join('');
}

function renderTrustStateSettings(section, states) {
  return Object.entries(states).map(([trust, defaults]) => {
    const cfg = section[trust] || {};
    return `<div class="settings-subsection" data-settings-target="${_escAttr(trust)}">
      <div class="settings-subtitle">${_escHtml(defaults.label || _label(trust))}</div>
      ${_color('Ring color', 'ring_color', cfg, 'trust_states', defaults.ring_color, trust)}
      ${_number('Ring width', 'ring_width', cfg, 'trust_states', 1, 12, 1, trust)}
      ${_select('Ring style', 'ring_style', { ring_style: cfg.ring_style || defaults.ring_style || 'solid' }, 'trust_states', ['solid','dashed','dotted','double'], trust)}
      ${_text('Badge text', 'badge', cfg, 'trust_states', defaults.badge || '', trust)}
      ${_toggle('Badge visibility', 'badge_visible', cfg, 'trust_states', trust)}
      ${_toggle('Pattern fallback', 'pattern_fallback', cfg, 'trust_states', trust)}
    </div>`;
  }).join('');
}

function applyInputChange(settings, input) {
  const tabId = input.dataset.settingsTab;
  const key = input.dataset.settingsKey;
  const nested = input.dataset.settingsNested;
  let value;
  if (input.type === 'checkbox') value = input.checked;
  else if (input.type === 'number') value = parseFloat(input.value);
  else value = input.value;

  if (nested) {
    if (!settings[tabId]) settings[tabId] = {};
    if (!settings[tabId][nested]) settings[tabId][nested] = {};
    settings[tabId][nested][key] = value;
  } else {
    if (!settings[tabId]) settings[tabId] = {};
    settings[tabId][key] = value;
  }
  return settings;
}

window.GraphSettings = {
  SETTINGS_TABS: GRAPH_SETTINGS_TABS,
  renderSettingsTabs,
  renderSettingsTabContent,
  renderNodeFamilySettings,
  renderEdgeLayerSettings,
  renderTrustStateSettings,
  applyInputChange,
};
