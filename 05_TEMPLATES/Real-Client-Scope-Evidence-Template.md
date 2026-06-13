---
type: ventureops-real-client-scope-evidence-template
status: template
version: "0.1"
---

# Real Client Scope Evidence Template

No live client data should be pasted into this template. Use this to declare the approved scope packet only.

```json
{
  "type": "ventureops-real-client-scope-evidence",
  "client_approved_scope_id": "scope-client-name-001",
  "client_label": "Client Name",
  "approval_id": "operator-real-client-scope-approval-001",
  "approval_status": "approved",
  "approval_artifact_path": "client_scopes/client-name/scope-approval.json",
  "approved_read_paths": [
    "client_scopes/client-name/approved-file.md"
  ],
  "redaction_policy": "client_safe_summary_only",
  "delivery_boundary": "no_external_delivery"
}
```

## Rules

- `approved_read_paths` must be relative paths inside the declared workspace.
- `approval_artifact_path` must point to a typed `ventureops-real-client-scope-approval` artifact for the same approval, client, scope, and read paths.
- Do not include `.env`, secrets, credentials, tokens, keys, cookies, wallets, or broad filesystem roots.
- This packet only unlocks the proof gate. It does not authorize provider/model calls, browser actions, CRM/payment mutation, external delivery, marketplace publication, or revenue claims.
