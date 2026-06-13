/**
 * graphStyles.js — Class-based Cytoscape stylesheet builder.
 *
 * Driven by the graph style registry (from api.get_graph_style_registry()).
 * Assigns CSS class strings to nodes/edges; builds the Cytoscape stylesheet.
 * No inline per-element styles for family/trust — only class assignments.
 */

'use strict';

// Compatibility token for static QA: data(display_label)

// ── Registry cache ────────────────────────────────────────────────────────────

let _registry = null;
let _settings = null;

function setStyleRegistry(registry) {
  _registry = registry;
}

function setStyleSettings(settings) {
  _settings = settings;
}

function getRegistry() {
  return _registry || {};
}

function getSettings() {
  return _settings || {};
}

// ── Class name helpers ─────────────────────────────────────────────────────────

/**
 * Returns the CSS class string for a node element.
 * e.g. "node node--knowledge trust--canonical"
 */
function nodeClasses(nodeData) {
  const reg = getRegistry();
  const nodeType = nodeData.node_type || '';
  const nodeTypeMap = reg.node_type_to_family || {};
  const family = nodeTypeMap[nodeType] || nodeData.node_family || 'entity_object';
  const trustState = nodeData.trust_state || 'raw';
  const generatedState = String(nodeData.generated_state || '').toLowerCase();
  const canonicalState = String(nodeData.canonical_state || '').toLowerCase();
  const generated = nodeData.generated === true
    || nodeData.generated_origin === true
    || trustState === 'generated'
    || family === 'generated_artifact'
    || generatedState.includes('generated')
    || generatedState === 'ai'
    || generatedState === 'ai_origin';
  const canonical = nodeData.canonical === true
    || nodeData.canonical_state === true
    || trustState === 'canonical'
    || canonicalState === 'canonical'
    || canonicalState === 'active'
    || canonicalState === 'authoritative';
  const provenance = nodeData.provenance_state || 'unknown';
  return [
    'node',
    `node--${_cssClassPart(family)}`,
    `trust--${_cssClassPart(trustState)}`,
    generated ? 'generated--true content--generated' : 'generated--false',
    canonical ? 'canonical--true content--canonical' : 'canonical--false',
    `provenance--${_cssClassPart(provenance)}`,
  ].join(' ');
}

/**
 * Returns the CSS class string for an edge element.
 * e.g. "edge edge--explicit"
 */
function edgeClasses(edgeData) {
  const layer = normalizeEdgeLayer(edgeData.edge_layer || edgeData.edge_family || edgeData.relation_layer || 'explicit');
  const relation = edgeData.relation ? ` relation--${_cssClassPart(edgeData.relation)}` : '';
  const confidence = edgeData.confidence ? ` confidence--${_cssClassPart(edgeData.confidence)}` : '';
  return `edge edge--${_cssClassPart(layer)}${relation}${confidence}`;
}

function normalizeEdgeLayer(layer) {
  // Canonical export label remains "runtime-action"; CSS class keys use runtime_action.
  const raw = String(layer || 'explicit').trim().toLowerCase().replace(/\s+/g, '_').replace(/-/g, '_');
  if (raw === 'runtime') return 'runtime_action';
  if (raw === 'suggested' || raw === 'semantic') return 'suggested_semantic';
  if (['explicit', 'structural', 'suggested_semantic', 'runtime_action'].includes(raw)) return raw;
  return 'explicit';
}

function _cssClassPart(value) {
  return String(value || 'unknown').trim().toLowerCase().replace(/_/g, '-').replace(/[^a-z0-9-]/g, '-');
}

// ── Cytoscape stylesheet builder ──────────────────────────────────────────────

/**
 * Map Cytoscape shape names from our registry format to Cytoscape's accepted names.
 * Registry uses "round-rectangle"; Cytoscape uses "roundrectangle" etc.
 */
const CY_SHAPE_MAP = {
  'round-rectangle': 'roundrectangle',
  'round-triangle': 'roundtriangle',
  'round-diamond': 'rounddiamond',
  'round-pentagon': 'roundpentagon',
  'round-hexagon': 'roundhexagon',
  'round-heptagon': 'roundheptagon',
  'round-octagon': 'roundoctagon',
  // Cytoscape 3.x accepts tag but not roundtag in the bundled renderer.
  'round-tag': 'tag',
  'cut-rectangle': 'cutrectangle',
  'bottom-round-rectangle': 'bottomroundrectangle',
  'concave-hexagon': 'concavehexagon',
  'right-rhomboid': 'rightrhomboid',
};

