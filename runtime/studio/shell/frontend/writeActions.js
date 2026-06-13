/* ChaseOS Studio - Write Actions (Pass 10AB)
 *
 * Graph create-node plus visual-link proposal flows.
 * All writes route through approval-gated StudioService contracts.
 */
'use strict';

const CREATABLE_NODE_TYPES = [
  { value: 'agent',              label: 'Agent' },
  { value: 'decision',           label: 'Decision' },
  { value: 'domain',             label: 'Domain' },
  { value: 'generated_artifact', label: 'Generated Artifact' },
  { value: 'intake',             label: 'Intake' },
  { value: 'knowledge',          label: 'Knowledge' },
  { value: 'knowledge_doc',      label: 'Knowledge Doc' },
  { value: 'log_audit',          label: 'Log / Audit' },
  { value: 'project',            label: 'Project' },
  { value: 'project_doc',        label: 'Project Doc' },
  { value: 'source',             label: 'Source' },
  { value: 'synthesis',          label: 'Synthesis' },
  { value: 'sop_template',       label: 'SOP Template' },
  { value: 'workflow',           label: 'Workflow' },
];

const VISUAL_LINK_EDGE_LAYERS = [
  { value: 'explicit', label: 'Explicit' },
  { value: 'suggested', label: 'Suggested' },
  { value: 'runtime', label: 'Runtime-Action' },
];

const VISUAL_LINK_RELATIONS = [
  { value: 'related', label: 'Related' },
  { value: 'references', label: 'References' },
  { value: 'supports', label: 'Supports' },
  { value: 'contradicts', label: 'Contradicts' },
  { value: 'depends_on', label: 'Depends On' },
  { value: 'follows', label: 'Follows' },
  { value: 'derived_from', label: 'Derived From' },
  { value: 'same_project', label: 'Same Project' },
  { value: 'runtime_action', label: 'Runtime Action' },
];

let _activeCy = null;
let _contextMenu = null;
let _createModal = null;
let _visualLinkModal = null;
let _writeActionsReady = false;
let _previewTimer = null;
let _visualLinkPreviewTimer = null;
let _domBindingsReady = false;
let _contextNode = null;
let _contextEdge = null;
let _linkSourceNode = null;
let _linkTargetNode = null;
let _dragLinkSource = null;
let _hoverNode = null;
let _lastOverlay = null;

function initWriteActions(graphInstance) {
  _activeCy = graphInstance;
  _contextMenu = document.getElementById('graph-context-menu');
  _createModal = document.getElementById('create-node-modal');
  _visualLinkModal = document.getElementById('visual-link-modal');

  if (!_activeCy || !_contextMenu) return;

  // 3d-force-graph: use onNodeRightClick / onBackgroundRightClick callbacks
  if (typeof _activeCy.onNodeRightClick === 'function') {
    _activeCy.onNodeRightClick((node, event) => {
      _contextNode = _nodePayloadFromPlainNode(node);
      _contextEdge = null;
      _showContextMenu({ x: event.clientX, y: event.clientY });
      event.stopPropagation && event.stopPropagation();
    });
    if (typeof _activeCy.onBackgroundRightClick === 'function') {
      _activeCy.onBackgroundRightClick((event) => {
        _contextNode = null;
        _contextEdge = null;
        _showContextMenu({ x: event.clientX, y: event.clientY });
      });
    }
    return;
  }

  // Cytoscape fallback
  _activeCy.on('cxttap', evt => {
    if (evt.target === _activeCy) {
      _contextNode = null;
      _contextEdge = null;
      _showContextMenu(evt.renderedPosition || { x: 0, y: 0 });
    }
  });

  _activeCy.on('cxttap', 'node', evt => {
    _contextNode = _nodePayloadFromCyNode(evt.target);
    _contextEdge = null;
    _showContextMenu(evt.renderedPosition || { x: 0, y: 0 });
    if (evt.originalEvent && evt.originalEvent.stopPropagation) evt.originalEvent.stopPropagation();
  });

  _activeCy.on('cxttap', 'edge', evt => {
    _contextNode = null;
    _contextEdge = _edgePayloadFromCyEdge(evt.target);
    _showContextMenu(evt.renderedPosition || { x: 0, y: 0 });
    if (evt.originalEvent && evt.originalEvent.stopPropagation) evt.originalEvent.stopPropagation();
  });

  _activeCy.on('mouseover', 'node', evt => {
    _hoverNode = _nodePayloadFromCyNode(evt.target);
  });
  _activeCy.on('mouseout', 'node', evt => {
    const leaving = _nodePayloadFromCyNode(evt.target);
    if (_hoverNode && leaving && _hoverNode.node_id === leaving.node_id) _hoverNode = null;
  });
  _activeCy.on('grab', 'node', evt => {
    const original = evt.originalEvent || {};
    if (original.shiftKey) {
      _dragLinkSource = _nodePayloadFromCyNode(evt.target);
      if (typeof setStatus === 'function') setStatus('Visual link source selected', 'observe');
    }
  });
  _activeCy.on('free', 'node', evt => {
    if (!_dragLinkSource) return;
    const target = _hoverNode || _nodePayloadFromCyNode(evt.target);
    const source = _dragLinkSource;
    _dragLinkSource = null;
    if (target && source && target.node_id && source.node_id && target.node_id !== source.node_id) {
      showVisualLinkModal(source, target);
    }
  });

  _bindDomOnce();
  _writeActionsReady = true;
}

