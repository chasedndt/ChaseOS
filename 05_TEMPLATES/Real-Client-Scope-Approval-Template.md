---
type: ventureops-real-client-scope-approval-template
status: template
version: "0.1"
---

# Real Client Scope Approval Template

No live client data should be pasted into this template. Use this to declare operator approval for a bounded real-client scope packet only.

```json
{
  "type": "ventureops-real-client-scope-approval",
  "approval_id": "operator-real-client-scope-approval-001",
  "client_label": "Client Name",
  "client_approved_scope_id": "scope-client-name-001",
  "approval_status": "approved",
  "approval_decision": "approved",
  "approved_read_paths": [
    "client_scopes/client-name/approved-file.md"
  ],
  "redaction_policy": "client_safe_summary_only",
  "delivery_boundary": "no_external_delivery",
  "operator_attested_scope_approved": true,
  "external_send_authorized": false,
  "payment_mutation_authorized": false,
  "crm_mutation_authorized": false,
  "provider_calls_authorized": false,
  "browser_actions_authorized": false,
  "revenue_claim_authorized": false
}
```

## Rules

- `approved_read_paths` must be relative paths inside the declared workspace.
- Do not include `.env`, secrets, credentials, tokens, keys, cookies, wallets, or broad filesystem roots.
- All side-effect authority flags must remain false.
- This approval only supports scope evidence authoring. It does not authorize provider/model calls, browser actions, CRM/payment mutation, external delivery, marketplace publication, accounting claims, or revenue claims.
