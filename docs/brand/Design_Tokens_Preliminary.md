# ChaseOS Preliminary Design Tokens

Status: `DOCS-ONLY / PRELIMINARY / FINAL LOGO AND UI REDESIGN NOT COMPLETE`

Source: [ChaseOS_Logo_Visual_Identity_Brief.md](ChaseOS_Logo_Visual_Identity_Brief.md)

These tokens capture the current brand direction only. They are not a final design system, not a completed logo package, and not a mandate to redesign the application UI in this pass.

## Visual Thesis

Human core. Agent network. Private boundary. Controlled execution.

## Color Philosophy

- Obsidian / Black: privacy, sovereignty, depth, control.
- Graphite / Gunmetal: system architecture, files, panels, permission surfaces.
- Off-white / Bone: clarity, trust, readable intelligence.
- Runtime Cyan / Agent Teal: agents, automations, active execution, runtime state.
- Human Gold / Warm Amber: human intent, judgment, permission, approval.
- Knowledge Violet: memory, knowledge graph, second brain, synthesis.
- Signal Red / Security Orange: warnings, blocked actions, permission conflicts, danger states.

Core color story:

> Obsidian is the private system. Graphite is the architecture. Cyan is the agent runtime. Amber is the human operator. Violet is the knowledge graph.

## Recommended Palette: Sovereign Obsidian

| Token | Name | Hex | Meaning |
|---|---|---:|---|
| `--chaseos-bg-primary` | Obsidian Black | `#050607` | Privacy, sovereignty, depth |
| `--chaseos-bg-secondary` | Deep System Navy | `#080A0F` | OS shell, command center |
| `--chaseos-surface-1` | Graphite | `#151922` | Panels, cards, containers |
| `--chaseos-surface-2` | Gunmetal | `#1D232D` | App modules, sidebars |
| `--chaseos-text-primary` | Bone White | `#F4F1EA` | Clarity, trust |
| `--chaseos-text-secondary` | Muted Silver | `#A8ADB7` | Metadata, descriptions |
| `--chaseos-agent-active` | Runtime Teal | `#39E6D2` | Agent activity, automation |
| `--chaseos-human-intent` | Human Amber | `#FFB86B` | User approval, intent |
| `--chaseos-memory-graph` | Knowledge Violet | `#7C5CFF` | Knowledge graph and memory |
| `--chaseos-permission-warning` | Permission Orange | `#FF8A4C` | Boundaries and alerts |
| `--chaseos-danger` | Runtime Red | `#FF4D6D` | Blocked or failed actions |
| `--chaseos-success` | Execution Green | `#22C55E` | Successful execution |

## Adaptive Light Palette

| Token | Name | Hex | Meaning |
|---|---|---:|---|
| `--chaseos-light-bg-primary` | Soft White | `#F8F7F3` | Clarity and accessibility |
| `--chaseos-light-surface-1` | Warm Paper | `#FFFFFF` | Cards and docs |
| `--chaseos-light-surface-2` | Soft Gray | `#ECEBE6` | Containers |
| `--chaseos-light-text-primary` | Deep Charcoal | `#111318` | Readability |
| `--chaseos-light-text-secondary` | Slate Gray | `#59606D` | Secondary text |
| `--chaseos-light-agent-active` | Runtime Teal | `#0F766E` | Agents and actions |
| `--chaseos-light-human-intent` | Amber | `#B7791F` | Human intent |
| `--chaseos-light-memory-graph` | Violet | `#6D4AFF` | Knowledge graph |

## Semantic Tokens

| Token | Role |
|---|---|
| `--chaseos-human-intent` | Human approvals, judgment, operator-owned decisions, explicit permission gates. |
| `--chaseos-agent-active` | Runtime activity, automation, agent execution state, active task lanes. |
| `--chaseos-memory-graph` | Knowledge graph, provenance, memory, synthesis, source relationships. |
| `--chaseos-private-boundary` | Private shell, containment, permission boundary, secure workspace surfaces. |
| `--chaseos-controlled-execution` | Executed workflow state, approved automation progress, bounded runtime output. |
| `--chaseos-permission-warning` | Approval missing, blocked authority, unsafe target, policy conflict. |

## Typography Direction

Primary direction: clean geometric or neo-grotesk sans-serif.

Recommended open/product stacks:

- Geist Sans + Geist Mono
- Inter + JetBrains Mono
- IBM Plex Sans + IBM Plex Mono

Use monospace sparingly for runtime logs, command palettes, permission events, workflow state labels, system metadata, and developer panels.

## Logo And UI Status

- Final logo: `PLANNED`.
- Final wordmark: `PLANNED`.
- Final Studio UI redesign: `PLANNED`.
- Branded installer assets: `PLANNED`.
- Current pass: brand documentation and preliminary token alignment only.