function _bindDomOnce() {
  if (_domBindingsReady) return;
  document.addEventListener('click', _hideContextMenu, true);

  const createBtn = document.getElementById('ctx-create-node');
  if (createBtn) createBtn.addEventListener('click', () => { _hideContextMenu(); showCreateNodeModal(); });

  const customizeNodeBtn = document.getElementById('ctx-customize-node-type');
  if (customizeNodeBtn) customizeNodeBtn.addEventListener('click', () => {
    if (_contextNode && window.openGraphSettings) {
      const family = _contextNode.node_family || _contextNode.node_type || 'knowledge';
      window.openGraphSettings({ tab: 'node_families', focusId: family });
    }
    _hideContextMenu();
  });

  const customizeEdgeBtn = document.getElementById('ctx-customize-edge-layer');
  if (customizeEdgeBtn) customizeEdgeBtn.addEventListener('click', () => {
    if (_contextEdge && window.openGraphSettings) {
      window.openGraphSettings({ tab: 'edge_layers', focusId: _contextEdge.edge_layer || 'explicit' });
    }
    _hideContextMenu();
  });

  const startLinkBtn = document.getElementById('ctx-start-link');
  if (startLinkBtn) startLinkBtn.addEventListener('click', () => {
    if (_contextNode) {
      _linkSourceNode = _contextNode;
      if (typeof setStatus === 'function') setStatus(`Link source: ${_contextNode.label || _contextNode.node_id}`, 'observe');
    }
    _hideContextMenu();
  });

  const finishLinkBtn = document.getElementById('ctx-finish-link');
  if (finishLinkBtn) finishLinkBtn.addEventListener('click', () => {
    if (_linkSourceNode && _contextNode) showVisualLinkModal(_linkSourceNode, _contextNode);
    _hideContextMenu();
  });

  const clearLinkBtn = document.getElementById('ctx-clear-link');
  if (clearLinkBtn) clearLinkBtn.addEventListener('click', () => {
    _linkSourceNode = null;
    _hideContextMenu();
    if (typeof setStatus === 'function') setStatus('Visual link source cleared', 'observe');
  });

  const closeBtn = document.getElementById('create-node-modal-close');
  const cancelBtn = document.getElementById('create-node-cancel-btn');
  const submitBtn = document.getElementById('create-node-submit-btn');
  const titleInput = document.getElementById('create-node-title');
  const typeSelect = document.getElementById('create-node-type');
  const domainInput = document.getElementById('create-node-domain');

  if (closeBtn) closeBtn.addEventListener('click', hideCreateNodeModal);
  if (cancelBtn) cancelBtn.addEventListener('click', hideCreateNodeModal);
  if (_createModal) {
    _createModal.addEventListener('click', evt => {
      if (evt.target === _createModal) hideCreateNodeModal();
    });
  }
  if (submitBtn) submitBtn.addEventListener('click', _submitCreateNode);
  [titleInput, typeSelect, domainInput].forEach(el => {
    if (!el) return;
    const eventName = el.tagName === 'SELECT' ? 'change' : 'input';
    el.addEventListener(eventName, _queueCreatePreview);
  });

  _bindVisualLinkModal();
  _domBindingsReady = true;
}