function cyShape(registryShape) {
  return CY_SHAPE_MAP[registryShape] || registryShape;
}

const COLORBLIND_SAFE_COLORS = [
  '#0072b2',
  '#e69f00',
  '#009e73',
  '#cc79a7',
  '#56b4e9',
  '#d55e00',
  '#f0e442',
  '#999999',
];

function _colorblindColor(index, fallback) {
  return COLORBLIND_SAFE_COLORS[index % COLORBLIND_SAFE_COLORS.length] || fallback;
}

function _accessibilityEdgeColor(layer, fallback, colorblindSafe, highContrast, index) {
  if (highContrast) {
    if (layer === 'runtime_action') return '#ffffff';
    if (layer === 'suggested_semantic') return '#fbbf24';
    return '#dbeafe';
  }
  return colorblindSafe ? _colorblindColor(index, fallback) : fallback;
}

function _accessibilityTrustColor(trustState, fallback, colorblindSafe, highContrast, index) {
  if (highContrast) {
    if (trustState === 'disputed') return '#ff4d4f';
    if (trustState === 'canonical') return '#60a5fa';
    if (trustState === 'generated') return '#f0abfc';
    return '#f8fafc';
  }
  return colorblindSafe ? _colorblindColor(index, fallback) : fallback;
}

/**
 * Build the full Cytoscape stylesheet from the registry + settings.
 * Returns an array of Cytoscape style objects.
 */
