---
type: personal-domain-node-template
template_status: git-safe
version: 1.0
created: YYYY-MM-DD
canonical_writeback_enabled: false
---

# <Personal Domain / Interest Node>

> Use this template for a personal operating-domain node that agents can read safely. Keep concrete private details in the personal instance; use generic placeholders in git-safe exports.

## Node Metadata

| Field | Value |
|---|---|
| Node ID | `<stable-kebab-case-id>` |
| Domain / Category | `<fitness / interest / language / networking / hardware / creative / content / etc.>` |
| Status | `SOURCE-DERIVED / REVIEW REQUIRED` |
| Truth posture | `<canonical / source-derived / direct-operator-input / candidate / generated / uncertain / evidence-gap>` |
| Last updated | `YYYY-MM-DD` |
| Source packet / evidence | `<relative path or source label; no private external URL unless safe>` |

## Purpose

- What this domain/interest is.
- Why it matters to the operator.
- What kinds of decisions or agent behavior it should influence.

## Source-Derived Context

Fill this from the source/handover packet to the maximum safe extent. Do not leave placeholders if the packet contains usable context.

- `<specific source-derived fact>`
- `<specific source-derived goal>`
- `<specific source-derived open loop>`

## Direct Operator Inputs

Use this section for direct corrections or additions from the operator.

| Date | Input | Routing impact |
|---|---|---|
| `YYYY-MM-DD` | `<operator statement>` | `<which OS/project/knowledge node it affects>` |

## Categories

| Category | Details | Linked OS surface |
|---|---|---|
| `<category>` | `<specific context>` | `[[linked-node]]` |

## Operating Role

- How agents should use this context.
- What this node should help prioritize, explain, protect, or route.
- What actions are appropriate versus out of scope.

## Linked Projects And Domains

- `[[00_HOME/Operating-System]]`
- `[[00_HOME/Personal-Operator-Index]]`
- `[[relevant project OS]]`
- `[[relevant knowledge root]]`

## Evidence Gaps

Write exact missing evidence. Avoid vague filler.

- `<current routine not supplied>`
- `<priority weight unconfirmed>`
- `<deadline/metric/status not supplied>`

## Git-Safe Export Notes

- Replace personal names, private projects, accounts, and logs with generic examples.
- Keep the structure, truth labels, and routing fields.
- Do not export secrets, credentials, private relationship details, financial data, medical details, exact locations, or sensitive personal history.
- Use example labels such as `<operator>`, `<project>`, `<interest>`, and `<knowledge-domain>` in public templates.

## Review / Apply Boundary

- Operator reviewed: `no`
- Accepted into Personal Map: `no`
- Personal Map apply allowed: `no`
- Canonical writeback allowed: `no`

## Graph Links

[[00_HOME/Personal-Operator-Index]] [[00_HOME/Operating-System]]