function _bindVisualLinkModal() {
  if (!_visualLinkModal) return;
  const closeBtn = document.getElementById('visual-link-modal-close');
  const cancelBtn = document.getElementById('visual-link-cancel-btn');
  const submitBtn = document.getElementById('visual-link-submit-btn');
  const layerSelect = document.getElementById('visual-link-edge-layer');
  const relationSelect = document.getElementById('visual-link-relation-type');
  const labelInput = document.getElementById('visual-link-label');
  const evidenceInput = document.getElementById('visual-link-evidence');

  if (closeBtn) closeBtn.addEventListener('click', hideVisualLinkModal);
  if (cancelBtn) cancelBtn.addEventListener('click', hideVisualLinkModal);
  if (_visualLinkModal) {
    _visualLinkModal.addEventListener('click', evt => {
      if (evt.target === _visualLinkModal) hideVisualLinkModal();
    });
  }
  if (submitBtn) submitBtn.addEventListener('click', _submitVisualLink);
  [layerSelect, relationSelect, labelInput, evidenceInput].forEach(el => {
    if (!el) return;
    const eventName = el.tagName === 'SELECT' ? 'change' : 'input';
    el.addEventListener(eventName, _queueVisualLinkPreview);
  });
}

function _showContextMenu(pos) {
  if (!_contextMenu) return;
  const startLinkBtn = document.getElementById('ctx-start-link');
  const finishLinkBtn = document.getElementById('ctx-finish-link');
  const clearLinkBtn = document.getElementById('ctx-clear-link');
  const createBtn = document.getElementById('ctx-create-node');
  const customizeNodeBtn = document.getElementById('ctx-customize-node-type');
  const customizeEdgeBtn = document.getElementById('ctx-customize-edge-layer');
  if (createBtn) createBtn.style.display = _contextEdge ? 'none' : 'block';
  if (customizeNodeBtn) customizeNodeBtn.style.display = _contextNode ? 'block' : 'none';
  if (customizeEdgeBtn) customizeEdgeBtn.style.display = _contextEdge ? 'block' : 'none';
  if (startLinkBtn) startLinkBtn.style.display = _contextNode ? 'block' : 'none';
  if (finishLinkBtn) finishLinkBtn.style.display = (_contextNode && _linkSourceNode && _linkSourceNode.node_id !== _contextNode.node_id) ? 'block' : 'none';
  if (clearLinkBtn) clearLinkBtn.style.display = _linkSourceNode ? 'block' : 'none';
  _contextMenu.style.left = `${pos.x}px`;
  _contextMenu.style.top = `${pos.y}px`;
  _contextMenu.style.display = 'block';
}

function _hideContextMenu() {
  if (_contextMenu) _contextMenu.style.display = 'none';
}

function _nodePayloadFromCyNode(node) {
  if (!node || !node.data) return null;
  const data = node.data() || {};
  const raw = data._raw || {};
  const props = raw.properties || {};
  const nodeType = String(raw.node_type || data.node_type || 'markdown_note');
  const registry = (window.GraphStyles && window.GraphStyles.getRegistry && window.GraphStyles.getRegistry()) || {};
  const nodeTypeMap = registry.node_type_to_family || {};
  return {
    node_id: String(data.id || raw.id || node.id() || ''),
    path: String(props.path || raw.path || data.path || ''),
    label: String(data.label || raw.label || raw.title || data.id || ''),
    node_type: nodeType,
    node_family: String(data.node_family || raw.node_family || nodeTypeMap[nodeType] || nodeType || 'knowledge'),
  };
}

