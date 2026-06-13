---
type: ventureops-live-revenue-evidence-template
status: template
version: "0.1"
---

# Live Revenue Evidence Template

No raw payment credentials or customer financial data should be pasted into this template. Use redacted proof artifact paths and opaque reference IDs only.

```json
{
  "type": "ventureops-live-revenue-evidence",
  "revenue_proof_id": "revenue-proof-client-name-001",
  "workflow_id": "agent_runtime_governance_audit",
  "client_label": "Client Name",
  "payment_reference_id": "opaque-payment-reference",
  "payment_status": "received",
  "amount": "250.00",
  "currency": "USD",
  "receipt_artifact_path": "07_LOGS/Revenue-Proofs/client-name-receipt-redacted.json",
  "delivery_proof_path": "07_LOGS/Workflow-Proofs/client-name-delivery-proof.json",
  "crm_reference_id": "opaque-crm-reference",
  "approval_id": "operator-live-revenue-proof-approval-001",
  "revenue_recognition_boundary": "proof_only_no_accounting_claim"
}
```

## Rules

- Use opaque IDs and redacted artifact paths only.
- Do not include card numbers, bank details, API keys, credentials, tokens, cookies, wallet keys, or raw customer financial data.
- This packet is proof evidence only. It is not an accounting record, tax record, payment-system mutation, CRM mutation, marketplace publication, or external delivery authorization.
