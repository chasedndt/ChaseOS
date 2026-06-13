/**
 * graphPresets.js — Preset selector UI and application logic.
 *
 * Renders the preset selector bar above the graph.
 * Applying a preset deep-merges its settings_patch onto current settings
 * and triggers a graph re-render.
 */

'use strict';

let _currentPresetId = null;
let _presets = [];

// ── Deep merge (same logic as Python _deep_merge) ────────────────────────────

function _deepMerge(base, override) {
  const result = Object.assign({}, base);
  for (const [key, val] of Object.entries(override)) {
    if (key in result && typeof result[key] === 'object' && result[key] !== null
        && typeof val === 'object' && val !== null && !Array.isArray(val)) {
      result[key] = _deepMerge(result[key], val);
    } else {
      result[key] = val;
    }
  }
  return result;
}

// ── Preset bar rendering — compact <select> dropdown ─────────────────────────

function renderPresetBar(presets, currentId, onApply, onSave, onDelete) {
  _presets = presets || [];
  _currentPresetId = currentId || null;

  const bar = document.getElementById('graph-preset-bar');
  if (!bar) return;

  bar.innerHTML = '';

  // ── Select dropdown ───────────────────────────────────────────────────────
  const wrap = document.createElement('div');
  wrap.className = 'preset-select-wrap';

  const sel = document.createElement('select');
  sel.className = 'preset-select';
  sel.id = 'graph-preset-select';
  sel.title = 'Switch graph preset (Knowledge Map, Project Cockpit, etc.)';

  const placeholder = document.createElement('option');
  placeholder.value = '';
  placeholder.textContent = 'Presets ▾';
  if (!_currentPresetId) placeholder.selected = true;
  sel.appendChild(placeholder);

  for (const preset of _presets) {
    const opt = document.createElement('option');
    opt.value = preset.id;
    opt.textContent = preset.label;
    if (preset.id === _currentPresetId) opt.selected = true;
    sel.appendChild(opt);
  }

  sel.addEventListener('change', async () => {
    const preset = _presets.find(p => p.id === sel.value);
    if (!preset) return;
    sel.disabled = true;
    try {
      const applied = await onApply(preset);
      if (applied !== false) {
        _currentPresetId = preset.id;
      } else {
        // Revert selection if apply failed
        sel.value = _currentPresetId || '';
      }
    } catch (_) {
      sel.value = _currentPresetId || '';
    } finally {
      sel.disabled = false;
    }
  });

  wrap.appendChild(sel);
  bar.appendChild(wrap);

  // ── Save / Delete actions as icon-buttons beside the dropdown ────────────
  const saveBtn = document.createElement('button');
  saveBtn.className = 'preset-action-btn';
  saveBtn.type = 'button';
  saveBtn.textContent = '+ Save';
  saveBtn.title = 'Save current graph settings as a new user preset';
  saveBtn.style.cssText = 'font-size:10px;padding:2px 7px;min-height:26px;';
  saveBtn.addEventListener('click', async () => {
    if (typeof onSave === 'function') await onSave();
  });

  const deleteBtn = document.createElement('button');
  deleteBtn.className = 'preset-action-btn preset-action-btn--danger';
  deleteBtn.type = 'button';
  deleteBtn.textContent = '✕';
  deleteBtn.title = 'Delete selected preset';
  deleteBtn.disabled = !_currentPresetId;
  deleteBtn.style.cssText = 'font-size:10px;padding:2px 7px;min-height:26px;';
  deleteBtn.addEventListener('click', async () => {
    const preset = _presets.find(p => p.id === _currentPresetId);
    if (preset && typeof onDelete === 'function') await onDelete(preset);
  });

  bar.appendChild(saveBtn);
  bar.appendChild(deleteBtn);
}

// ── Apply a preset patch to current settings ──────────────────────────────────

function applyPresetPatch(currentSettings, preset) {
  if (!preset || !preset.settings_patch) return currentSettings;
  return _deepMerge(currentSettings, preset.settings_patch);
}

// ── Exports ───────────────────────────────────────────────────────────────────

window.GraphPresets = {
  renderPresetBar,
  applyPresetPatch,
  getCurrentPresetId: () => _currentPresetId,
};