function _nodePayloadFromPlainNode(node) {
  if (!node) return null;
  const raw = node._raw || {};
  const props = raw.properties || {};
  const nodeType = String(raw.node_type || node.node_type || 'markdown_note');
  const registry = (window.GraphStyles && window.GraphStyles.getRegistry && window.GraphStyles.getRegistry()) || {};
  const nodeTypeMap = registry.node_type_to_family || {};
  return {
    node_id: String(node.id || raw.id || ''),
    path: String(props.path || raw.path || node.source_path || node.path || ''),
    label: String(node.label || raw.label || raw.title || node.id || ''),
    node_type: nodeType,
    node_family: String(node.node_family || raw.node_family || nodeTypeMap[nodeType] || nodeType || 'knowledge'),
  };
}

function _edgePayloadFromCyEdge(edge) {
  if (!edge || !edge.data) return null;
  const data = edge.data() || {};
  const layer = (window.GraphStyles && window.GraphStyles.normalizeEdgeLayer)
    ? window.GraphStyles.normalizeEdgeLayer(data.edge_layer || data.edge_family || 'explicit')
    : String(data.edge_layer || data.edge_family || 'explicit').replace(/-/g, '_');
  return {
    edge_id: String(data.id || edge.id() || ''),
    edge_layer: layer,
    relation: String(data.relation || ''),
  };
}

function showCreateNodeModal() {
  if (!_createModal) return;

  const titleInput = document.getElementById('create-node-title');
  const typeSelect = document.getElementById('create-node-type');
  const domainInput = document.getElementById('create-node-domain');
  const statusEl = document.getElementById('create-node-status');
  const submitBtn = document.getElementById('create-node-submit-btn');
  const previewEl = document.getElementById('create-node-target-preview');
  const postureEl = document.getElementById('create-node-approval-posture');

  if (titleInput) titleInput.value = '';
  if (domainInput) domainInput.value = 'general';
  if (statusEl) statusEl.textContent = '';
  if (previewEl) previewEl.textContent = 'Target preview will appear here.';
  if (postureEl) postureEl.textContent = 'Approval required before any file is written.';
  if (submitBtn) submitBtn.disabled = false;

  if (typeSelect && typeSelect.options.length === 0) {
    CREATABLE_NODE_TYPES.forEach(({ value, label }) => {
      const opt = document.createElement('option');
      opt.value = value;
      opt.textContent = label;
      typeSelect.appendChild(opt);
    });
  }

  _createModal.style.display = 'flex';
  if (titleInput) setTimeout(() => titleInput.focus(), 50);
  _queueCreatePreview();
}

function hideCreateNodeModal() {
  if (_createModal) _createModal.style.display = 'none';
}

function _queueCreatePreview() {
  if (_previewTimer) clearTimeout(_previewTimer);
  _previewTimer = setTimeout(_updateCreateNodePreview, 180);
}

async function _updateCreateNodePreview() {
  const titleInput = document.getElementById('create-node-title');
  const typeSelect = document.getElementById('create-node-type');
  const domainInput = document.getElementById('create-node-domain');
  const previewEl = document.getElementById('create-node-target-preview');
  const postureEl = document.getElementById('create-node-approval-posture');
  const submitBtn = document.getElementById('create-node-submit-btn');

  const title = (titleInput ? titleInput.value.trim() : '') || '';
  const nodeType = (typeSelect ? typeSelect.value : 'knowledge_doc') || 'knowledge_doc';
  const domain = (domainInput ? domainInput.value.trim() : '') || 'general';

  if (!previewEl) return;
  if (!title) {
    previewEl.textContent = 'Enter a title to preview the target file path.';
    if (submitBtn) submitBtn.disabled = false;
    return;
  }
  if (!window.pywebview || !window.pywebview.api || !window.pywebview.api.preview_create_node) {
    previewEl.textContent = 'Target preview unavailable.';
    return;
  }

  try {
    const resp = await window.pywebview.api.preview_create_node(nodeType, title, domain);
    const data = (resp && resp.data) || {};
    if (resp && resp.ok && data.target_path) {
      previewEl.textContent = data.target_path;
      previewEl.dataset.ok = String(!!data.ok);
      if (postureEl) {
        postureEl.textContent = data.ok
          ? 'Approval required before any file is written.'
          : (data.errors || ['Target is blocked.']).join(' ');
      }
      if (submitBtn) submitBtn.disabled = !data.ok;
    } else {
      const msg = (resp && resp.error && resp.error.message) || 'Preview failed.';
      previewEl.textContent = msg;
      if (submitBtn) submitBtn.disabled = true;
    }
  } catch (err) {
    previewEl.textContent = `Preview error: ${err.message}`;
    if (submitBtn) submitBtn.disabled = true;
  }
}

