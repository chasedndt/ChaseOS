/* ChaseOS Studio — Approval Modal (Pass 10C)
 *
 * Handles the operator approval flow for gated write actions.
 * All decisions route through window.pywebview.api.submit_approval().
 *
 * Runtime identity: Archon / Claude Code Engineering Runtime
 */
'use strict';

let _approvalModal = null;
let _onResolveCallback = null;

function initApprovalModal() {
  _approvalModal = document.getElementById('approval-modal');
  if (!_approvalModal) return;

  const closeBtn = document.getElementById('approval-modal-close');
  if (closeBtn) closeBtn.addEventListener('click', hideApprovalModal);

  _approvalModal.addEventListener('click', evt => {
    if (evt.target === _approvalModal) hideApprovalModal();
  });
}

function showApprovalModal(approvalData, onResolve) {
  _onResolveCallback = onResolve || null;

  if (!_approvalModal) {
    // Auto-init if not done
    initApprovalModal();
    if (!_approvalModal) return;
  }

  const data = approvalData || {};
  const setText = (id, val) => { const el = document.getElementById(id); if (el) el.textContent = val || ''; };
  const setVal  = (id, val) => { const el = document.getElementById(id); if (el) el.value  = val || ''; };

  setText('approval-action-type', data.action_type || '');
  setText('approval-path',        data.target_path  || '');
  setText('approval-detail',      data.detail        || '');
  setText('approval-id-display',  data.approval_id   || '');
  setVal('approval-note', '');
  setText('approval-modal-status', '');

  // Store approval_id on the modal element for _submitApproval to read
  _approvalModal.dataset.approvalId = data.approval_id || '';

  const approveBtn = document.getElementById('approval-approve-btn');
  const rejectBtn  = document.getElementById('approval-reject-btn');
  if (approveBtn) { approveBtn.disabled = false; approveBtn.onclick = () => _submitApproval('approve'); }
  if (rejectBtn)  { rejectBtn.disabled  = false; rejectBtn.onclick  = () => _submitApproval('reject');  }

  _approvalModal.style.display = 'flex';
}

function hideApprovalModal() {
  if (_approvalModal) _approvalModal.style.display = 'none';
  _onResolveCallback = null;
}

async function _submitApproval(decision) {
  const approvalId = _approvalModal ? (_approvalModal.dataset.approvalId || '') : '';
  const noteEl   = document.getElementById('approval-note');
  const statusEl = document.getElementById('approval-modal-status');
  const approveBtn = document.getElementById('approval-approve-btn');
  const rejectBtn  = document.getElementById('approval-reject-btn');
  const note = noteEl ? noteEl.value.trim() : '';

  if (!approvalId) {
    if (statusEl) statusEl.textContent = 'No approval ID — cannot submit.';
    return;
  }

  if (statusEl) statusEl.textContent = 'Submitting…';
  if (approveBtn) approveBtn.disabled = true;
  if (rejectBtn)  rejectBtn.disabled  = true;

  try {
    const resp = await window.pywebview.api.submit_approval(approvalId, decision, note);

    if (resp.ok) {
      const resolvedData = resp.data || {};
      hideApprovalModal();

      if (typeof _onResolveCallback === 'function') _onResolveCallback(resolvedData);

      if (decision === 'approve') {
        const writes = resolvedData.writes || [];
        if (typeof setStatus === 'function') {
          setStatus(`Approved — ${writes.length} file(s) written`, 'observe');
        }
        // Reload graph if vault files were written
        if (writes.length > 0 && typeof loadGraph === 'function') loadGraph();
      } else {
        if (typeof setStatus === 'function') setStatus('Action rejected', 'observe');
      }

      refreshApprovalBadge();

    } else {
      const msg = (resp.error && resp.error.message) || 'Approval failed';
      if (statusEl) statusEl.textContent = `Error: ${msg}`;
      if (approveBtn) approveBtn.disabled = false;
      if (rejectBtn)  rejectBtn.disabled  = false;
    }

  } catch (err) {
    if (statusEl) statusEl.textContent = `Error: ${err.message}`;
    if (approveBtn) approveBtn.disabled = false;
    if (rejectBtn)  rejectBtn.disabled  = false;
  }
}

async function refreshApprovalBadge() {
  const badge = document.getElementById('approval-queue-badge');
  if (!badge || !window.pywebview || !window.pywebview.api) return;
  try {
    const resp = await window.pywebview.api.get_approval_queue();
    if (resp && resp.ok) {
      const count = (resp.data && (resp.data.pending_count != null ? resp.data.pending_count : (resp.data.items || []).length)) || 0;
      badge.textContent   = count > 0 ? String(count) : '';
      badge.style.display = count > 0 ? 'inline-block' : 'none';
      const topbarCount = document.getElementById('topbar-approvals-count');
      if (topbarCount) topbarCount.textContent = String(count);
    }
  } catch (_) {}
}

window.ApprovalModal = {
  initApprovalModal,
  showApprovalModal,
  hideApprovalModal,
  refreshApprovalBadge,
};

// Top-level alias so app.js can call refreshApprovalBadge() directly
window.refreshApprovalBadge = refreshApprovalBadge;