function buildCytoscapeStylesheet() {
  const reg = getRegistry();
  const settings = getSettings();
  const nodeFamilies = reg.node_families || {};
  const edgeLayers = reg.edge_layers || {};
  const trustStates = reg.trust_states || {};
  const appearance = (settings.appearance) || {};
  const settingsNodeFamilies = (settings.node_families) || {};
  const settingsEdgeLayers = (settings.edge_layers) || {};
  const settingsTrustStates = (settings.trust_states) || {};
  const accessibility = (settings.accessibility) || {};
  const generatedCanonical = (settings.generated_canonical) || {};
  const colorblindSafe = accessibility.colorblind_safe_palette === true || (accessibility.colorblind_mode && accessibility.colorblind_mode !== 'none');
  const highContrast = accessibility.high_contrast === true;
  const reduceMotion = accessibility.motion_reduce === true;
  const largeLabels = accessibility.large_labels === true;
  const shapeFirst = accessibility.shape_first_mode === true;
  const patternFirstTrust = accessibility.pattern_first_trust_rings !== false;

  const baseNodeOpacity = appearance.node_opacity != null ? appearance.node_opacity : 0.92;
  const showBadges = appearance.show_badges !== false;
  const showLabels = appearance.show_labels !== false;
  const labelFontSize = largeLabels ? Math.max(14, appearance.label_font_size || 11) : (appearance.label_font_size || 11);
  const labelMaxLength = appearance.label_max_length || 32;
  const underlayOpacity = highContrast ? 0.34 : (appearance.underlay_opacity != null ? appearance.underlay_opacity : 0.18);
  const edgeOpacityMult = appearance.edge_opacity_multiplier != null ? appearance.edge_opacity_multiplier : 1.0;
  const linkThickness = appearance.link_thickness != null ? appearance.link_thickness : 1.0;
  const arrowheadsEnabled = appearance.arrowheads !== false;
  const sizeByDegree = appearance.node_size_by_degree === true;
  const globalNodeSizeBase = appearance.node_size_base != null ? appearance.node_size_base : 24;
  const runtimeEdgeAnimationEnabled = appearance.animate_runtime_edges !== false;
  const minEdgeWidth = highContrast ? Math.max(2.0, accessibility.min_edge_width || 1.0) : (accessibility.min_edge_width || 1.0);
  const generatedBadgeVisible = generatedCanonical.generated_badge_visible !== false;
  const canonicalBadgeVisible = generatedCanonical.canonical_badge_visible !== false;

  const stylesheet = [];

  // Base node style
  stylesheet.push({
    selector: 'node',
    style: {
      'label': showLabels ? (showBadges ? 'data(rendered_label)' : 'data(rendered_plain_label)') : '',
      'text-valign': 'center',
      'text-halign': 'center',
      'font-size': labelFontSize,
      'font-family': 'Inter, system-ui, sans-serif',
      'color': highContrast ? '#ffffff' : '#e2e8f0',
      'text-outline-color': highContrast ? '#000000' : '#0f172a',
      'text-outline-width': highContrast ? 2.5 : 1.5,
      'text-max-width': largeLabels ? '160px' : '120px',
      'text-wrap': 'ellipsis',
      'width': 28,
      'height': 28,
      'opacity': baseNodeOpacity,
      'z-index': 10,
    },
  });

  // Base edge style
  stylesheet.push({
    selector: 'edge',
    style: {
      'label': '',
      'width': 1.2,
      'line-color': '#475569',
      'target-arrow-color': '#475569',
      'target-arrow-shape': 'triangle',
      'curve-style': 'bezier',
      'font-size': highContrast ? 10 : 9,
      'font-family': 'Inter, system-ui, sans-serif',
      'color': highContrast ? '#ffffff' : '#cbd5e1',
      'text-outline-color': highContrast ? '#000000' : '#0f172a',
      'text-outline-width': highContrast ? 2 : 1,
      'text-rotation': 'autorotate',
      'text-margin-y': -8,
      'opacity': Math.max(highContrast ? 0.72 : 0.35, 0.5 * edgeOpacityMult),
      'z-index': 1,
    },
  });

  stylesheet.push({
    selector: 'node.node--pinned',
    style: {
      'overlay-color': highContrast ? '#ffffff' : '#38bdf8',
      'overlay-opacity': highContrast ? 0.16 : 0.10,
      'border-width': highContrast ? 5 : 4,
    },
  });

  // Per-family node styles
  for (const [family, defaults] of Object.entries(nodeFamilies)) {
    const overrides = settingsNodeFamilies[family] || {};
    const fillColor = highContrast ? '#111827' : (overrides.fill_color || defaults.fill_color);
    const borderColor = highContrast ? '#f8fafc' : (overrides.border_color || defaults.border_color);
    const borderStyle = overrides.border_style || defaults.border_style;
    const borderWidth = Math.max(shapeFirst || highContrast ? 3 : 1, overrides.border_width != null ? overrides.border_width : defaults.border_width);
    const familySizeBase = overrides.size_base != null ? overrides.size_base : defaults.size_base;
    const sizeBase = Math.max(8, familySizeBase + (globalNodeSizeBase - 24));
    const nodeSize = sizeByDegree ? `mapData(degree, 0, 12, ${sizeBase}, ${sizeBase + 18})` : sizeBase;
    const shape = cyShape(overrides.shape || defaults.shape);

    stylesheet.push({
      selector: `node.node--${_cssClassPart(family)}`,
      style: {
        'background-color': fillColor,
        'border-color': borderColor,
        'border-width': borderStyle === 'dashed' ? 0 : borderWidth,
        'shape': shape,
        'width': nodeSize,
        'height': nodeSize,
      },
    });

    // Dashed border simulation via background-image not supported; use border-style directly
    if (borderStyle === 'dashed') {
      stylesheet.push({
        selector: `node.node--${_cssClassPart(family)}`,
        style: {
          'border-width': borderWidth,
          'border-style': 'dashed',
          'border-color': borderColor,
        },
      });
    }
  }

  // Per-layer edge styles
  let edgeIndex = 0;
  for (const [layer, defaults] of Object.entries(edgeLayers)) {
    const normalizedLayer = normalizeEdgeLayer(layer);
    const overrides = settingsEdgeLayers[layer] || settingsEdgeLayers[normalizedLayer] || {};
    const color = _accessibilityEdgeColor(normalizedLayer, overrides.color || defaults.color, colorblindSafe, highContrast, edgeIndex);
    const width = Math.max(minEdgeWidth, (overrides.width != null ? overrides.width : defaults.width) * linkThickness);
    const opacity = Math.min(1.0, Math.max(highContrast ? 0.74 : 0.08, (overrides.opacity != null ? overrides.opacity : defaults.opacity) * edgeOpacityMult));
    const arrowSetting = overrides.arrow || defaults.arrow;
    const arrow = !arrowheadsEnabled || arrowSetting === 'none' ? 'none' : arrowSetting;
    const animationRequested = runtimeEdgeAnimationEnabled && (overrides.animation === true || overrides.animated === true || defaults.animated === true) && !reduceMotion;
    const lineStyle = animationRequested ? 'solid' : (overrides.line_style || defaults.line_style);
    const visible = overrides.visible !== false;
    const labelMode = overrides.label_mode || defaults.label_mode || 'hidden';
    const labelValue = labelMode === 'relation' ? 'data(edge_label_relation)'
      : labelMode === 'layer' ? (defaults.label || normalizedLayer)
      : labelMode === 'confidence' ? 'data(edge_label_confidence)'
      : '';

    stylesheet.push({
      selector: `edge.edge--${_cssClassPart(normalizedLayer)}`,
      style: {
        'label': labelValue,
        'line-color': color,
        'target-arrow-color': color,
        'target-arrow-shape': arrow,
        'line-style': lineStyle,
        'width': width,
        'opacity': visible ? opacity : 0,
        'display': visible ? 'element' : 'none',
      },
    });
    edgeIndex += 1;
  }

  // Trust state underlay rings
  let trustIndex = 0;
  for (const [ts, tsDef] of Object.entries(trustStates)) {
    const overrides = settingsTrustStates[ts] || {};
    const ringColor = _accessibilityTrustColor(ts, overrides.ring_color || tsDef.ring_color, colorblindSafe, highContrast, trustIndex);
    const ringWidth = Math.max(highContrast ? 5 : 1, overrides.ring_width || tsDef.ring_width || 3);
    const ringStyle = overrides.ring_style || tsDef.ring_style || 'solid';

    const trustStyle = {
      'underlay-color': ringColor,
      'underlay-opacity': underlayOpacity,
      'underlay-padding': ringWidth,
      'underlay-shape': 'ellipse',
    };
    if (patternFirstTrust && ringStyle !== 'solid') {
      trustStyle['border-style'] = ringStyle;
    }
    stylesheet.push({
      selector: `node.trust--${_cssClassPart(ts)}`,
      style: trustStyle,
    });
    trustIndex += 1;
  }

  stylesheet.push({
    selector: 'node.generated--true',
    style: {
      'border-style': 'dashed',
      'overlay-color': '#a855f7',
      'overlay-opacity': generatedBadgeVisible ? 0.08 : 0.04,
      'overlay-padding': 3,
    },
  });

  stylesheet.push({
    selector: 'node.canonical--true',
    style: {
      'border-width': 4,
      'border-style': 'double',
      'underlay-opacity': canonicalBadgeVisible ? Math.min(0.34, underlayOpacity + 0.12) : underlayOpacity,
    },
  });

  // Selected node highlight
  stylesheet.push({
    selector: 'node:selected',
    style: {
      'border-width': 3,
      'border-color': '#f8fafc',
      'opacity': 1.0,
    },
  });

  // Dimmed state for filtered-out nodes
  stylesheet.push({
    selector: 'node.dimmed',
    style: {
      'opacity': 0.08,
      'z-index': 0,
    },
  });

  stylesheet.push({
    selector: 'edge.dimmed',
    style: {
      'opacity': 0.04,
      'z-index': 0,
    },
  });

  stylesheet.push({
    selector: 'edge.visual-link-pending, edge.visual-link-approved, edge.visual-link-executing',
    style: {
      'line-style': 'dashed',
      'opacity': 0.72,
      'width': 2.2,
      'z-index': 3,
    },
  });

  stylesheet.push({
    selector: 'edge.visual-link-execution_failed',
    style: {
      'line-style': 'dotted',
      'line-color': '#ef4444',
      'target-arrow-color': '#ef4444',
      'opacity': 0.65,
      'z-index': 3,
    },
  });

  // Highlighted (search match)
  stylesheet.push({
    selector: 'node.highlighted',
    style: {
      'border-width': 2,
      'border-color': '#fbbf24',
      'opacity': 1.0,
    },
  });

  return stylesheet;
}

// ── Exports ───────────────────────────────────────────────────────────────────

window.GraphStyles = {
  setStyleRegistry,
  setStyleSettings,
  getRegistry,
  getSettings,
  nodeClasses,
  edgeClasses,
  normalizeEdgeLayer,
  buildCytoscapeStylesheet,
};