function _ensureVisualLinkOptions() {
  const layerSelect = document.getElementById('visual-link-edge-layer');
  const relationSelect = document.getElementById('visual-link-relation-type');
  if (layerSelect && layerSelect.options.length === 0) {
    VISUAL_LINK_EDGE_LAYERS.forEach(({ value, label }) => {
      const opt = document.createElement('option');
      opt.value = value;
      opt.textContent = label;
      layerSelect.appendChild(opt);
    });
  }
  if (relationSelect && relationSelect.options.length === 0) {
    VISUAL_LINK_RELATIONS.forEach(({ value, label }) => {
      const opt = document.createElement('option');
      opt.value = value;
      opt.textContent = label;
      relationSelect.appendChild(opt);
    });
  }
}

function showVisualLinkModal(sourceNode, targetNode) {
  if (!_visualLinkModal || !sourceNode || !targetNode) return;
  _ensureVisualLinkOptions();
  _linkSourceNode = sourceNode;
  _linkTargetNode = targetNode;

  const setText = (id, value) => { const el = document.getElementById(id); if (el) el.textContent = value || ''; };
  setText('visual-link-source-label', sourceNode.label || sourceNode.node_id);
  setText('visual-link-target-label', targetNode.label || targetNode.node_id);
  setText('visual-link-source-path', sourceNode.path || 'unresolved path');
  setText('visual-link-target-path', targetNode.path || 'unresolved path');

  const labelInput = document.getElementById('visual-link-label');
  const evidenceInput = document.getElementById('visual-link-evidence');
  const statusEl = document.getElementById('visual-link-status');
  const previewEl = document.getElementById('visual-link-preview');
  const submitBtn = document.getElementById('visual-link-submit-btn');
  if (labelInput) labelInput.value = '';
  if (evidenceInput) evidenceInput.value = '';
  if (statusEl) statusEl.textContent = '';
  if (previewEl) previewEl.textContent = 'Previewing approval-gated edge...';
  if (submitBtn) submitBtn.disabled = false;

  _visualLinkModal.style.display = 'flex';
  _queueVisualLinkPreview();
}

function hideVisualLinkModal() {
  if (_visualLinkModal) _visualLinkModal.style.display = 'none';
  _linkTargetNode = null;
}

function _visualLinkFormValues() {
  const layerSelect = document.getElementById('visual-link-edge-layer');
  const relationSelect = document.getElementById('visual-link-relation-type');
  const labelInput = document.getElementById('visual-link-label');
  const evidenceInput = document.getElementById('visual-link-evidence');
  return {
    edge_layer: (layerSelect ? layerSelect.value : 'explicit') || 'explicit',
    relation_type: (relationSelect ? relationSelect.value : 'related') || 'related',
    label: (labelInput ? labelInput.value.trim() : '') || '',
    evidence: (evidenceInput ? evidenceInput.value.trim() : '') || '',
  };
}

function _queueVisualLinkPreview() {
  if (_visualLinkPreviewTimer) clearTimeout(_visualLinkPreviewTimer);
  _visualLinkPreviewTimer = setTimeout(_updateVisualLinkPreview, 180);
}

async function _updateVisualLinkPreview() {
  const previewEl = document.getElementById('visual-link-preview');
  const statusEl = document.getElementById('visual-link-status');
  const submitBtn = document.getElementById('visual-link-submit-btn');
  const api = window.pywebview && window.pywebview.api;
  if (!previewEl || !_linkSourceNode || !_linkTargetNode) return;
  if (!api || !api.preview_visual_link) {
    previewEl.textContent = 'Visual link preview unavailable.';
    if (submitBtn) submitBtn.disabled = true;
    return;
  }
  const values = _visualLinkFormValues();
  try {
    const resp = await api.preview_visual_link(
      _linkSourceNode.node_id,
      _linkTargetNode.node_id,
      _linkSourceNode.path,
      _linkTargetNode.path,
      _linkSourceNode.label,
      _linkTargetNode.label,
      values.edge_layer,
      values.relation_type,
      values.label,
      values.evidence
    );
    const data = (resp && resp.data) || {};
    if (resp && resp.ok && data.preview_edge) {
      previewEl.textContent = `${data.source.label} -> ${data.target.label} (${data.edge_layer} / ${data.relation_type})`;
      if (statusEl) statusEl.textContent = 'Approval required. Pending edge will render as a non-canonical overlay.';
      if (submitBtn) submitBtn.disabled = false;
    } else {
      const msg = (resp && resp.error && resp.error.message) || 'Visual link blocked.';
      previewEl.textContent = msg;
      if (statusEl) statusEl.textContent = msg;
      if (submitBtn) submitBtn.disabled = true;
    }
  } catch (err) {
    previewEl.textContent = `Preview error: ${err.message}`;
    if (submitBtn) submitBtn.disabled = true;
  }
}

async function _submitCreateNode() {
  const titleInput = document.getElementById('create-node-title');
  const typeSelect = document.getElementById('create-node-type');
  const domainInput = document.getElementById('create-node-domain');
  const statusEl = document.getElementById('create-node-status');
  const submitBtn = document.getElementById('create-node-submit-btn');

  const title = (titleInput ? titleInput.value.trim() : '') || '';
  const nodeType = (typeSelect ? typeSelect.value : 'knowledge_doc') || 'knowledge_doc';
  const domain = (domainInput ? domainInput.value.trim() : '') || 'general';

  if (!title) {
    if (statusEl) statusEl.textContent = 'Title is required.';
    return;
  }

  if (statusEl) statusEl.textContent = 'Queueing approval...';
  if (submitBtn) submitBtn.disabled = true;

  try {
    const resp = await window.pywebview.api.create_node(nodeType, title, domain);

    if (resp.status === 'requires_approval') {
      hideCreateNodeModal();
      if (window.ApprovalModal) {
        window.ApprovalModal.showApprovalModal(resp.approval, refreshAfterApproval);
      }
    } else if (resp.ok) {
      hideCreateNodeModal();
      if (typeof setStatus === 'function') setStatus(`Created: ${title}`, 'observe');
      refreshAfterApproval();
    } else {
      const msg = (resp.error && resp.error.message) || 'Create failed';
      if (statusEl) statusEl.textContent = `Error: ${msg}`;
      if (submitBtn) submitBtn.disabled = false;
    }
  } catch (err) {
    if (statusEl) statusEl.textContent = `Error: ${err.message}`;
    if (submitBtn) submitBtn.disabled = false;
  }
}

async function _submitVisualLink() {
  const statusEl = document.getElementById('visual-link-status');
  const submitBtn = document.getElementById('visual-link-submit-btn');
  const api = window.pywebview && window.pywebview.api;
  if (!api || !api.create_link || !_linkSourceNode || !_linkTargetNode) {
    if (statusEl) statusEl.textContent = 'Visual link API unavailable.';
    return;
  }
  if (statusEl) statusEl.textContent = 'Queueing visual link approval...';
  if (submitBtn) submitBtn.disabled = true;
  const values = _visualLinkFormValues();
  try {
    const resp = await api.create_link(
      _linkSourceNode.node_id,
      _linkTargetNode.node_id,
      _linkSourceNode.path,
      _linkTargetNode.path,
      _linkSourceNode.label,
      _linkTargetNode.label,
      values.edge_layer,
      values.relation_type,
      values.label,
      values.evidence
    );
    if (resp && resp.status === 'requires_approval') {
      hideVisualLinkModal();
      _linkSourceNode = null;
      if (window.ApprovalModal) window.ApprovalModal.showApprovalModal(resp.approval, refreshAfterApproval);
      refreshVisualLinkOverlay();
      return;
    }
    const msg = (resp && resp.error && resp.error.message) || 'Visual link request blocked.';
    if (statusEl) statusEl.textContent = msg;
    if (submitBtn) submitBtn.disabled = false;
  } catch (err) {
    if (statusEl) statusEl.textContent = `Error: ${err.message}`;
    if (submitBtn) submitBtn.disabled = false;
  }
}

function _renderOverlaySummary(data) {
  const el = document.getElementById('graph-link-overlay-summary');
  if (!el) return;
  const contract = data && data.performance_contract ? data.performance_contract : {};
  const count = data ? (data.overlay_edge_count || 0) : 0;
  const scanned = contract.approval_files_scanned || 0;
  el.textContent = `Pending links ${count} - overlay cap ${contract.max_overlay_edges || 250} - approval scan ${scanned}`;
}

function _removeExistingOverlayEdges() {
  if (!_activeCy) return;
  _activeCy.edges('[pending_visual_link = "true"]').remove();
}

function _overlayEdgeElement(edge) {
  const layer = edge.edge_layer || 'suggested';
  return {
    group: 'edges',
    data: {
      id: String(edge.id || `pending-${edge.approval_id}`),
      source: String(edge.source),
      target: String(edge.target),
      relation: edge.relation || 'studio_visual_related',
      edge_family: layer,
      relation_layer: layer,
      edge_layer: layer,
      canonical_layer: edge.canonical_layer || (layer === 'runtime' ? 'runtime-action' : layer),
      approval_id: edge.approval_id || '',
      approval_status: edge.approval_status || 'pending',
      pending_visual_link: 'true',
    },
    classes: `edge edge--${layer} visual-link-${edge.approval_status || 'pending'}`,
  };
}

async function refreshVisualLinkOverlay() {
  const api = window.pywebview && window.pywebview.api;
  if (!_activeCy || !api || !api.get_visual_link_overlay) return null;
  try {
    const resp = await api.get_visual_link_overlay(250);
    if (!resp || !resp.ok) return null;
    const data = resp.data || {};
    _lastOverlay = data;
    _removeExistingOverlayEdges();
    const elements = [];
    (data.overlay_edges || []).forEach(edge => {
      if (!_activeCy.$id(String(edge.source)).length) return;
      if (!_activeCy.$id(String(edge.target)).length) return;
      if (_activeCy.$id(String(edge.id)).length) return;
      elements.push(_overlayEdgeElement(edge));
    });
    if (elements.length) _activeCy.add(elements);
    _renderOverlaySummary(data);
    if (typeof applyGraphFilters === 'function') applyGraphFilters();
    return data;
  } catch (_) {
    return null;
  }
}

function refreshAfterApproval() {
  if (window.ApprovalModal) window.ApprovalModal.refreshApprovalBadge();
  if (typeof graphLoaded !== 'undefined') graphLoaded = false;
  if (typeof loadGraph === 'function') loadGraph();
  if (window.InspectorTabs && window.InspectorTabs.refreshCurrentMetadata) {
    window.InspectorTabs.refreshCurrentMetadata();
  }
  refreshVisualLinkOverlay();
}

window.WriteActions = {
  initWriteActions,
  showCreateNodeModal,
  hideCreateNodeModal,
  showVisualLinkModal,
  hideVisualLinkModal,
  refreshVisualLinkOverlay,
  refreshAfterApproval,
  lastOverlay: () => _lastOverlay,
  isReady: () => _writeActionsReady,
};
