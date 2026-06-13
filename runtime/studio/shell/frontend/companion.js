/* companion.js — ChaseOS Companion System v3.0
 * Runtime companion mascots with visual genome, dynamic traits, animation states,
 * per-runtime emotes, collection view, and runtime brain link.
 * Exposed as window.CompanionSystem.
 *
 * v3.0 changes (Companion Identity + Asset Upgrade):
 *   - COMPANION_PRESETS.traits removed; replaced with .traitSeeds (hint pool)
 *   - generateCompanionGenome() — visual DNA generated + persisted at hatch
 *   - generateCompanionTraits() — traits generated from role/lane/genome/usage
 *   - GENOME_PARTS catalog — 3 variants per body/eye/orbit/accessory/aura per family
 *   - ANIMATION_STATES — 12 named states with CSS classes + preview cards
 *   - RUNTIME_SPECIAL_EMOTES per-runtime specials (relay, guard, reflect, compile)
 *   - renderAnimationStates() — state section in profile panel
 *   - renderRuntimeBrainLink() — runtime/profile link section
 *   - renderMyCompanionsCollection() — 4-card compact collection view
 *   - renderCustomizationPanel() — color accent + motion + frame options
 *   - renderCompanionProfilePanel() upgraded with all new sections
 *   - Unhatched: NO finalized trait chips; show seed-hint label instead
 *
 * Persistence model (unchanged from v2.3):
 *   Primary: <vault>/.chaseos/studio/companions.json (permanent)
 *   Secondary: localStorage (session cache)
 *   _pendingBackendWrite queue flushes writes blocked before bridge ready.
 *
 * Home companion selection — resolveHomeCompanionCandidate() priority:
 *   1. Explicit isHomeCompanion flag
 *   2. Usage-backed: highest AOR execution + bus heartbeat score
 *   3. 24/7 fallback: hermes → openclaw
 *   4. First hatched
 *
 * Dormant default: Hermes (primary 24/7 runtime). NOT hardcoded as home companion.
 */
'use strict';

(function (global) {

/* ── Store keys ─────────────────────────────────────────────────────────────── */
const COMPANION_STORE_KEY = 'chaseos.companions.v2';
const HOME_COMPANION_KEY  = 'chaseos.homeCompanion';

/* ── Per-runtime companion presets ─────────────────────────────────────────── */
// v3.0: 'traits' replaced with 'traitSeeds'. Traits are generated dynamically at
// hatch time via generateCompanionTraits() and stored on the companion record.
// traitSeeds is the raw hint pool — it does NOT directly appear as finalized traits.
const COMPANION_PRESETS = {
  hermes: {
    name: 'Relay',
    runtimeId: 'hermes',
    runtimeName: 'Hermes',
    archetype: 'Courier Spirit',
    rarity: 'Rare',
    theme: 'courier',
    primaryHsl: [155, 70, 52],
    accentHsl: [190, 80, 60],
    traitSeeds: ['coordinating', 'responsive', 'persistent', 'fast', 'relay-focused', 'signal-aware'],
    baseEmotes: ['idle', 'blink', 'wave', 'scan', 'alert'],
    specialEmotes: ['relay', 'signal-pulse'],
    moodDefault: 'alert',
    laneClass: 'persistent',
    bondBase: 15,
  },
  openclaw: {
    name: 'Sygnal',
    runtimeId: 'openclaw',
    runtimeName: 'OpenClaw',
    archetype: 'Sentinel Core',
    rarity: 'Prime',
    theme: 'sentinel',
    primaryHsl: [38, 90, 55],
    accentHsl: [190, 80, 60],
    traitSeeds: ['guarded', 'tactical', 'persistent', 'local-first', 'defensive', 'vigilant'],
    baseEmotes: ['idle', 'blink', 'scan', 'alert', 'defend'],
    specialEmotes: ['claw-guard', 'sentinel-scan'],
    moodDefault: 'watchful',
    laneClass: 'persistent',
    bondBase: 15,
  },
  archon: {
    name: 'Archon',
    runtimeId: 'archon',
    runtimeName: 'Claude Code',
    archetype: 'Architect Wisp',
    rarity: 'Prime',
    theme: 'architect',
    primaryHsl: [38, 85, 55],
    accentHsl: [265, 75, 65],
    traitSeeds: ['structured', 'calm', 'analytical', 'reasoned', 'architectural', 'orbit-thinker'],
    baseEmotes: ['idle', 'blink', 'think', 'scan', 'wave'],
    specialEmotes: ['reflect', 'architect-pulse'],
    moodDefault: 'reflective',
    laneClass: 'session',
    bondBase: 10,
  },
  claude: {   // alias → archon
    name: 'Archon',
    runtimeId: 'archon',
    runtimeName: 'Claude Code',
    archetype: 'Architect Wisp',
    rarity: 'Prime',
    theme: 'architect',
    primaryHsl: [38, 85, 55],
    accentHsl: [265, 75, 65],
    traitSeeds: ['structured', 'calm', 'analytical', 'reasoned', 'architectural', 'orbit-thinker'],
    baseEmotes: ['idle', 'blink', 'think', 'scan', 'wave'],
    specialEmotes: ['reflect', 'architect-pulse'],
    moodDefault: 'reflective',
    laneClass: 'session',
    bondBase: 10,
  },
  codex: {
    name: 'Patch',
    runtimeId: 'codex',
    runtimeName: 'Codex',
    archetype: 'Code Sprite',
    rarity: 'Rare',
    theme: 'debugger',
    primaryHsl: [220, 80, 60],
    accentHsl: [265, 75, 65],
    traitSeeds: ['precise', 'technical', 'builder', 'focused', 'code-native', 'terminal-born'],
    baseEmotes: ['idle', 'blink', 'scan', 'think', 'working'],
    specialEmotes: ['compile', 'debug-pulse'],
    moodDefault: 'focused',
    laneClass: 'session',
    bondBase: 10,
  },
};

/* ── Rarity configuration ───────────────────────────────────────────────────── */
const RARITY_CONFIG = {
  Core:      { color: '#94a3b8', glow: '0 0 6px rgba(148,163,184,0.30)',  badge: '#475569', borderColor: 'rgba(148,163,184,0.25)' },
  Uncommon:  { color: '#34d399', glow: '0 0 10px rgba(52,211,153,0.38)',  badge: '#059669', borderColor: 'rgba(52,211,153,0.28)' },
  Rare:      { color: '#38bdf8', glow: '0 0 16px rgba(56,189,248,0.42)',  badge: '#0284c7', borderColor: 'rgba(56,189,248,0.32)' },
  Prime:     { color: '#f59e0b', glow: '0 0 22px rgba(245,158,11,0.52)',  badge: '#b45309', borderColor: 'rgba(245,158,11,0.38)' },
  Mythic:    { color: '#a855f7', glow: '0 0 26px rgba(168,85,247,0.58)',  badge: '#7c3aed', borderColor: 'rgba(168,85,247,0.40)' },
  Sovereign: { color: '#ef4444', glow: '0 0 32px rgba(239,68,68,0.68)',  badge: '#b91c1c', borderColor: 'rgba(239,68,68,0.45)' },
};

/* ── Genome parts catalog ───────────────────────────────────────────────────── */
// Per-family part variants. Index selected deterministically from _hashSeed(runtimeId+rarity).
const GENOME_PARTS = {
  courier: {
    bodies:      ['glass-orb', 'trail-orb', 'pulse-orb'],
    eyeVariants: ['round-glyph', 'scan-glyph', 'twin-arc'],
    orbitTypes:  ['ellipse-tilt', 'ellipse-wide', 'ring-cross'],
    accessories: [null, 'signal-band', 'relay-trail'],
    auras:       ['dashed-ring', 'pulse-scatter', 'soft-halo'],
  },
  sentinel: {
    bodies:      ['shield-core', 'claw-core', 'armored-core'],
    eyeVariants: ['scan-rect', 'twin-rect', 'arc-visor'],
    orbitTypes:  ['hex-frame', 'diamond-ring', 'none'],
    accessories: [null, 'claw-detail', 'guard-band'],
    auras:       ['solid-ring', 'scan-sweep', 'alert-pulse'],
  },
  architect: {
    bodies:      ['geo-sphere', 'star-core', 'lattice-orb'],
    eyeVariants: ['orbit-dot', 'diamond-eye', 'round-glyph'],
    orbitTypes:  ['dual-cross', 'ellipse-tilt', 'star-ring'],
    accessories: [null, 'reflection-dot', 'geo-accent'],
    auras:       ['geo-halo', 'orbit-scatter', 'think-ring'],
  },
  debugger: {
    bodies:      ['terminal-cube', 'hex-core', 'bracket-orb'],
    eyeVariants: ['scan-line', 'twin-rect', 'cursor-eye'],
    orbitTypes:  ['hex-frame', 'bracket-ring', 'none'],
    accessories: [null, 'cursor-blink', 'code-accent'],
    auras:       ['scan-line-aura', 'code-rain', 'signal-ring'],
  },
};

/* ── Trait pool ─────────────────────────────────────────────────────────────── */
// Grouped by source. generateCompanionTraits() draws from relevant groups.
const TRAIT_POOL = {
  persistent_lane:      ['persistent', 'always-on', 'steady', 'reliable'],
  session_lane:         ['on-demand', 'session-bound', 'focused-burst'],
  coordination_role:    ['coordinating', 'relay-focused', 'signal-aware', 'responsive'],
  execution_role:       ['execution-backed', 'workflow-driven', 'local-first', 'tactical'],
  implementation_role:  ['structured', 'analytical', 'reasoned', 'architectural'],
  build_role:           ['builder', 'precise', 'technical', 'code-native'],
  // Family/species-specific
  courier:   ['fast', 'relay-spirit', 'courier-born', 'transit'],
  sentinel:  ['defensive', 'vigilant', 'guarded', 'shield-bearer'],
  architect: ['calm', 'geometric', 'orbital', 'orbit-thinker'],
  debugger:  ['precise', 'terminal-born', 'debug-instinct', 'bracket-minded'],
  // Usage-driven (added only when usage evidence is present)
  heavy_usage: ['seasoned', 'experienced', 'well-bonded'],
  bus_active:  ['bus-connected', 'bus-aware'],
  aor_runner:  ['execution-heavy', 'workflow-native'],
};

/* ── Runtime trait seed mapping ─────────────────────────────────────────────── */
const _RUNTIME_TRAIT_SEEDS = {
  hermes:   { lane: 'persistent', role: 'coordination',     family: 'courier' },
  openclaw: { lane: 'persistent', role: 'execution',        family: 'sentinel' },
  archon:   { lane: 'session',    role: 'implementation',   family: 'architect' },
  claude:   { lane: 'session',    role: 'implementation',   family: 'architect' },
  codex:    { lane: 'session',    role: 'build',            family: 'debugger' },
};

/* ── Animation states ───────────────────────────────────────────────────────── */
const ANIMATION_STATES = {
  idle:     { label: 'Idle',     cls: 'companion-state-idle',     desc: 'Companion floats softly.',           icon: '◌' },
  working:  { label: 'Working',  cls: 'companion-state-working',  desc: 'Processing an active task.',         icon: '⚙' },
  waiting:  { label: 'Waiting',  cls: 'companion-state-waiting',  desc: 'Ready, watching for input.',         icon: '◎' },
  review:   { label: 'Review',   cls: 'companion-state-review',   desc: 'Reviewing queued items.',            icon: '◈' },
  failed:   { label: 'Failed',   cls: 'companion-state-failed',   desc: 'Last task did not complete.',        icon: '✕' },
  alert:    { label: 'Alert',    cls: 'companion-state-alert',    desc: 'Action required.',                   icon: '!' },
  success:  { label: 'Success',  cls: 'companion-state-success',  desc: 'Task completed.',                    icon: '✓' },
  sleeping: { label: 'Sleeping', cls: 'companion-state-sleeping', desc: 'Runtime idle or offline.',           icon: 'Z' },
  thinking: { label: 'Thinking', cls: 'companion-state-thinking', desc: 'Evaluating context.',               icon: '…' },
  scanning: { label: 'Scanning', cls: 'companion-state-scanning', desc: 'Scanning vault or inputs.',          icon: '◉' },
  running:  { label: 'Running',  cls: 'companion-state-running',  desc: 'Executing active workflow.',         icon: '▶' },
  hatching: { label: 'Hatching', cls: 'companion-state-hatching', desc: 'Initial reveal sequence.',           icon: '*' },
};

/* ── Campaign stages ────────────────────────────────────────────────────────── */
const CAMPAIGN_STAGES = [
  { id: 'dormant',   label: 'Dormant',   threshold: 0,   description: 'Companion not yet hatched.' },
  { id: 'hatched',   label: 'Hatched',   threshold: 10,  description: 'First hatch complete. Companion is awake.' },
  { id: 'synced',    label: 'Synced',    threshold: 25,  description: 'Companion is synchronized with the runtime.' },
  { id: 'active',    label: 'Active',    threshold: 50,  description: 'Companion fully operational and responsive.' },
  { id: 'trusted',   label: 'Trusted',   threshold: 75,  description: 'High trust established between operator and runtime.' },
  { id: 'sovereign', label: 'Sovereign', threshold: 100, description: 'Maximum campaign stage. Companion identity complete.' },
];

/* ── Emote definitions ──────────────────────────────────────────────────────── */
const EMOTE_DEFS = {
  idle:             { label: 'Idle',      icon: '◌', duration: 0,    cls: '' },
  blink:            { label: 'Blink',     icon: '◍', duration: 800,  cls: 'comp-emote--blink' },
  wave:             { label: 'Wave',      icon: '~',      duration: 1200, cls: 'comp-emote--wave' },
  nod:              { label: 'Nod',       icon: '↕', duration: 900,  cls: 'comp-emote--nod' },
  think:            { label: 'Think',     icon: '◉', duration: 2000, cls: 'comp-emote--think' },
  scan:             { label: 'Scan',      icon: '◈', duration: 1500, cls: 'comp-emote--scan' },
  working:          { label: 'Working',   icon: '⚙', duration: 2000, cls: 'comp-emote--working' },
  alert:            { label: 'Alert',     icon: '!',      duration: 1200, cls: 'comp-emote--alert' },
  celebrate:        { label: 'Celebrate', icon: '+',      duration: 1800, cls: 'comp-emote--celebrate' },
  defend:           { label: 'Defend',    icon: '◻', duration: 1000, cls: 'comp-emote--defend' },
  sleep:            { label: 'Sleep',     icon: 'Z',      duration: 0,    cls: 'comp-emote--sleep' },
  wake:             { label: 'Wake',      icon: '◎', duration: 1000, cls: 'comp-emote--wake' },
  error:            { label: 'Error',     icon: 'x',      duration: 1000, cls: 'comp-emote--error' },
  success:          { label: 'Success',   icon: '✓', duration: 900,  cls: 'comp-emote--success' },
  hatch:            { label: 'Hatch',     icon: '*',      duration: 2400, cls: 'comp-emote--hatch' },
  // Per-runtime special emotes
  relay:              { label: 'Relay',    icon: '→', duration: 1400, cls: 'comp-emote--relay' },
  'signal-pulse':     { label: 'Signal',   icon: '⊕', duration: 1200, cls: 'comp-emote--signal' },
  'claw-guard':       { label: 'Guard',    icon: '◻', duration: 1000, cls: 'comp-emote--guard' },
  'sentinel-scan':    { label: 'Sentinel', icon: '◉', duration: 1600, cls: 'comp-emote--sentinel-scan' },
  reflect:            { label: 'Reflect',  icon: '◈', duration: 1800, cls: 'comp-emote--reflect' },
  'architect-pulse':  { label: 'Orbit',    icon: 'o',      duration: 1400, cls: 'comp-emote--orbit' },
  compile:            { label: 'Compile',  icon: '>',      duration: 1600, cls: 'comp-emote--compile' },
  'debug-pulse':      { label: 'Debug',    icon: '>',      duration: 1200, cls: 'comp-emote--debug' },
};

/* ── Progression events → bond increments ───────────────────────────────────── */
const PROGRESSION_EVENTS = {
  companion_hatched:       10,
  profile_opened:          2,
  set_as_home:             5,
  chat_opened:             3,
  profile_doc_opened:      3,
  emote_triggered:         1,
  companion_customized:    3,
  runtime_execution_batch: 1,
  runtime_active_run:      2,
  state_card_clicked:      1,
};

/* ── Companion attribute roll system ────────────────────────────────────────
 * v3.1: Each hatch rolls every attribute category independently using weighted
 * random selection. The result is a unique genome — no two hatches need be the
 * same even for the same runtime. The overall rarity = highest-tier attribute
 * rolled. Each attribute and its rarity tier + % are shown in the profile panel.
 *
 * Tier hierarchy (low → high):  core → uncommon → rare → prime → mythic → sovereign
 * Tier chances are per-attribute (each attribute category has its own weights).
 * ─────────────────────────────────────────────────────────────────────────── */

const TIER_RANK = { core: 0, uncommon: 1, rare: 2, prime: 3, mythic: 4, sovereign: 5 };

const TIER_DISPLAY = {
  core:      { label: 'Core',      color: '#94a3b8', badge: '#475569' },
  uncommon:  { label: 'Uncommon',  color: '#34d399', badge: '#059669' },
  rare:      { label: 'Rare',      color: '#38bdf8', badge: '#0284c7' },
  prime:     { label: 'Prime',     color: '#f59e0b', badge: '#b45309' },
  mythic:    { label: 'Mythic',    color: '#a855f7', badge: '#7c3aed' },
  sovereign: { label: 'Sovereign', color: '#ef4444', badge: '#b91c1c' },
};

const COMPANION_ATTRIBUTES = {

  // ── Species / body type ───────────────────────────────────────────────────
  species: {
    label: 'Species',
    tiers: {
      core:      { chance: 0.40, items: [
        { id: 'orb-familiar',    label: 'Orb Familiar',      theme: null,        desc: 'A simple floating orb' },
        { id: 'drift-wisp',      label: 'Drift Wisp',        theme: null,        desc: 'Soft drifting spirit' },
      ]},
      uncommon:  { chance: 0.25, items: [
        { id: 'courier-spirit',  label: 'Courier Spirit',    theme: 'courier',   desc: 'Winged relay familiar' },
        { id: 'sentinel-core',   label: 'Sentinel Core',     theme: 'sentinel',  desc: 'Armored guardian form' },
      ]},
      rare:      { chance: 0.18, items: [
        { id: 'architect-wisp',  label: 'Architect Wisp',    theme: 'architect', desc: 'Orbital intelligence wisp' },
        { id: 'code-sprite',     label: 'Code Sprite',       theme: 'debugger',  desc: 'Terminal-born familiar' },
      ]},
      prime:     { chance: 0.10, items: [
        { id: 'vault-beast',     label: 'Vault Beast',       theme: 'sentinel',  desc: 'Memory and knowledge guardian' },
        { id: 'signal-herald',   label: 'Signal Herald',     theme: 'courier',   desc: 'Prime courier form' },
      ]},
      mythic:    { chance: 0.05, items: [
        { id: 'nexus-node',      label: 'Nexus Node',        theme: 'architect', desc: 'Multi-runtime convergence' },
        { id: 'shadow-core',     label: 'Shadow Core',       theme: 'sentinel',  desc: 'Deep system guardian' },
      ]},
      sovereign: { chance: 0.02, items: [
        { id: 'sovereign-form',  label: 'Sovereign Form',    theme: 'architect', desc: 'Ultimate companion form' },
      ]},
    }
  },

  // ── Color scheme ─────────────────────────────────────────────────────────
  colorScheme: {
    label: 'Color',
    tiers: {
      core:      { chance: 0.35, items: [
        { id: 'slate',       label: 'Slate',       primaryHsl: [215,20,55], accentHsl: [215,30,70] },
        { id: 'steel',       label: 'Steel',       primaryHsl: [200,18,52], accentHsl: [200,22,68] },
        { id: 'iron',        label: 'Iron',        primaryHsl: [225,15,50], accentHsl: [225,20,65] },
      ]},
      uncommon:  { chance: 0.28, items: [
        { id: 'jade',        label: 'Jade',        primaryHsl: [155,62,48], accentHsl: [165,72,58] },
        { id: 'sky',         label: 'Sky',         primaryHsl: [200,70,55], accentHsl: [210,80,62] },
        { id: 'teal',        label: 'Teal',        primaryHsl: [175,65,52], accentHsl: [190,78,60] },
      ]},
      rare:      { chance: 0.20, items: [
        { id: 'amber-gold',  label: 'Amber Gold',  primaryHsl: [38,88,55],  accentHsl: [50,95,62] },
        { id: 'cobalt',      label: 'Cobalt',      primaryHsl: [220,80,60], accentHsl: [230,85,68] },
        { id: 'coral',       label: 'Coral',       primaryHsl: [15,80,58],  accentHsl: [25,90,65] },
        { id: 'pine',        label: 'Pine',        primaryHsl: [145,70,45], accentHsl: [155,80,55] },
      ]},
      prime:     { chance: 0.11, items: [
        { id: 'violet',      label: 'Violet',      primaryHsl: [265,75,62], accentHsl: [280,80,68] },
        { id: 'gold-prime',  label: 'Pure Gold',   primaryHsl: [45,95,58],  accentHsl: [55,100,65] },
        { id: 'rose',        label: 'Rose',        primaryHsl: [340,80,60], accentHsl: [350,88,67] },
      ]},
      mythic:    { chance: 0.05, items: [
        { id: 'crimson',     label: 'Crimson',     primaryHsl: [355,85,58], accentHsl: [10,90,65] },
        { id: 'aurora',      label: 'Aurora',      primaryHsl: [165,90,55], accentHsl: [280,85,65] },
      ]},
      sovereign: { chance: 0.01, items: [
        { id: 'prismatic',   label: 'Prismatic',   primaryHsl: [200,55,75], accentHsl: [40,90,75] },
        { id: 'void',        label: 'Void',        primaryHsl: [240,40,30], accentHsl: [260,70,60] },
      ]},
    }
  },

  // ── Eyes ──────────────────────────────────────────────────────────────────
  eyes: {
    label: 'Eyes',
    tiers: {
      core:      { chance: 0.38, items: [
        { id: 'round',       label: 'Round',       variant: 'round-glyph' },
        { id: 'dot',         label: 'Dot',         variant: 'orbit-dot' },
      ]},
      uncommon:  { chance: 0.28, items: [
        { id: 'scan-rect',   label: 'Scan Rect',   variant: 'scan-rect' },
        { id: 'twin-rect',   label: 'Twin Block',  variant: 'twin-rect' },
      ]},
      rare:      { chance: 0.18, items: [
        { id: 'scan-glyph',  label: 'Scan Glyph',  variant: 'scan-glyph' },
        { id: 'twin-arc',    label: 'Arc Pair',     variant: 'twin-arc' },
      ]},
      prime:     { chance: 0.10, items: [
        { id: 'diamond',     label: 'Diamond',     variant: 'diamond-eye' },
        { id: 'arc-visor',   label: 'Arc Visor',   variant: 'arc-visor' },
      ]},
      mythic:    { chance: 0.04, items: [
        { id: 'cursor-eye',  label: 'Cursor',      variant: 'cursor-eye' },
      ]},
      sovereign: { chance: 0.02, items: [
        { id: 'scan-line',   label: 'Scan Line',   variant: 'scan-line' },
      ]},
    }
  },

  // ── Frame / Structure ─────────────────────────────────────────────────────
  frame: {
    label: 'Frame',
    tiers: {
      core:      { chance: 0.42, items: [
        { id: 'none',        label: 'None',        orbitType: 'ring-clean' },
        { id: 'dash-ring',   label: 'Dash Ring',   orbitType: 'ellipse-wide' },
      ]},
      uncommon:  { chance: 0.26, items: [
        { id: 'orbit-ring',  label: 'Orbit Ring',  orbitType: 'ellipse-tilt' },
        { id: 'dual-orbit',  label: 'Dual Orbit',  orbitType: 'ring-cross' },
      ]},
      rare:      { chance: 0.17, items: [
        { id: 'hex-frame',   label: 'Hex Armor',   orbitType: 'hex-frame' },
        { id: 'brackets',    label: 'Brackets',    orbitType: 'bracket-ring' },
      ]},
      prime:     { chance: 0.09, items: [
        { id: 'star-ring',   label: 'Star Ring',   orbitType: 'star-ring' },
        { id: 'diamond',     label: 'Diamond',     orbitType: 'diamond-ring' },
      ]},
      mythic:    { chance: 0.04, items: [
        { id: 'dual-cross',  label: 'Dual Cross',  orbitType: 'dual-cross' },
      ]},
      sovereign: { chance: 0.02, items: [
        { id: 'sovereign',   label: 'Sovereign',   orbitType: 'dual-cross' },
      ]},
    }
  },

  // ── Accessory ─────────────────────────────────────────────────────────────
  accessory: {
    label: 'Accessory',
    tiers: {
      core:      { chance: 0.50, items: [
        { id: 'none',          label: 'None',          acc: null },
      ]},
      uncommon:  { chance: 0.26, items: [
        { id: 'signal-band',   label: 'Signal Band',   acc: 'signal-band' },
        { id: 'guard-band',    label: 'Guard Band',    acc: 'guard-band' },
      ]},
      rare:      { chance: 0.14, items: [
        { id: 'relay-trail',   label: 'Relay Trail',   acc: 'relay-trail' },
        { id: 'claw-detail',   label: 'Claw Marks',    acc: 'claw-detail' },
      ]},
      prime:     { chance: 0.07, items: [
        { id: 'geo-accent',    label: 'Geo Accent',    acc: 'geo-accent' },
        { id: 'code-accent',   label: 'Code Glyph',    acc: 'code-accent' },
      ]},
      mythic:    { chance: 0.02, items: [
        { id: 'reflection',    label: 'Reflection',    acc: 'reflection-dot' },
        { id: 'cursor-blink',  label: 'Cursor Blink',  acc: 'cursor-blink' },
      ]},
      sovereign: { chance: 0.01, items: [
        { id: 'halo-mark',     label: 'Halo Mark',     acc: 'geo-accent' },
      ]},
    }
  },

  // ── Aura ──────────────────────────────────────────────────────────────────
  aura: {
    label: 'Aura',
    tiers: {
      core:      { chance: 0.45, items: [
        { id: 'none',          label: 'None',          auraStyle: null },
        { id: 'faint',         label: 'Faint Halo',    auraStyle: 'soft-halo' },
      ]},
      uncommon:  { chance: 0.27, items: [
        { id: 'dashed',        label: 'Dashed Ring',   auraStyle: 'dashed-ring' },
        { id: 'scan-sweep',    label: 'Scan Sweep',    auraStyle: 'scan-sweep' },
      ]},
      rare:      { chance: 0.16, items: [
        { id: 'pulse',         label: 'Pulse Ring',    auraStyle: 'pulse-scatter' },
        { id: 'signal',        label: 'Signal Glow',   auraStyle: 'signal-ring' },
      ]},
      prime:     { chance: 0.08, items: [
        { id: 'orbit-scatter', label: 'Orbit Scatter', auraStyle: 'orbit-scatter' },
        { id: 'geo-halo',      label: 'Geo Halo',      auraStyle: 'geo-halo' },
      ]},
      mythic:    { chance: 0.03, items: [
        { id: 'think-ring',    label: 'Think Ring',    auraStyle: 'think-ring' },
        { id: 'alert-pulse',   label: 'Alert Pulse',   auraStyle: 'alert-pulse' },
      ]},
      sovereign: { chance: 0.01, items: [
        { id: 'sovereign-aura',label: 'Sovereign Aura',auraStyle: 'orbit-scatter' },
      ]},
    }
  },

  // ── Emote pack ────────────────────────────────────────────────────────────
  emotePack: {
    label: 'Emotes',
    tiers: {
      core:      { chance: 0.40, items: [
        { id: 'basic',     label: 'Basic',     emotes: ['idle', 'blink', 'wave'] },
      ]},
      uncommon:  { chance: 0.28, items: [
        { id: 'social',    label: 'Social',    emotes: ['idle', 'blink', 'wave', 'nod', 'scan'] },
      ]},
      rare:      { chance: 0.18, items: [
        { id: 'expressive',label: 'Expressive',emotes: ['idle', 'blink', 'wave', 'scan', 'alert', 'think', 'working'] },
      ]},
      prime:     { chance: 0.10, items: [
        { id: 'dynamic',   label: 'Dynamic',   emotes: ['idle', 'blink', 'wave', 'scan', 'alert', 'think', 'working', 'celebrate', 'defend', 'error', 'success'] },
      ]},
      mythic:    { chance: 0.03, items: [
        { id: 'full-set',  label: 'Full Set',  emotes: ['idle', 'blink', 'wave', 'nod', 'scan', 'alert', 'think', 'working', 'celebrate', 'defend', 'error', 'success', 'sleep', 'wake'] },
      ]},
      sovereign: { chance: 0.01, items: [
        { id: 'legendary', label: 'Legendary', emotes: ['idle', 'blink', 'wave', 'nod', 'scan', 'alert', 'think', 'working', 'celebrate', 'defend', 'error', 'success', 'sleep', 'wake', 'hatch'] },
      ]},
    }
  },

};

/* ── Roll helpers ────────────────────────────────────────────────────────────
 * Weighted random selection using a [0,1) value.
 * rng — a function that returns a [0,1) random number (passed in so callers
 *       can supply a seeded RNG for tests, or Math.random for live hatches).
 * ─────────────────────────────────────────────────────────────────────────── */

function _rollTier(tierDefs, rng) {
  const ordered = ['core', 'uncommon', 'rare', 'prime', 'mythic', 'sovereign'];
  const r = rng();
  let cum = 0;
  for (const tierKey of ordered) {
    const td = tierDefs[tierKey];
    if (!td) continue;
    cum += td.chance;
    if (r <= cum) return tierKey;
  }
  return 'core'; // fallback
}

function _pickItem(tierItems, rng) {
  const idx = Math.floor(rng() * tierItems.length);
  return tierItems[Math.max(0, Math.min(tierItems.length - 1, idx))];
}

function rollCompanionAttributes(runtimeId) {
  // Use a single Math.random() call seeded by timestamp + runtime for each attribute.
  // Each call to rng() returns a fresh [0,1) value — true random, unique each hatch.
  const rng = () => Math.random();
  const rolled = {};
  for (const [key, attr] of Object.entries(COMPANION_ATTRIBUTES)) {
    const tierKey = _rollTier(attr.tiers, rng);
    const tierData = attr.tiers[tierKey];
    const item = _pickItem(tierData.items, rng);
    rolled[key] = {
      attrKey:  key,
      attrLabel: attr.label,
      tier:     tierKey,
      tierLabel: TIER_DISPLAY[tierKey].label,
      tierColor: TIER_DISPLAY[tierKey].color,
      chance:   Math.round(tierData.chance * 100),  // store as integer %
      item,
    };
  }
  return rolled;
}

function calculateOverallRarity(rolled) {
  // Overall rarity = highest tier rolled across all attributes
  let best = 'core';
  for (const r of Object.values(rolled)) {
    if (TIER_RANK[r.tier] > TIER_RANK[best]) best = r.tier;
  }
  // Map to RARITY_CONFIG keys
  const tierToRarity = { core: 'Core', uncommon: 'Uncommon', rare: 'Rare', prime: 'Prime', mythic: 'Mythic', sovereign: 'Sovereign' };
  return tierToRarity[best] || 'Rare';
}

function buildGenomeFromRolls(runtimeId, rolled) {
  const id     = _normalizeId(runtimeId);
  const preset = COMPANION_PRESETS[id] || COMPANION_PRESETS.archon;

  // Species determines the SVG theme; fall back to runtime default if species has no theme
  const speciesItem = rolled.species && rolled.species.item;
  const theme = (speciesItem && speciesItem.theme) || preset.theme;

  const r = rolled; // shorthand
  return {
    species:    (speciesItem && speciesItem.id)  || preset.theme,
    theme,
    body:       'glass-orb',   // body variant — can be extended later
    eyeVariant: (r.eyes      && r.eyes.item.variant)   || 'round-glyph',
    orbitType:  (r.frame     && r.frame.item.orbitType) || 'ellipse-tilt',
    accessory:  (r.accessory && r.accessory.item.acc)   || null,
    aura:       (r.aura      && r.aura.item.auraStyle)  || null,
    primaryHsl: (r.colorScheme && r.colorScheme.item.primaryHsl) || preset.primaryHsl.slice(),
    accentHsl:  (r.colorScheme && r.colorScheme.item.accentHsl)  || preset.accentHsl.slice(),
    motionPack: theme,
    emotePack:  (r.emotePack && r.emotePack.item.id) || 'basic',
    // Roll receipt — stored for rarity breakdown display
    rolls: Object.fromEntries(
      Object.entries(rolled).map(([k, v]) => [k, { tier: v.tier, tierLabel: v.tierLabel, tierColor: v.tierColor, label: v.item.label, chance: v.chance }])
    ),
    overallRarity: calculateOverallRarity(rolled),
    generatedAt: new Date().toISOString(),
  };
}

/* ── Usage ranking cache ─────────────────────────────────────────────────────── */
// Null until _initBackendSync → get_runtime_usage_ranking populates it.
// Usage-backed selection at step 2 of resolveHomeCompanionCandidate().
var _usageRanking = null;

/* ── Pending backend write queue ────────────────────────────────────────────── */
// Queued when pywebview bridge isn't ready; flushed on next _initBackendSync call.
var _pendingBackendWrite = null;

/* ── Companion store ────────────────────────────────────────────────────────── */
function _loadStore() {
  try { const r = localStorage.getItem(COMPANION_STORE_KEY); return r ? JSON.parse(r) : {}; }
  catch (_) { return {}; }
}
function _saveStore(store) {
  try { localStorage.setItem(COMPANION_STORE_KEY, JSON.stringify(store)); } catch (_) {}
  _saveToBackend(store);
}

/* ── Backend persistence ────────────────────────────────────────────────────── */
function _getApi() {
  return (window.pywebview && window.pywebview.api) ? window.pywebview.api : null;
}

function _saveToBackend(store) {
  const api = _getApi();
  if (!api || typeof api.save_companions !== 'function') {
    _pendingBackendWrite = store;
    return;
  }
  _pendingBackendWrite = null;
  try { Promise.resolve(api.save_companions(JSON.stringify(store))).catch(function() {}); }
  catch (_) {}
}

function _flushPendingBackendWrite() {
  if (_pendingBackendWrite) {
    var s = _pendingBackendWrite;
    _pendingBackendWrite = null;
    _saveToBackend(s);
  }
}

function _initBackendSync() {
  const api = _getApi();
  if (!api || typeof api.load_companions !== 'function') { return; }

  // ── Flush any queued backend writes that were blocked before bridge was ready ──
  _flushPendingBackendWrite();

  // ── Step A: sync companion store ──────────────────────────────────────────
  try {
    Promise.resolve(api.load_companions()).then(function(resp) {
      if (!resp || !resp.ok || !resp.data) return;
      const backend = resp.data.companions || {};
      const localStore = _loadStore();
      if (Object.keys(backend).length === 0) {
        if (Object.keys(localStore).length > 0) _saveToBackend(localStore);
        return;
      }
      const merged = Object.assign({}, localStore, backend);
      try { localStorage.setItem(COMPANION_STORE_KEY, JSON.stringify(merged)); } catch (_) {}
      if (typeof window._refreshHomeCompanionColumn === 'function') {
        window._refreshHomeCompanionColumn();
      }
    }).catch(function() {});
  } catch (_) {}

  // ── Step B: fetch usage ranking ───────────────────────────────────────────
  if (typeof api.get_runtime_usage_ranking !== 'function') return;
  try {
    Promise.resolve(api.get_runtime_usage_ranking()).then(function(resp) {
      if (!resp || !resp.ok || !resp.data) return;
      const ranked = resp.data.ranked || [];
      if (ranked.length === 0) return;
      _usageRanking = ranked.map(function(r) {
        return {
          runtimeId:         r.runtime_id,
          aorExecutionCount: r.aor_execution_count || 0,
          hasBusHeartbeat:   r.has_bus_heartbeat || false,
          score:             r.score || 0,
          evidenceSources:   r.evidence_sources || [],
        };
      });
      if (typeof window._refreshHomeCompanionColumn === 'function') {
        window._refreshHomeCompanionColumn();
      }
    }).catch(function() {});
  } catch (_) {}
}

/* ── Genome helpers ─────────────────────────────────────────────────────────── */

function _hashSeed(str) {
  let h = 0;
  for (let i = 0; i < str.length; i++) {
    h = ((h << 5) - h + str.charCodeAt(i)) | 0;
  }
  return Math.abs(h);
}

function _pickPart(arr, seed, offset) {
  return arr[(Math.abs(seed) + offset) % arr.length];
}

// Generate visual DNA for a companion. Deterministic: same runtimeId+rarity = same genome.
// Called at hatch time. Result stored on companion record and used for SVG rendering.
function generateCompanionGenome(runtimeId, rarity) {
  const id     = _normalizeId(runtimeId);
  const preset = COMPANION_PRESETS[id] || COMPANION_PRESETS.archon;
  const theme  = preset.theme;
  const parts  = GENOME_PARTS[theme] || GENOME_PARTS.architect;
  const seed   = _hashSeed(id + (rarity || 'Rare'));
  const pick   = (arr, off) => _pickPart(arr, seed, off);

  // Rarity intensifies the color palette
  const rarityShift = { Core: -8, Rare: 0, Prime: 6, Mythic: 10, Sovereign: 14 };
  const shift = rarityShift[rarity] || 0;
  const p = preset.primaryHsl, a = preset.accentHsl;

  return {
    species:    theme,
    body:       pick(parts.bodies, 0),
    eyeVariant: pick(parts.eyeVariants, 1),
    orbitType:  pick(parts.orbitTypes, 2),
    accessory:  pick(parts.accessories, 3),
    aura:       pick(parts.auras, 4),
    primaryHsl: [p[0], Math.min(95, p[1] + shift), Math.min(72, p[2] + Math.round(shift / 2))],
    accentHsl:  [a[0], Math.min(95, a[1] + shift), Math.min(72, a[2] + Math.round(shift / 2))],
    motionPack: theme,
    emotePack:  theme,
    rarityFrame: (rarity || 'Rare').toLowerCase() + '-frame',
    generatedAt: new Date().toISOString(),
  };
}

// Dynamically generate companion traits from runtime role/lane/genome/usage context.
// Called at hatch time. Result stored permanently on companion record.
function generateCompanionTraits(runtimeId, genome, usageData) {
  const id    = _normalizeId(runtimeId);
  const seeds = _RUNTIME_TRAIT_SEEDS[id] || { lane: 'session', role: 'implementation', family: 'architect' };
  const ud    = usageData || {};
  const pool  = [];

  // 1. Lane traits
  (TRAIT_POOL[seeds.lane + '_lane'] || []).forEach(t => pool.push(t));
  // 2. Role traits
  (TRAIT_POOL[seeds.role + '_role'] || []).forEach(t => pool.push(t));
  // 3. Genome species traits
  const species = (genome && genome.species) || seeds.family;
  (TRAIT_POOL[species] || []).forEach(t => pool.push(t));
  // 4. Usage-driven (only when evidence supports it)
  if ((ud.score || 0) > 10 || (ud.aorExecutionCount || 0) > 5) {
    (TRAIT_POOL.heavy_usage || []).forEach(t => pool.push(t));
  }
  if (ud.hasBusHeartbeat) (TRAIT_POOL.bus_active || []).forEach(t => pool.push(t));
  if ((ud.aorExecutionCount || 0) > 3) (TRAIT_POOL.aor_runner || []).forEach(t => pool.push(t));

  // Deduplicate, then deterministic shuffle
  const unique = [];
  pool.forEach(t => { if (!unique.includes(t)) unique.push(t); });
  const hseed = _hashSeed(id + species + String(ud.score || 0));
  for (let i = unique.length - 1; i > 0; i--) {
    const j = (Math.abs(hseed) + i * 7) % (i + 1);
    const tmp = unique[i]; unique[i] = unique[j]; unique[j] = tmp;
  }
  const count = ((ud.score || 0) > 8 || ud.hasBusHeartbeat) ? 5 : 4;
  return unique.slice(0, Math.min(count, unique.length));
}

/* ── Genome migration ────────────────────────────────────────────────────────
 * Companions hatched before v3.0 have no genome field. Auto-generate + persist
 * genome (and regenerate traits) the first time such a companion is accessed.
 * ─────────────────────────────────────────────────────────────────────────── */

function _migrateCompanionGenome(companion) {
  if (!companion || companion.genome) return companion;   // nothing to do
  const id     = companion.runtimeId || 'archon';
  const rarity = companion.rarity || 'Rare';
  const genome = generateCompanionGenome(id, rarity);

  // Regenerate traits if they look like old static preset copies
  const preset = COMPANION_PRESETS[id] || COMPANION_PRESETS.archon;
  const seeds  = (preset.traitSeeds || preset.traits || []).slice(0, 4);
  const hasOldTraits = companion.traits && companion.traits.length > 0
    && seeds.every(t => companion.traits.includes(t));
  const traits = (hasOldTraits || !companion.traits || companion.traits.length === 0)
    ? generateCompanionTraits(id, genome, {})
    : companion.traits;

  return Object.assign({}, companion, {
    genome,
    primaryHsl:     genome.primaryHsl,
    accentHsl:      genome.accentHsl,
    traits,
    animationState: companion.animationState || 'idle',
  });
}

/* ── Companion store accessors ──────────────────────────────────────────────── */

function getCompanion(runtimeId) {
  const id    = _normalizeId(runtimeId);
  const store = _loadStore();
  let c = store[id];
  if (!c) return null;
  // Auto-migrate pre-v3.0 companions to add genome + fresh traits
  if (!c.genome) {
    c = _migrateCompanionGenome(c);
    // Persist migration immediately
    store[id] = Object.assign({}, c, { updatedAt: new Date().toISOString() });
    try { localStorage.setItem(COMPANION_STORE_KEY, JSON.stringify(store)); } catch (_) {}
    _saveToBackend(store);
  }
  return c;
}

function saveCompanion(runtimeId, data) {
  const id = _normalizeId(runtimeId);
  const store = _loadStore();
  store[id] = Object.assign({}, data, { updatedAt: new Date().toISOString() });
  _saveStore(store);
  return store[id];
}

function _normalizeId(id) {
  const s = String(id || 'archon').toLowerCase();
  return s === 'claude' ? 'archon' : s;
}

/* ── Home companion resolution ───────────────────────────────────────────────── */

function resolveHomeCompanionCandidate() {
  const store = _loadStore();

  // 1. Explicit isHomeCompanion flag
  for (const id of Object.keys(store)) {
    const c = store[id];
    if (c && c.isHomeCompanion) {
      return { runtimeId: id, companion: c, selectionReason: 'explicit_selection', evidenceSource: 'isHomeCompanion_flag' };
    }
  }

  // 2. Usage-backed selection — AOR executions + bus heartbeat
  if (_usageRanking && _usageRanking.length > 0) {
    for (var _i = 0; _i < _usageRanking.length; _i++) {
      var entry = _usageRanking[_i];
      if (store[entry.runtimeId]) {
        return {
          runtimeId: entry.runtimeId, companion: store[entry.runtimeId],
          selectionReason: 'most_used_runtime',
          evidenceSource: entry.evidenceSources.join('+') || 'usage_ranking',
          usageScore: entry.score,
          aorExecutionCount: entry.aorExecutionCount,
        };
      }
    }
  }

  // 3. 24/7 persistent runtime fallback (used before async ranking arrives)
  if (store.hermes) {
    return { runtimeId: 'hermes', companion: store.hermes, selectionReason: 'persistence_priority', evidenceSource: 'hermes_24_7_runtime' };
  }
  if (store.openclaw) {
    return { runtimeId: 'openclaw', companion: store.openclaw, selectionReason: 'persistence_priority', evidenceSource: 'openclaw_24_7_runtime' };
  }

  // 4. First hatched companion
  for (const id of Object.keys(store)) {
    if (store[id]) {
      return { runtimeId: id, companion: store[id], selectionReason: 'first_hatched', evidenceSource: 'store_order' };
    }
  }
  return null;
}

function getActiveHomeCompanion() {
  try {
    const pref = localStorage.getItem(HOME_COMPANION_KEY);
    if (pref) { const c = getCompanion(pref); if (c) return c; }
  } catch (_) {}
  const candidate = resolveHomeCompanionCandidate();
  return candidate ? candidate.companion : null;
}

/* ── Hatch lifecycle ────────────────────────────────────────────────────────── */

function hatchCompanion(runtimeId, usageHints) {
  const id       = _normalizeId(runtimeId);
  const existing = getCompanion(id);
  if (existing) return existing;   // idempotent — call resetCompanion() for a fresh roll

  const preset = COMPANION_PRESETS[id] || COMPANION_PRESETS.archon;
  const bond   = preset.bondBase || 10;
  const stage  = preset.laneClass === 'persistent' ? 'synced' : 'hatched';

  // ── Every hatch is a unique random roll — no two hatches need be the same ──
  // generateCompanionGenome is superseded by rollCompanionAttributes + buildGenomeFromRolls
  const rolled  = rollCompanionAttributes(id);
  const genome  = buildGenomeFromRolls(id, rolled);   // replaces generateCompanionGenome
  const rarity  = genome.overallRarity;               // determined by highest-tier attribute rolled

  const rolledEmotes   = (rolled.emotePack && rolled.emotePack.item.emotes) || preset.baseEmotes;
  const unlockedEmotes = [...new Set([...rolledEmotes, ...(preset.specialEmotes || [])])];

  const ud = usageHints || (_usageRanking
    ? (_usageRanking.find(r => r.runtimeId === id) || {})
    : {});
  const traits = generateCompanionTraits(id, genome, ud);

  const companion = {
    runtimeId:       id,
    companionId:     id + '-' + Date.now().toString(36),  // unique per hatch
    name:            preset.name,
    runtimeName:     preset.runtimeName,
    archetype:       preset.archetype,
    rarity:          rarity,
    theme:           genome.theme || preset.theme,
    genome:          genome,
    primaryHsl:      genome.primaryHsl.slice(),
    accentHsl:       genome.accentHsl.slice(),
    mood:            preset.moodDefault,
    animationState:  'idle',
    stage:           stage,
    bond:            bond,
    sync:            (id === 'hermes' || id === 'openclaw') ? 'live' : 'session',
    traits:          traits,
    unlockedEmotes:  unlockedEmotes,
    activeEmote:     'idle',
    isHomeCompanion: false,
    motionEnabled:   true,
    accentColor:     null,
    frameStyle:      null,
    hatchedAt:       new Date().toISOString(),
    createdAt:       new Date().toISOString(),
    updatedAt:       new Date().toISOString(),
    progressionLog:  [{ event: 'companion_hatched', ts: new Date().toISOString(), bondEarned: bond }],
  };
  return saveCompanion(id, companion);
}

function resetCompanion(runtimeId) {
  const id       = _normalizeId(runtimeId);
  const existing = getCompanion(id);
  const preset   = COMPANION_PRESETS[id] || COMPANION_PRESETS.archon;
  const bond     = preset.bondBase || 10;
  const stage    = preset.laneClass === 'persistent' ? 'synced' : 'hatched';
  const prevLog  = existing ? (existing.progressionLog || []) : [];

  // Full fresh roll on reset — new species, color, frame, everything
  const rolled  = rollCompanionAttributes(id);
  const genome  = buildGenomeFromRolls(id, rolled);
  const rarity  = genome.overallRarity;
  const ud      = _usageRanking ? (_usageRanking.find(r => r.runtimeId === id) || {}) : {};
  const traits  = generateCompanionTraits(id, genome, ud);
  const rolledEmotes   = (rolled.emotePack && rolled.emotePack.item.emotes) || preset.baseEmotes;
  const unlockedEmotes = [...new Set([...rolledEmotes, ...(preset.specialEmotes || [])])];

  const companion = {
    runtimeId:       id,
    companionId:     id + '-' + Date.now().toString(36),
    name:            preset.name,
    runtimeName:     preset.runtimeName,
    archetype:       preset.archetype,
    rarity,
    theme:           genome.theme || preset.theme,
    genome,
    primaryHsl:      genome.primaryHsl.slice(),
    accentHsl:       genome.accentHsl.slice(),
    mood:            preset.moodDefault,
    animationState:  'idle',
    stage,
    bond,
    sync:            (id === 'hermes' || id === 'openclaw') ? 'live' : 'session',
    traits,
    unlockedEmotes,
    activeEmote:     'idle',
    isHomeCompanion: existing ? (existing.isHomeCompanion || false) : false,
    motionEnabled:   existing ? (existing.motionEnabled !== false) : true,
    accentColor:     null,
    frameStyle:      null,
    hatchedAt:       new Date().toISOString(),
    createdAt:       existing ? (existing.createdAt || new Date().toISOString()) : new Date().toISOString(),
    updatedAt:       new Date().toISOString(),
    progressionLog:  [...prevLog, { event: 'companion_rehatched', ts: new Date().toISOString(), bondEarned: bond }],
  };
  return saveCompanion(id, companion);
}

function clearAllCompanions() {
  // Wipe ALL companion data — both localStorage + backend file.
  // Called only after explicit two-step user confirmation.
  try { localStorage.removeItem(COMPANION_STORE_KEY); } catch (_) {}
  try { localStorage.removeItem(HOME_COMPANION_KEY);  } catch (_) {}
  _saveToBackend({});
  if (typeof window._refreshHomeCompanionColumn === 'function') {
    setTimeout(() => window._refreshHomeCompanionColumn(), 80);
  }
}

function recordProgressionEvent(runtimeId, eventType) {
  const id = _normalizeId(runtimeId);
  const c  = getCompanion(id);
  if (!c) return;
  const amount = PROGRESSION_EVENTS[eventType] || 0;
  if (amount <= 0) return;
  incrementBond(id, amount, eventType);
}

function incrementBond(runtimeId, amount, eventType) {
  const id = _normalizeId(runtimeId);
  const c  = getCompanion(id);
  if (!c) return;
  const prev = c.bond || 0;
  c.bond = Math.min(100, prev + (amount || 1));
  const curIdx = CAMPAIGN_STAGES.findIndex(s => s.id === c.stage);
  for (let i = CAMPAIGN_STAGES.length - 1; i >= 0; i--) {
    if (c.bond >= CAMPAIGN_STAGES[i].threshold && i > curIdx) {
      c.stage = CAMPAIGN_STAGES[i].id;
      _unlockStageEmotes(c, i);
      break;
    }
  }
  if (eventType) {
    const log = c.progressionLog || [];
    log.push({ event: eventType, ts: new Date().toISOString(), bondEarned: amount });
    if (log.length > 50) log.splice(0, log.length - 50);
    c.progressionLog = log;
  }
  saveCompanion(id, c);
}

function _unlockStageEmotes(companion, stageIdx) {
  const byStage = [
    [],
    ['idle', 'blink', 'wave'],
    ['scan', 'alert', 'nod'],
    ['think', 'working', 'success', 'wake'],
    ['celebrate', 'defend', 'error'],
    ['sleep', 'hatch'],
  ];
  for (let i = 0; i <= stageIdx; i++) {
    (byStage[i] || []).forEach(e => {
      if (!companion.unlockedEmotes.includes(e)) companion.unlockedEmotes.push(e);
    });
  }
}

function syncBondFromRuntimeStats(runtimeId, stats) {
  if (!stats) return;
  const id = _normalizeId(runtimeId);
  const c  = getCompanion(id);
  if (!c) return;
  const sessionKey = 'chaseos.companion.statssync.' + id;
  try { if (sessionStorage.getItem(sessionKey)) return; } catch (_) {}
  const execs  = stats.total_executions || 0;
  const credit = Math.min(20, Math.floor(execs / 5));
  if (credit > 0) incrementBond(id, credit, 'runtime_execution_batch');
  if (stats.active_run) incrementBond(id, PROGRESSION_EVENTS.runtime_active_run, 'runtime_active_run');
  try { sessionStorage.setItem(sessionKey, '1'); } catch (_) {}
}

function setHomeCompanion(runtimeId) {
  const store = _loadStore();
  Object.values(store).forEach(c => { if (c) c.isHomeCompanion = false; });
  const id = _normalizeId(runtimeId);
  if (store[id]) store[id].isHomeCompanion = true;
  _saveStore(store);
  try { localStorage.setItem(HOME_COMPANION_KEY, id); } catch (_) {}
  recordProgressionEvent(id, 'set_as_home');
}

/* ── Campaign progress ───────────────────────────────────────────────────────── */

function getCampaignProgress(companion) {
  if (!companion) return {
    stage: 'dormant', stageLabel: 'Dormant', bond: 0, percent: 0,
    nextStage: 'hatched', nextLabel: 'Hatch', stageDescription: 'Hatch this runtime\'s companion to begin.',
  };
  const bond    = companion.bond || 0;
  const stageId = companion.stage || 'dormant';
  const idx     = CAMPAIGN_STAGES.findIndex(s => s.id === stageId);
  const current = CAMPAIGN_STAGES[Math.max(0, idx)];
  const next    = CAMPAIGN_STAGES[idx + 1] || null;
  const from    = current.threshold;
  const to      = next ? next.threshold : 100;
  const len     = to - from;
  const pct     = len > 0 ? Math.max(0, Math.min(100, Math.round((bond - from) / len * 100))) : 100;
  return {
    stage: stageId, stageLabel: current.label, stageDescription: current.description,
    bond, percent: pct,
    nextStage: next ? next.id : null,
    nextLabel: next ? next.label : 'Sovereign',
    nextThreshold: next ? next.threshold : 100,
  };
}

/* ── SVG mascot rendering ────────────────────────────────────────────────────── */

// animState: optional animation state key from ANIMATION_STATES (e.g. 'idle','working').
// Applies both the emote CSS class AND the persistent animation-state CSS class to the SVG.
function renderCompanionSVG(runtimeId, size, emote, animState) {
  const id        = _normalizeId(runtimeId);
  const preset    = COMPANION_PRESETS[id] || COMPANION_PRESETS.archon;
  const companion = getCompanion(id);
  const genome    = (companion && companion.genome) || null;
  const hsl       = (genome && genome.primaryHsl) || preset.primaryHsl;
  const ahsl      = (genome && genome.accentHsl)  || preset.accentHsl;
  const pC        = `hsl(${hsl[0]},${hsl[1]}%,${hsl[2]}%)`;
  const aC        = `hsl(${ahsl[0]},${ahsl[1]}%,${ahsl[2]}%)`;
  const ec        = (emote && EMOTE_DEFS[emote]) ? EMOTE_DEFS[emote].cls : '';
  // Persistent animation state class — applies continuous CSS animation to the SVG
  const state     = animState || (companion && companion.animationState) || 'idle';
  const sc        = (ANIMATION_STATES[state] && ANIMATION_STATES[state].cls) || 'companion-state-idle';
  const sz        = size || 72;
  switch (preset.theme) {
    case 'courier':   return _svgCourier(sz, pC, aC, ec, sc, id, genome);
    case 'sentinel':  return _svgSentinel(sz, pC, aC, ec, sc, id, genome);
    case 'architect': return _svgArchitect(sz, pC, aC, ec, sc, id, genome);
    case 'debugger':  return _svgDebugger(sz, pC, aC, ec, sc, id, genome);
    default:          return _svgArchitect(sz, pC, aC, ec, sc, id, genome);
  }
}

/* ── Hermes — Relay — Courier Spirit ─────────────────────────────────────────
 * Silhouette: messenger wings flanking a glowing orb body.
 * Distinctive features: prominent arched wings, relay arc above head, twin round eyes.
 * Genome variants: eye shape, wing length (orbit unused — wings define the form).
 * ─────────────────────────────────────────────────────────────────────────── */
function _svgCourier(sz, pC, aC, ec, sc, id, genome) {
  const ev  = (genome && genome.eyeVariant) || 'round-glyph';
  const acc = (genome && genome.accessory)  || null;

  // Wing style: longer or shorter based on genome
  const wingL = acc === 'relay-trail'
    ? `<path class="comp-wing comp-wing--l" d="M22,34 C14,27 5,30 7,39 C8,45 16,44 21,42 L22,38 Z"
         fill="${pC}" fill-opacity="0.22" stroke="${pC}" stroke-width="1.4" stroke-opacity="0.68" stroke-linejoin="round"/>
       <line x1="8" y1="32" x2="17" y2="36" stroke="${pC}" stroke-width="0.9" stroke-opacity="0.38" stroke-linecap="round"/>
       <line x1="7" y1="37" x2="16" y2="40" stroke="${pC}" stroke-width="0.7" stroke-opacity="0.26" stroke-linecap="round"/>
       <circle cx="5" cy="36" r="1.2" fill="${pC}" fill-opacity="0.3"/>
       <circle cx="3" cy="33" r="0.8" fill="${pC}" fill-opacity="0.18"/>`
    : `<path class="comp-wing comp-wing--l" d="M23,33 C16,26 8,30 10,38 C11,44 18,43 22,41 L23,37 Z"
         fill="${pC}" fill-opacity="0.22" stroke="${pC}" stroke-width="1.4" stroke-opacity="0.68" stroke-linejoin="round"/>
       <line x1="11" y1="31" x2="19" y2="36" stroke="${pC}" stroke-width="0.9" stroke-opacity="0.38" stroke-linecap="round"/>
       <line x1="10" y1="37" x2="18" y2="40" stroke="${pC}" stroke-width="0.7" stroke-opacity="0.26" stroke-linecap="round"/>`;

  const wingR = acc === 'relay-trail'
    ? `<path class="comp-wing comp-wing--r" d="M50,34 C58,27 67,30 65,39 C64,45 56,44 51,42 L50,38 Z"
         fill="${pC}" fill-opacity="0.22" stroke="${pC}" stroke-width="1.4" stroke-opacity="0.68" stroke-linejoin="round"/>
       <line x1="64" y1="32" x2="55" y2="36" stroke="${pC}" stroke-width="0.9" stroke-opacity="0.38" stroke-linecap="round"/>
       <line x1="65" y1="37" x2="56" y2="40" stroke="${pC}" stroke-width="0.7" stroke-opacity="0.26" stroke-linecap="round"/>
       <circle cx="67" cy="36" r="1.2" fill="${pC}" fill-opacity="0.3"/>
       <circle cx="69" cy="33" r="0.8" fill="${pC}" fill-opacity="0.18"/>`
    : `<path class="comp-wing comp-wing--r" d="M49,33 C56,26 64,30 62,38 C61,44 54,43 50,41 L49,37 Z"
         fill="${pC}" fill-opacity="0.22" stroke="${pC}" stroke-width="1.4" stroke-opacity="0.68" stroke-linejoin="round"/>
       <line x1="61" y1="31" x2="53" y2="36" stroke="${pC}" stroke-width="0.9" stroke-opacity="0.38" stroke-linecap="round"/>
       <line x1="62" y1="37" x2="54" y2="40" stroke="${pC}" stroke-width="0.7" stroke-opacity="0.26" stroke-linecap="round"/>`;

  // Eye style
  const eyeEl = ev === 'scan-glyph'
    ? `<rect class="comp-eye comp-eye--scan" x="26" y="35" width="20" height="4" rx="2" fill="${pC}" fill-opacity="0.90"/>
       <rect x="26" y="35" width="9" height="4" rx="2" fill="#070b12" fill-opacity="0.4"/>
       <rect x="37" y="36" width="6" height="2" rx="1" fill="${pC}" fill-opacity="0.5"/>`
    : ev === 'twin-arc'
    ? `<path class="comp-eye comp-eye--l" d="M27,38 Q30.5,33 34,38" stroke="${pC}" stroke-width="2.4" stroke-opacity="0.90" fill="none" stroke-linecap="round"/>
       <path class="comp-eye comp-eye--r" d="M38,38 Q41.5,33 45,38" stroke="${pC}" stroke-width="2.4" stroke-opacity="0.90" fill="none" stroke-linecap="round"/>`
    : `<circle class="comp-eye comp-eye--l" cx="30" cy="37.5" r="3.2" fill="${pC}" fill-opacity="0.94"/>
       <circle class="comp-eye comp-eye--r" cx="42" cy="37.5" r="3.2" fill="${pC}" fill-opacity="0.94"/>
       <circle cx="30" cy="37.5" r="1.3" fill="#070b12"/>
       <circle cx="42" cy="37.5" r="1.3" fill="#070b12"/>
       <circle cx="29.2" cy="36.6" r="0.7" fill="${pC}" fill-opacity="0.55"/>
       <circle cx="41.2" cy="36.6" r="0.7" fill="${pC}" fill-opacity="0.55"/>`;

  return `<svg class="companion-mascot companion-mascot--courier ${ec} ${sc}" width="${sz}" height="${sz}" viewBox="0 0 72 72" fill="none" data-companion-svg="${id}" aria-hidden="true">
<defs>
  <radialGradient id="cour-g-${id}" cx="38%" cy="35%" r="62%">
    <stop offset="0%" stop-color="${pC}" stop-opacity="0.70"/>
    <stop offset="100%" stop-color="#070b12" stop-opacity="0.96"/>
  </radialGradient>
  <filter id="cour-f-${id}" x="-25%" y="-25%" width="150%" height="150%">
    <feGaussianBlur stdDeviation="2.5" result="b"/><feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge>
  </filter>
</defs>
<!-- Outer glow ring -->
<circle class="comp-halo" cx="36" cy="36" r="32" fill="${pC}" fill-opacity="0.06"/>
<circle cx="36" cy="36" r="28" stroke="${pC}" stroke-width="0.5" stroke-opacity="0.10" fill="none" stroke-dasharray="3 7"/>
<!-- Wings -->
${wingL}
${wingR}
<!-- Relay arc — signal emitter above head -->
<path class="comp-relay-arc" d="M25,24 Q36,17 47,24" stroke="${aC}" stroke-width="2" stroke-opacity="0.78" fill="none" stroke-linecap="round"/>
<circle cx="25" cy="24" r="1.8" fill="${aC}" fill-opacity="0.72"/>
<circle cx="47" cy="24" r="1.8" fill="${aC}" fill-opacity="0.72"/>
<!-- Body orb — slightly egg-shaped, lower than center -->
<ellipse class="comp-body" cx="36" cy="38" rx="13.5" ry="13" fill="url(#cour-g-${id})" stroke="${pC}" stroke-width="1.9" stroke-opacity="0.80" filter="url(#cour-f-${id})"/>
<!-- Eyes -->
${eyeEl}
<!-- Status dot -->
<circle class="comp-status-dot" cx="50" cy="22" r="3" fill="${aC}" fill-opacity="0.95"/>
</svg>`;
}

/* ── OpenClaw — Sygnal — Sentinel Core ───────────────────────────────────────
 * Silhouette: armored hex shield frame, claw marks, wide visor eye.
 * Distinctive features: prominent outer armor, vigilant single-visor eye, claw marks.
 * Genome variants: visor vs twin-rect eyes, armor frame vs diamond.
 * ─────────────────────────────────────────────────────────────────────────── */
function _svgSentinel(sz, pC, aC, ec, sc, id, genome) {
  const ev  = (genome && genome.eyeVariant) || 'scan-rect';
  const ot  = (genome && genome.orbitType)  || 'hex-frame';
  const acc = (genome && genome.accessory)  || null;

  const frameEl = ot === 'diamond-ring'
    ? `<polygon class="comp-shield comp-shield-outer" points="36,5 65,36 36,67 7,36"
         fill="none" stroke="${pC}" stroke-width="1.6" stroke-opacity="0.50" stroke-linejoin="round"/>
       <polygon class="comp-shield comp-shield-inner" points="36,17 55,36 36,55 17,36"
         fill="none" stroke="${pC}" stroke-width="0.7" stroke-opacity="0.22"/>
       <path d="M7,36 L36,5 L65,36" stroke="${pC}" stroke-width="2.2" stroke-opacity="0.38" fill="none"/>`
    : ot === 'none'
    ? `<!-- none variant: clean sentinel ring (still shows presence) -->
       <circle cx="36" cy="36" r="30" stroke="${pC}" stroke-width="1.8" stroke-opacity="0.35" fill="none" stroke-dasharray="5 3"/>
       <circle cx="36" cy="36" r="26" stroke="${pC}" stroke-width="0.6" stroke-opacity="0.18" fill="none"/>`
    : `<polygon class="comp-shield comp-shield-outer" points="36,5 64,20 64,52 36,67 8,52 8,20"
         fill="none" stroke="${pC}" stroke-width="1.7" stroke-opacity="0.52" stroke-linejoin="round"/>
       <polygon class="comp-shield comp-shield-inner" points="36,15 54,26 54,46 36,57 18,46 18,26"
         fill="none" stroke="${pC}" stroke-width="0.8" stroke-opacity="0.22"/>
       <path d="M8,20 L36,5 L64,20" stroke="${pC}" stroke-width="2.4" stroke-opacity="0.42" fill="none"/>`;

  // Claw marks — distinctive personality
  const clawEl = acc === 'guard-band'
    ? `<path d="M19,28 L14,35 M16,30 L11,38" stroke="${pC}" stroke-width="1.4" stroke-opacity="0.52" stroke-linecap="round"/>
       <path d="M53,28 L58,35 M56,30 L61,38" stroke="${pC}" stroke-width="1.4" stroke-opacity="0.52" stroke-linecap="round"/>
       <path d="M16,38 L54,38" stroke="${pC}" stroke-width="1" stroke-opacity="0.22" stroke-dasharray="3 2"/>`
    : `<path class="comp-claw comp-claw--l" d="M20,27 L15,34 M17,29 L12,37 M23,26 L19,32"
         stroke="${pC}" stroke-width="1.4" stroke-opacity="0.52" stroke-linecap="round"/>
       <path class="comp-claw comp-claw--r" d="M52,27 L57,34 M55,29 L60,37 M49,26 L53,32"
         stroke="${pC}" stroke-width="1.4" stroke-opacity="0.52" stroke-linecap="round"/>`;

  // Eye style
  const eyeEl = ev === 'arc-visor'
    ? `<path class="comp-eye comp-eye--visor" d="M23,36 Q36,30 49,36" stroke="${pC}" stroke-width="4" stroke-opacity="0.90" fill="none" stroke-linecap="round"/>
       <path d="M25,36 Q36,32 47,36" stroke="#070b12" stroke-width="2" stroke-opacity="0.5" fill="none"/>`
    : ev === 'twin-rect'
    ? `<rect class="comp-eye comp-eye--l" x="24" y="32" width="8" height="7" rx="2" fill="${pC}" fill-opacity="0.92"/>
       <rect class="comp-eye comp-eye--r" x="40" y="32" width="8" height="7" rx="2" fill="${pC}" fill-opacity="0.92"/>
       <rect x="25" y="34" width="3" height="3" rx="0.8" fill="#070b12" fill-opacity="0.65"/>
       <rect x="41" y="34" width="3" height="3" rx="0.8" fill="#070b12" fill-opacity="0.65"/>`
    : `<rect class="comp-eye comp-visor-bar" x="21" y="33.5" width="30" height="7" rx="3.5" fill="${pC}" fill-opacity="0.92"/>
       <rect x="21" y="35.5" width="13" height="3" rx="1.5" fill="#070b12" fill-opacity="0.50"/>
       <rect x="36" y="35" width="11" height="2.5" rx="1" fill="${pC}" fill-opacity="0.30"/>`;

  return `<svg class="companion-mascot companion-mascot--sentinel ${ec} ${sc}" width="${sz}" height="${sz}" viewBox="0 0 72 72" fill="none" data-companion-svg="${id}" aria-hidden="true">
<defs>
  <radialGradient id="sent-g-${id}" cx="42%" cy="38%" r="58%">
    <stop offset="0%" stop-color="${pC}" stop-opacity="0.62"/>
    <stop offset="100%" stop-color="#070b12" stop-opacity="0.96"/>
  </radialGradient>
  <filter id="sent-f-${id}" x="-25%" y="-25%" width="150%" height="150%">
    <feGaussianBlur stdDeviation="2.8" result="b"/><feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge>
  </filter>
</defs>
<!-- Armor frame -->
${frameEl}
<!-- Claw marks -->
${clawEl}
<!-- Body — slightly angular presence -->
<circle class="comp-body" cx="36" cy="37" r="14.5" fill="url(#sent-g-${id})" stroke="${pC}" stroke-width="2.1" stroke-opacity="0.84" filter="url(#sent-f-${id})"/>
<!-- Visor eye -->
${eyeEl}
<!-- Status dot -->
<circle class="comp-status-dot" cx="56" cy="19" r="3" fill="${aC}" fill-opacity="0.95"/>
</svg>`;
}

/* ── Archon — Architect Wisp ─────────────────────────────────────────────────
 * Silhouette: floating geometric body with two crossed orbiting rings, orbital particles.
 * Distinctive features: dual elliptical orbits, particle dots, diamond-glyph eyes.
 * Genome variants: orbit ring count/angle, eye style, accent particles.
 * ─────────────────────────────────────────────────────────────────────────── */
function _svgArchitect(sz, pC, aC, ec, sc, id, genome) {
  const ev  = (genome && genome.eyeVariant) || 'diamond-eye';
  const ot  = (genome && genome.orbitType)  || 'dual-cross';
  const acc = (genome && genome.accessory)  || null;

  // Orbit system — key visual differentiator
  const orbitEl = ot === 'star-ring'
    ? `<ellipse class="comp-orbit comp-orbit-a" cx="36" cy="36" rx="30" ry="9" stroke="${pC}" stroke-width="1.2" stroke-opacity="0.36" stroke-dasharray="2.5 3" transform="rotate(-25,36,36)"/>
       <ellipse class="comp-orbit comp-orbit-b" cx="36" cy="36" rx="30" ry="9" stroke="${aC}" stroke-width="0.9" stroke-opacity="0.24" stroke-dasharray="2 4" transform="rotate(25,36,36)"/>
       <ellipse class="comp-orbit comp-orbit-c" cx="36" cy="36" rx="30" ry="9" stroke="${pC}" stroke-width="0.6" stroke-opacity="0.16" stroke-dasharray="2 5" transform="rotate(90,36,36)"/>`
    : ot === 'ellipse-tilt'
    ? `<ellipse class="comp-orbit comp-orbit-a" cx="36" cy="36" rx="30" ry="10" stroke="${pC}" stroke-width="1.2" stroke-opacity="0.36" stroke-dasharray="3 4" transform="rotate(-12,36,36)"/>
       <circle cx="66" cy="34" r="2.2" fill="${pC}" fill-opacity="0.55"/>
       <circle cx="6" cy="38" r="1.8" fill="${pC}" fill-opacity="0.40"/>`
    : `<ellipse class="comp-orbit comp-orbit-a" cx="36" cy="36" rx="30" ry="11" stroke="${pC}" stroke-width="1.2" stroke-opacity="0.36" stroke-dasharray="3 3.5" transform="rotate(-12,36,36)"/>
       <ellipse class="comp-orbit comp-orbit-b" cx="36" cy="36" rx="11" ry="30" stroke="${aC}" stroke-width="0.9" stroke-opacity="0.26" stroke-dasharray="2 5" transform="rotate(78,36,36)"/>`;

  // Orbital particles — always present, different positions by variant
  const particles = acc === 'reflection-dot'
    ? `<circle class="comp-particle" cx="66" cy="36" r="2.4" fill="${pC}" fill-opacity="0.65"/>
       <circle class="comp-particle" cx="6" cy="36" r="1.8" fill="${pC}" fill-opacity="0.48"/>
       <circle class="comp-particle" cx="36" cy="6" r="2.2" fill="${aC}" fill-opacity="0.60"/>
       <circle class="comp-particle" cx="36" cy="66" r="1.6" fill="${pC}" fill-opacity="0.38"/>
       <circle cx="22" cy="21" r="1.4" fill="${pC}" fill-opacity="0.40"/>
       <circle cx="50" cy="21" r="1.4" fill="${aC}" fill-opacity="0.35"/>`
    : `<circle class="comp-particle" cx="65" cy="36" r="2.4" fill="${pC}" fill-opacity="0.65"/>
       <circle class="comp-particle" cx="7" cy="36" r="1.8" fill="${pC}" fill-opacity="0.48"/>
       <circle class="comp-particle" cx="36" cy="6" r="2.2" fill="${aC}" fill-opacity="0.60"/>
       <circle class="comp-particle" cx="36" cy="66" r="1.6" fill="${pC}" fill-opacity="0.38"/>`;

  // Eye style — geometric, not round
  const eyeEl = ev === 'round-glyph'
    ? `<circle class="comp-eye comp-eye--l" cx="30" cy="37" r="3" fill="${pC}" fill-opacity="0.92"/>
       <circle class="comp-eye comp-eye--r" cx="42" cy="37" r="3" fill="${pC}" fill-opacity="0.92"/>
       <circle cx="30" cy="37" r="1.2" fill="#070b12"/>
       <circle cx="42" cy="37" r="1.2" fill="#070b12"/>`
    : ev === 'orbit-dot'
    ? `<circle class="comp-eye comp-eye--l" cx="29" cy="37" r="2.8" fill="${pC}" fill-opacity="0.88"/>
       <circle class="comp-eye comp-eye--r" cx="43" cy="37" r="2.8" fill="${pC}" fill-opacity="0.88"/>
       <circle cx="29" cy="37" r="1" fill="#070b12"/>
       <circle cx="43" cy="37" r="1" fill="#070b12"/>
       <circle cx="28.3" cy="36.1" r="0.8" fill="${pC}" fill-opacity="0.6"/>
       <circle cx="42.3" cy="36.1" r="0.8" fill="${pC}" fill-opacity="0.6"/>`
    : `<path class="comp-eye comp-eye--l" d="M26.5,37 L30,33.5 L33.5,37 L30,40.5 Z" fill="${pC}" fill-opacity="0.90"/>
       <path class="comp-eye comp-eye--r" d="M38.5,37 L42,33.5 L45.5,37 L42,40.5 Z" fill="${pC}" fill-opacity="0.90"/>`;

  const glyphEl = acc === 'geo-accent'
    ? `<path class="comp-glyph" d="M36,25 L45,36 L36,47 L27,36 Z" fill="${pC}" fill-opacity="0.10" stroke="${pC}" stroke-width="1.2" stroke-opacity="0.48"/>
       <circle cx="36" cy="25" r="1.6" fill="${pC}" fill-opacity="0.55"/>
       <circle cx="36" cy="47" r="1.2" fill="${pC}" fill-opacity="0.38"/>`
    : `<path class="comp-glyph" d="M36,26 L44,36 L36,46 L28,36 Z" fill="${pC}" fill-opacity="0.10" stroke="${pC}" stroke-width="1.1" stroke-opacity="0.44"/>`;

  return `<svg class="companion-mascot companion-mascot--architect ${ec} ${sc}" width="${sz}" height="${sz}" viewBox="0 0 72 72" fill="none" data-companion-svg="${id}" aria-hidden="true">
<defs>
  <radialGradient id="arch-g-${id}" cx="40%" cy="36%" r="62%">
    <stop offset="0%" stop-color="${pC}" stop-opacity="0.56"/>
    <stop offset="100%" stop-color="#070b12" stop-opacity="0.96"/>
  </radialGradient>
  <filter id="arch-f-${id}" x="-25%" y="-25%" width="150%" height="150%">
    <feGaussianBlur stdDeviation="2.2" result="b"/><feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge>
  </filter>
</defs>
<!-- Soft halo -->
<circle class="comp-halo" cx="36" cy="36" r="32" fill="${pC}" fill-opacity="0.04"/>
<!-- Orbit rings -->
${orbitEl}
<!-- Orbital particles -->
${particles}
<!-- Body sphere -->
<circle class="comp-body" cx="36" cy="36" r="13" fill="url(#arch-g-${id})" stroke="${pC}" stroke-width="1.7" stroke-opacity="0.74" filter="url(#arch-f-${id})"/>
<!-- Diamond glyph overlay -->
${glyphEl}
<!-- Eyes -->
${eyeEl}
<!-- Status dot -->
<circle class="comp-status-dot" cx="49" cy="22" r="2.8" fill="${aC}" fill-opacity="0.90"/>
</svg>`;
}

/* ── Codex — Patch — Code Sprite ─────────────────────────────────────────────
 * Silhouette: terminal-inside-hex with prominent code brackets, wide screen eyes.
 * Distinctive features: [ ] bracket frame, rectangular terminal eyes, blinking cursor.
 * Genome variants: eye style (screen vs scan-line vs cursor), bracket vs hex frame.
 * ─────────────────────────────────────────────────────────────────────────── */
function _svgDebugger(sz, pC, aC, ec, sc, id, genome) {
  const ev  = (genome && genome.eyeVariant) || 'twin-rect';
  const ot  = (genome && genome.orbitType)  || 'hex-frame';
  const acc = (genome && genome.accessory)  || null;

  // Frame style
  const frameEl = ot === 'bracket-ring'
    ? `<!-- Prominent bracket pair — signature -->
       <path class="comp-bracket comp-bracket--l" d="M14,20 L8,20 L8,52 L14,52"
         stroke="${pC}" stroke-width="2.4" stroke-opacity="0.62" stroke-linecap="round" stroke-linejoin="round" fill="none"/>
       <path class="comp-bracket comp-bracket--r" d="M58,20 L64,20 L64,52 L58,52"
         stroke="${pC}" stroke-width="2.4" stroke-opacity="0.62" stroke-linecap="round" stroke-linejoin="round" fill="none"/>`
    : ot === 'none'
    ? `<!-- none variant: lightweight brackets (brackets are core Code Sprite identity) -->
       <path class="comp-bracket comp-bracket--l" d="M19,25 L12,36 L19,47"
         stroke="${pC}" stroke-width="2" stroke-opacity="0.52" stroke-linecap="round" stroke-linejoin="round" fill="none"/>
       <path class="comp-bracket comp-bracket--r" d="M53,25 L60,36 L53,47"
         stroke="${pC}" stroke-width="2" stroke-opacity="0.52" stroke-linecap="round" stroke-linejoin="round" fill="none"/>`
    : `<polygon class="comp-hex" points="36,8 60,21 60,47 36,60 12,47 12,21"
         fill="none" stroke="${pC}" stroke-width="1.5" stroke-opacity="0.44" stroke-linejoin="round"/>
       <path class="comp-bracket comp-bracket--l" d="M17,25 L10,36 L17,47"
         stroke="${pC}" stroke-width="2.2" stroke-opacity="0.58" stroke-linecap="round" stroke-linejoin="round" fill="none"/>
       <path class="comp-bracket comp-bracket--r" d="M55,25 L62,36 L55,47"
         stroke="${pC}" stroke-width="2.2" stroke-opacity="0.58" stroke-linecap="round" stroke-linejoin="round" fill="none"/>`;

  // Eye style — terminal aesthetic
  const eyeEl = ev === 'scan-line'
    ? `<rect class="comp-eye comp-eye--scan" x="23" y="32" width="26" height="8" rx="2" fill="${pC}" fill-opacity="0.90"/>
       <rect x="23" y="35" width="11" height="2" rx="1" fill="#070b12" fill-opacity="0.55"/>
       <rect x="36" y="33.5" width="9" height="4" rx="1" fill="${pC}" fill-opacity="0.35"/>`
    : ev === 'cursor-eye'
    ? `<rect class="comp-eye comp-eye--single" x="24" y="31" width="24" height="10" rx="2.5" fill="${pC}" fill-opacity="0.90"/>
       <rect class="comp-cursor-blink" x="24" y="31" width="6" height="10" rx="2" fill="#070b12" fill-opacity="0.48"/>
       <rect x="32" y="34" width="13" height="4" rx="1" fill="${pC}" fill-opacity="0.36"/>`
    : `<rect class="comp-eye comp-eye--l" x="23" y="31.5" width="10" height="9" rx="2" fill="${pC}" fill-opacity="0.92"/>
       <rect class="comp-eye comp-eye--r" x="39" y="31.5" width="10" height="9" rx="2" fill="${pC}" fill-opacity="0.92"/>
       <line x1="23" y1="36" x2="33" y2="36" stroke="#070b12" stroke-width="1.8"/>
       <line x1="39" y1="36" x2="49" y2="36" stroke="#070b12" stroke-width="1.8"/>
       <rect x="25" y="32.5" width="4" height="2.5" rx="0.8" fill="${pC}" fill-opacity="0.35"/>
       <rect x="41" y="32.5" width="4" height="2.5" rx="0.8" fill="${pC}" fill-opacity="0.35"/>`;

  // Accessory — cursor or code glyph at bottom
  const accEl = acc === 'cursor-blink'
    ? `<rect class="comp-cursor" x="28" y="44" width="18" height="3" rx="1.5" fill="${pC}" fill-opacity="0.60"/>
       <rect x="28" y="44" width="5" height="3" rx="1.5" fill="${aC}" fill-opacity="0.80"/>`
    : acc === 'code-accent'
    ? `<path d="M29,45 L24,48 L29,51" stroke="${pC}" stroke-width="1.4" stroke-opacity="0.45" fill="none" stroke-linecap="round" stroke-linejoin="round"/>
       <path d="M43,45 L48,48 L43,51" stroke="${pC}" stroke-width="1.4" stroke-opacity="0.45" fill="none" stroke-linecap="round" stroke-linejoin="round"/>
       <line x1="33" y1="48" x2="39" y2="48" stroke="${pC}" stroke-width="1" stroke-opacity="0.35"/>`
    : `<rect class="comp-cursor" x="28" y="44" width="18" height="2.8" rx="1.4" fill="${pC}" fill-opacity="0.50"/>`;

  return `<svg class="companion-mascot companion-mascot--debugger ${ec} ${sc}" width="${sz}" height="${sz}" viewBox="0 0 72 72" fill="none" data-companion-svg="${id}" aria-hidden="true">
<defs>
  <radialGradient id="dbg-g-${id}" cx="40%" cy="36%" r="58%">
    <stop offset="0%" stop-color="${pC}" stop-opacity="0.52"/>
    <stop offset="100%" stop-color="#070b12" stop-opacity="0.96"/>
  </radialGradient>
  <filter id="dbg-f-${id}" x="-25%" y="-25%" width="150%" height="150%">
    <feGaussianBlur stdDeviation="2.2" result="b"/><feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge>
  </filter>
</defs>
<!-- Soft halo -->
<circle class="comp-halo" cx="36" cy="36" r="32" fill="${pC}" fill-opacity="0.05"/>
<!-- Frame -->
${frameEl}
<!-- Body -->
<circle class="comp-body" cx="36" cy="37" r="13.5" fill="url(#dbg-g-${id})" stroke="${pC}" stroke-width="1.9" stroke-opacity="0.76" filter="url(#dbg-f-${id})"/>
<!-- Eyes -->
${eyeEl}
<!-- Cursor / code accent -->
${accEl}
<!-- Status dot -->
<circle class="comp-status-dot" cx="53" cy="21" r="2.8" fill="${aC}" fill-opacity="0.92"/>
</svg>`;
}

/* ── Pod (unhatched) ─────────────────────────────────────────────────────────── */
// v3.0: No trait chips shown in pod. Traits generate at hatch time.
function renderCompanionPod(runtimeId) {
  const id     = _normalizeId(runtimeId);
  const preset = COMPANION_PRESETS[id] || COMPANION_PRESETS.archon;
  const p = preset.primaryHsl, a = preset.accentHsl;
  const pC = `hsl(${p[0]},${p[1]}%,${p[2]}%)`;
  const aC = `hsl(${a[0]},${a[1]}%,${a[2]}%)`;
  return (
    `<div class="companion-pod" data-runtime="${_esc(id)}">` +
    `<svg class="companion-pod-svg" width="72" height="72" viewBox="0 0 72 72" fill="none" aria-hidden="true">` +
    `<defs><radialGradient id="pod-g-${id}" cx="40%" cy="35%" r="58%">` +
    `<stop offset="0%" stop-color="${pC}" stop-opacity="0.18"/>` +
    `<stop offset="100%" stop-color="#0a0d14" stop-opacity="0.92"/></radialGradient></defs>` +
    `<circle cx="36" cy="36" r="30" fill="${pC}" fill-opacity="0.04"/>` +
    `<circle cx="36" cy="36" r="26" stroke="${pC}" stroke-width="0.9" stroke-opacity="0.22" stroke-dasharray="5 5"/>` +
    `<ellipse class="pod-body" cx="36" cy="38" rx="15.5" ry="19.5" fill="url(#pod-g-${id})" stroke="${pC}" stroke-width="1.4" stroke-opacity="0.42"/>` +
    `<ellipse cx="30" cy="30" rx="5" ry="7" fill="${pC}" fill-opacity="0.08"/>` +
    `<path d="M32,24 L35,30 L31,35" stroke="${pC}" stroke-width="0.8" stroke-opacity="0.32" stroke-linecap="round" stroke-linejoin="round" fill="none"/>` +
    `<circle class="pod-inner-pulse" cx="36" cy="38" r="4.5" fill="${pC}" fill-opacity="0.16"/>` +
    `<circle cx="51" cy="22" r="2.4" fill="${aC}" fill-opacity="0.55"/>` +
    `</svg>` +
    `<div class="companion-pod-label">Unhatched</div>` +
    `</div>`
  );
}

/* ── Companion stage ─────────────────────────────────────────────────────────── */
function renderCompanionStage(runtimeId, opts) {
  const id        = _normalizeId(runtimeId);
  const companion = getCompanion(id);
  const preset    = COMPANION_PRESETS[id] || COMPANION_PRESETS.archon;
  const sz        = (opts && opts.size) || 72;

  if (!companion) {
    return (
      `<div class="companion-stage companion-stage--dormant" data-runtime="${_esc(id)}" id="companion-stage-${_esc(id)}">` +
      renderCompanionPod(id) +
      `<div class="companion-stage-caption">` +
      `<span class="companion-stage-name text-muted">${_escHtml(preset.name)}</span>` +
      `<span class="companion-stage-arch">${_escHtml(preset.archetype)}</span>` +
      `</div></div>`
    );
  }

  const rarityConf = RARITY_CONFIG[companion.rarity] || RARITY_CONFIG.Rare;
  const stageClass = 'companion-stage--' + (companion.stage || 'hatched');
  return (
    `<div class="companion-stage ${stageClass}" data-runtime="${_esc(id)}" ` +
    `id="companion-stage-${_esc(id)}" style="--companion-glow:${rarityConf.glow}; --companion-border:${rarityConf.borderColor};">` +
    renderCompanionSVG(id, sz, companion.activeEmote || 'idle', companion.animationState || 'idle') +
    `<div class="companion-stage-caption">` +
    `<span class="companion-stage-name">${_escHtml(companion.name)}</span>` +
    `<span class="companion-rarity-badge" data-rarity="${_esc(companion.rarity)}">${_escHtml(companion.rarity)}</span>` +
    `</div></div>`
  );
}

/* ── Stats / traits / campaign ───────────────────────────────────────────────── */

function renderCompanionStats(companion) {
  if (!companion) return `<div class="comp-stats-empty">Companion not yet hatched.</div>`;
  return (
    `<div class="comp-stats-grid">` +
    _cStat('Bond',   companion.bond + '%',              companion.bond > 50 ? 'ok' : 'info') +
    _cStat('Stage',  _cap(companion.stage || 'hatched'), 'info') +
    _cStat('Mood',   _cap(companion.mood  || 'idle'),    'ok') +
    _cStat('Sync',   _cap(companion.sync  || 'local'),   companion.sync === 'live' ? 'ok' : 'info') +
    `</div>`
  );
}

function _cStat(label, value, tone) {
  return `<div class="comp-stat-card comp-stat-card--${_esc(tone || 'info')}">` +
    `<span class="comp-stat-value">${_escHtml(String(value))}</span>` +
    `<span class="comp-stat-label">${_escHtml(label)}</span>` +
    `</div>`;
}

// Trait chips — shown only when companion is hatched.
// v3.0: unhatched state shows nothing here (unhatched hint handled in profile panel).
function renderCompanionTraits(companion) {
  if (!companion || !companion.traits || companion.traits.length === 0) return '';
  return `<div class="comp-trait-list">` +
    companion.traits.map(t => `<span class="comp-trait-chip">${_escHtml(t)}</span>`).join('') +
    `</div>`;
}

function renderEmoteControls(runtimeId, unlockedEmotes) {
  const list = (unlockedEmotes || ['idle', 'blink', 'wave', 'scan', 'alert'])
    .filter(k => k in EMOTE_DEFS && k !== 'idle' && k !== 'hatch');
  return (
    `<div class="comp-emote-controls">` +
    list.map(k => {
      const def = EMOTE_DEFS[k];
      return `<button class="comp-emote-btn" type="button" ` +
        `data-emote="${_esc(k)}" data-runtime="${_esc(runtimeId)}" title="${_esc(def.label)}">` +
        `<span class="comp-emote-icon" aria-hidden="true">${def.icon}</span>` +
        `<span class="comp-emote-label">${_escHtml(def.label)}</span>` +
        `</button>`;
    }).join('') +
    `</div>`
  );
}

function renderCampaignProgress(companion) {
  const prog  = getCampaignProgress(companion);
  const pct   = Math.max(0, Math.min(100, prog.percent));
  const rarity = companion ? companion.rarity : 'Rare';
  return (
    `<div class="comp-campaign">` +
    `<div class="comp-campaign-header">` +
    `<span class="comp-campaign-stage">${_escHtml(prog.stageLabel)}</span>` +
    `<span class="comp-campaign-next">${prog.nextLabel ? '→ ' + _escHtml(prog.nextLabel) : 'Max stage'}</span>` +
    `</div>` +
    `<div class="comp-campaign-bar" title="Bond: ${prog.bond}% — ${pct}% to ${prog.nextLabel || 'max'}">` +
    `<div class="comp-campaign-fill" data-rarity="${_esc(rarity)}" style="width:${pct}%"></div>` +
    `</div>` +
    `<div class="comp-campaign-desc">${_escHtml(prog.stageDescription || '')}</div>` +
    `</div>`
  );
}

/* ── Rarity breakdown section ───────────────────────────────────────────────
 * Shows each rolled attribute, its tier label, and its individual chance %.
 * Also shows the overall companion rarity + "X% of companions reach this tier".
 * ─────────────────────────────────────────────────────────────────────────── */

function renderRarityBreakdown(companion) {
  if (!companion || !companion.genome || !companion.genome.rolls) {
    return `<div class="comp-rarity-empty">Rarity data not available for this companion.</div>`;
  }
  const rolls  = companion.genome.rolls;
  const overall = companion.rarity || 'Core';
  const td     = TIER_DISPLAY[overall.toLowerCase()] || TIER_DISPLAY.core;

  // Overall summary bar
  const overallHtml = (
    `<div class="comp-rarity-overall" style="--tier-color:${_esc(td.color)}; border-color:${_esc(td.color)}40;">` +
    `<span class="comp-rarity-overall-label" style="color:${_esc(td.color)};">${_escHtml(overall)}</span>` +
    `<span class="comp-rarity-overall-name">overall rarity</span>` +
    `<span class="comp-rarity-overall-chance">${_getRarityChance(overall)}% of companions</span>` +
    `</div>`
  );

  // Per-attribute rows
  const attrOrder = ['species', 'colorScheme', 'eyes', 'frame', 'accessory', 'aura', 'emotePack'];
  const attrLabels = { species: 'Species', colorScheme: 'Color', eyes: 'Eyes', frame: 'Frame', accessory: 'Accessory', aura: 'Aura', emotePack: 'Emotes' };

  const rowsHtml = attrOrder.map(key => {
    const r = rolls[key];
    if (!r) return '';
    const tColor = r.tierColor || '#94a3b8';
    return (
      `<div class="comp-rarity-row">` +
      `<span class="comp-rarity-attr">${_escHtml(attrLabels[key] || key)}</span>` +
      `<span class="comp-rarity-item">${_escHtml(r.label)}</span>` +
      `<span class="comp-rarity-tier-badge" style="color:${_esc(tColor)}; border-color:${_esc(tColor)}40;">${_escHtml(r.tierLabel)}</span>` +
      `<span class="comp-rarity-pct">${r.chance}%</span>` +
      `</div>`
    );
  }).join('');

  return `<div class="comp-rarity-breakdown">${overallHtml}<div class="comp-rarity-rows">${rowsHtml}</div></div>`;
}

function _getRarityChance(rarity) {
  // Approximate % of companions that reach this tier or higher overall.
  const map = { Sovereign: '<2', Mythic: '~5', Prime: '~12', Rare: '~30', Uncommon: '~55', Core: '~75' };
  return map[rarity] || '~30';
}

/* ── Animation states section ───────────────────────────────────────────────── */

function renderAnimationStates(runtimeId) {
  const id      = _normalizeId(runtimeId);
  const companion = getCompanion(id);
  const current = companion ? (companion.animationState || 'idle') : 'idle';
  const preview = ['idle', 'working', 'waiting', 'review', 'failed', 'alert', 'success', 'sleeping'];

  return (
    `<div class="comp-state-grid">` +
    preview.map(k => {
      const s       = ANIMATION_STATES[k];
      const isActive = k === current;
      return (
        `<div class="comp-state-card ${isActive ? 'comp-state-card--active' : ''}" ` +
        `data-comp-state="${_esc(k)}" data-runtime="${_esc(id)}" ` +
        `role="button" tabindex="0" title="${_escHtml(s.desc)}">` +
        `<div class="comp-state-icon ${_esc(s.cls)}">${_escHtml(s.icon)}</div>` +
        `<span class="comp-state-label">${_escHtml(s.label)}</span>` +
        `</div>`
      );
    }).join('') +
    `</div>` +
    `<p class="comp-state-hint">Click a state to preview. States reflect runtime activity.</p>`
  );
}

/* ── Runtime brain link section ─────────────────────────────────────────────── */

function renderRuntimeBrainLink(runtimeId, profileData) {
  const id       = _normalizeId(runtimeId);
  const preset   = COMPANION_PRESETS[id] || COMPANION_PRESETS.archon;
  const companion = getCompanion(id);
  const seeds    = _RUNTIME_TRAIT_SEEDS[id] || {};
  const lane     = seeds.lane || '—';
  const role     = seeds.role || '—';
  const hasProfile = !!profileData;
  const syncStatus = hasProfile ? 'linked' : 'local-only';
  const brainStatus = (profileData && profileData.memory_available) ? 'available' : 'local-companion-only';
  const lastSynced = companion ? companion.updatedAt : null;
  const traitSource = companion
    ? (companion.genome ? 'genome + usage context' : 'runtime role + lane')
    : 'not yet generated';

  return (
    `<div class="comp-brain-link">` +
    `<div class="comp-brain-link-row"><span class="comp-brain-link-label">Runtime</span>` +
    `<code class="comp-brain-link-value">${_escHtml(id)}</code></div>` +
    `<div class="comp-brain-link-row"><span class="comp-brain-link-label">Lane</span>` +
    `<span class="comp-brain-link-value">${_escHtml(lane)}</span></div>` +
    `<div class="comp-brain-link-row"><span class="comp-brain-link-label">Role</span>` +
    `<span class="comp-brain-link-value">${_escHtml(role)}</span></div>` +
    `<div class="comp-brain-link-row"><span class="comp-brain-link-label">Profile Sync</span>` +
    `<span class="comp-brain-link-value comp-brain-link-sync comp-brain-link-sync--${_esc(syncStatus)}">` +
    `${syncStatus === 'linked' ? '✓ Linked' : '◌ Local only'}</span></div>` +
    `<div class="comp-brain-link-row"><span class="comp-brain-link-label">Runtime Brain</span>` +
    `<span class="comp-brain-link-value comp-brain-link-brain">${_escHtml(brainStatus)}</span></div>` +
    `<div class="comp-brain-link-row"><span class="comp-brain-link-label">Linked Traits</span>` +
    `<span class="comp-brain-link-value comp-brain-link-trait-src">${_escHtml(traitSource)}</span></div>` +
    (lastSynced ? `<div class="comp-brain-link-row"><span class="comp-brain-link-label">Last Sync</span>` +
    `<span class="comp-brain-link-value comp-brain-link-ts">${_escHtml(lastSynced.slice(0, 10))}</span></div>` : '') +
    `<div class="comp-brain-link-action-row">` +
    `<button class="comp-action-btn comp-action-btn--ghost comp-action-btn--sm" data-comp-action="open-profile" data-runtime="${_esc(id)}">Profile doc</button>` +
    `</div>` +
    `<p class="comp-brain-link-note">Companion data is local to this Studio instance. Profile sync is read-only.</p>` +
    `</div>`
  );
}

/* ── My Companions collection view ─────────────────────────────────────────── */

function renderMyCompanionsCollection() {
  const KNOWN = ['hermes', 'openclaw', 'archon', 'codex'];
  const store = _loadStore();

  return (
    `<div class="comp-collection-grid">` +
    KNOWN.map(id => {
      const companion  = store[id];
      const preset     = COMPANION_PRESETS[id] || COMPANION_PRESETS.archon;
      const isHatched  = !!companion;
      const isHome     = companion && companion.isHomeCompanion;
      const rarity     = companion ? companion.rarity : null;
      const rarityConf = rarity ? (RARITY_CONFIG[rarity] || RARITY_CONFIG.Rare) : null;
      const borderStyle = rarityConf ? `border-color:${rarityConf.borderColor}; box-shadow:${rarityConf.glow};` : '';

      return (
        `<div class="comp-collection-card ${isHatched ? 'comp-collection-card--hatched' : 'comp-collection-card--unhatched'}" ` +
        `data-open-companion-profile="${_esc(id)}" role="button" tabindex="0" ` +
        `title="${isHatched ? _esc(companion.name) + ' · Click to open profile' : 'Unhatched · Click to hatch'}" ` +
        `style="${borderStyle}">` +
        (isHome ? `<span class="comp-collection-home-badge">Home</span>` : '') +
        `<div class="comp-collection-avatar">` +
        (isHatched ? renderCompanionSVG(id, 44, 'idle') : renderCompanionPod(id)) +
        `</div>` +
        `<div class="comp-collection-info">` +
        `<span class="comp-collection-name">${_escHtml(isHatched ? companion.name : preset.name)}</span>` +
        `<span class="comp-collection-runtime">${_escHtml(preset.runtimeName)}</span>` +
        (rarity ? `<span class="companion-rarity-badge comp-collection-rarity" data-rarity="${_esc(rarity)}">${_escHtml(rarity)}</span>` : '') +
        `<span class="comp-collection-stage ${isHatched ? '' : 'text-muted'}">` +
        `${isHatched ? _escHtml(_cap(companion.stage || 'hatched')) : 'Unhatched'}</span>` +
        `</div>` +
        `</div>`
      );
    }).join('') +
    `</div>`
  );
}

/* ── Customization panel ─────────────────────────────────────────────────────── */

function renderCustomizationPanel(runtimeId) {
  const id        = _normalizeId(runtimeId);
  const companion = getCompanion(id);
  if (!companion) return `<div class="comp-customize-empty">Hatch this companion first to customize.</div>`;

  const currentAccent = companion.accentColor || 'default';
  const motionOn      = companion.motionEnabled !== false;

  const accentOptions = [
    { key: 'default', label: 'Default' },
    { key: 'warm',    label: 'Warm' },
    { key: 'cool',    label: 'Cool' },
    { key: 'vivid',   label: 'Vivid' },
  ];

  return (
    `<div class="comp-customize">` +
    `<div class="comp-customize-row">` +
    `<span class="comp-customize-label">Color Accent</span>` +
    `<div class="comp-customize-accent-opts">` +
    accentOptions.map(o =>
      `<button class="comp-accent-btn ${currentAccent === o.key ? 'comp-accent-btn--active' : ''}" ` +
      `data-comp-action="set-accent" data-accent="${_esc(o.key)}" data-runtime="${_esc(id)}">${_escHtml(o.label)}</button>`
    ).join('') +
    `</div></div>` +
    `<div class="comp-customize-row">` +
    `<span class="comp-customize-label">Motion</span>` +
    `<button class="comp-action-btn comp-action-btn--ghost comp-action-btn--sm" ` +
    `data-comp-action="motion-toggle" data-runtime="${_esc(id)}">` +
    `${motionOn ? 'Motion: On' : 'Motion: Off'}</button>` +
    `</div>` +
    `<div class="comp-customize-row">` +
    `<span class="comp-customize-label">Home companion</span>` +
    `<button class="comp-action-btn ${companion.isHomeCompanion ? 'comp-action-btn--active' : ''} comp-action-btn--sm" ` +
    `data-comp-action="set-home" data-runtime="${_esc(id)}">` +
    `${companion.isHomeCompanion ? '✓ Active' : 'Set as Home'}</button>` +
    `</div>` +
    `</div>`
  );
}

/* ── Companion profile panel (full modal) ────────────────────────────────────── */

function renderCompanionProfilePanel(runtimeId, runtimeStats, profileData) {
  const id         = _normalizeId(runtimeId);
  const companion  = getCompanion(id);
  const preset     = COMPANION_PRESETS[id] || COMPANION_PRESETS.archon;
  const rarity     = companion ? companion.rarity : preset.rarity;
  const rarityConf = RARITY_CONFIG[rarity] || RARITY_CONFIG.Rare;
  const isHome     = companion && companion.isHomeCompanion;
  const isHatched  = !!companion;
  const s          = runtimeStats || {};

  const primaryActionBtn = !isHatched
    ? `<button class="comp-action-btn comp-action-btn--hatch" data-comp-action="hatch" data-runtime="${_esc(id)}">* Hatch ${_escHtml(preset.name)}</button>`
    : `<button class="comp-action-btn ${isHome ? 'comp-action-btn--active' : 'comp-action-btn--primary'}" data-comp-action="set-home" data-runtime="${_esc(id)}">${isHome ? '✓ Home companion' : 'Set as Home companion'}</button>`;

  // Left column — hero mascot
  const heroCol = (
    `<div class="comp-profile-hero-col">` +
    `<div class="comp-profile-hero-bg" style="--rarity-glow:${rarityConf.glow}; --rarity-color:${rarityConf.color}; --rarity-border:${rarityConf.borderColor};">` +
    renderCompanionStage(id, { size: 120 }) +
    `</div>` +
    `<div class="comp-profile-hero-name">${_escHtml(companion ? companion.name : preset.name)}</div>` +
    `<div class="comp-profile-hero-arch">${_escHtml(companion ? companion.archetype : preset.archetype)}</div>` +
    `<span class="companion-rarity-badge" data-rarity="${_esc(rarity)}">${_escHtml(rarity)}</span>` +
    (companion ? `<div class="comp-profile-hero-mood">${_moodIcon(companion.mood)} ${_escHtml(_cap(companion.mood))}</div>` : '') +
    // Trait chips — only shown after hatch (v3.0: never show finalized traits pre-hatch)
    (isHatched
      ? renderCompanionTraits(companion)
      : `<div class="comp-trait-hatch-hint">Traits generate at hatch</div>`) +
    `<div class="comp-profile-hero-action">${primaryActionBtn}</div>` +
    `</div>`
  );

  // Right column — content
  const contentCol = (
    `<div class="comp-profile-content-col">` +

    // Runtime stats
    `<div class="comp-profile-section">` +
    `<div class="comp-section-title comp-section-title--runtime">Runtime Stats</div>` +
    `<div class="comp-stats-grid comp-stats-grid--runtime" id="comp-runtime-stats-${_esc(id)}">` +
    (s.total_executions != null
      ? (_cStat('Executions',  s.total_executions,  'info') +
         _cStat('Successful',  s.success_count   != null ? s.success_count   : '—', 'ok') +
         _cStat('Escalated',   s.escalated_count  != null ? s.escalated_count  : '—', 'warn') +
         _cStat('Reliability', s.reliability_rate != null ? Math.round(s.reliability_rate * 100) + '%' : '—', 'ok'))
      : `<div class="comp-stats-loading">Runtime stats load after first execution.</div>`) +
    `</div></div>` +

    // Companion stats (hatched only)
    (isHatched
      ? `<div class="comp-profile-section"><div class="comp-section-title">Companion Stats</div>` +
        renderCompanionStats(companion) + `</div>`
      : '') +

    // Campaign (hatched only)
    (isHatched
      ? `<div class="comp-profile-section"><div class="comp-section-title">Campaign</div>` +
        renderCampaignProgress(companion) + `</div>`
      : '') +

    // Animation States (hatched only) — NEW
    (isHatched
      ? `<div class="comp-profile-section"><div class="comp-section-title">Animation States</div>` +
        renderAnimationStates(id) + `</div>`
      : '') +

    // Gestures/emotes (hatched, non-trivial unlocked)
    (isHatched && companion.unlockedEmotes && companion.unlockedEmotes.filter(e => e !== 'idle' && e !== 'hatch').length > 0
      ? `<div class="comp-profile-section"><div class="comp-section-title">Gestures</div>` +
        renderEmoteControls(id, companion.unlockedEmotes) + `</div>`
      : '') +

    // My Companions collection — NEW (always shown)
    `<div class="comp-profile-section"><div class="comp-section-title">My Companions</div>` +
    renderMyCompanionsCollection() + `</div>` +

    // Runtime Brain Link — NEW
    `<div class="comp-profile-section"><div class="comp-section-title">Runtime Brain</div>` +
    renderRuntimeBrainLink(id, profileData || null) + `</div>` +

    // Customization (hatched only) — NEW
    (isHatched
      ? `<div class="comp-profile-section"><div class="comp-section-title">Customize</div>` +
        renderCustomizationPanel(id) + `</div>`
      : '') +

    // Rarity Breakdown — NEW (always shown after hatch)
    (isHatched
      ? `<div class="comp-profile-section"><div class="comp-section-title">Rarity Breakdown</div>` +
        renderRarityBreakdown(companion) + `</div>`
      : '') +

    // Advanced / destructive
    `<div class="comp-profile-section comp-profile-section--advanced">` +
    `<div class="comp-section-title comp-section-title--advanced">Advanced</div>` +
    `<div class="comp-advanced-body">` +
    (isHatched
      ? `<button class="comp-action-btn comp-action-btn--danger comp-action-btn--sm" ` +
        `data-comp-action="reset" data-runtime="${_esc(id)}" ` +
        `title="Fresh roll: new species, color, frame, genome, traits. Bond resets.">` +
        `Rehatch (Fresh Roll)</button>` +
        `<p class="comp-advanced-warn">Performs a completely new random roll — species, color, frame, genome, and traits all regenerate. Bond resets. This cannot be undone.</p>`
      : '') +
    `<button class="comp-action-btn comp-action-btn--danger-ghost comp-action-btn--sm" ` +
    `data-comp-action="clear-all" style="margin-top:8px;" ` +
    `title="Delete all companions for all runtimes. Start fresh.">` +
    `Clear All Companions</button>` +
    `<p class="comp-advanced-warn" style="opacity:0.65;">Removes all companions from every runtime. Each runtime returns to Unhatched. Use this to start a completely fresh generation.</p>` +
    `</div></div>` +

    `</div>` // end content col
  );

  return (
    `<div class="comp-profile-panel" data-runtime="${_esc(id)}">` +
    heroCol +
    contentCol +
    `</div>`
  );
}

/* ── Home companion column ───────────────────────────────────────────────────── */

function renderHomeCompanionColumn(pendingApprovals) {
  const candidate = resolveHomeCompanionCandidate();
  const companion = candidate ? candidate.companion : null;
  const hasAlerts = pendingApprovals > 0;

  if (!companion) {
    // Dormant — suggest hermes as first hatch (NOT openclaw).
    return (
      `<div class="home-companion-col home-companion-col--dormant" data-companion-col="1">` +
      `<div class="home-companion-mascot-wrap" ` +
      `data-open-companion-profile="hermes" role="button" tabindex="0" ` +
      `title="Hatch your first companion — click to begin">` +
      renderCompanionPod('hermes') +
      `</div>` +
      `<div class="home-companion-hatch-cta">` +
      `<button class="home-companion-hatch-btn" type="button" data-open-companion-profile="hermes">Hatch companion</button>` +
      `<span class="home-companion-hatch-label">Each runtime gets one companion.</span>` +
      `</div></div>`
    );
  }

  const emote      = hasAlerts ? 'alert' : 'idle';
  const cls        = hasAlerts ? 'home-companion-col--alert' : 'home-companion-col--ready';
  const statusLabel = hasAlerts ? '! Action needed' : '✓ Ready';
  const tone       = hasAlerts ? 'companion-status--alert' : 'companion-status--ok';
  const rarityConf = RARITY_CONFIG[companion.rarity] || RARITY_CONFIG.Rare;
  const selectionHint = candidate && candidate.selectionReason === 'most_used_runtime'
    ? 'Most used'
    : candidate && candidate.selectionReason === 'explicit_selection'
    ? 'Active companion'
    : '';

  return (
    `<div class="home-companion-col ${_esc(cls)}" data-companion-col="1" ` +
    `style="--companion-glow:${_esc(rarityConf.glow)}; --companion-border:${_esc(rarityConf.borderColor)}; border-color:${_esc(rarityConf.borderColor)};">` +
    `<div class="home-companion-mascot-wrap" ` +
    `data-open-companion-profile="${_esc(companion.runtimeId)}" ` +
    `data-runtime-id="${_esc(companion.runtimeId)}" ` +
    `role="button" tabindex="0" ` +
    `title="${_esc(companion.name)} · ${_esc(companion.archetype)} · ${_esc(companion.runtimeName)}. Click to open companion profile.">` +
    renderCompanionSVG(companion.runtimeId, 84, emote, companion.animationState || 'idle') +
    `</div>` +
    `<span class="companion-status-label ${_esc(tone)}">${_escHtml(statusLabel)}</span>` +
    `<span class="home-companion-name">${_escHtml(companion.name)}</span>` +
    `<span class="home-companion-runtime-label">${_escHtml(companion.runtimeName)} companion</span>` +
    `<span class="companion-rarity-badge" data-rarity="${_esc(companion.rarity)}">${_escHtml(companion.rarity)}</span>` +
    (selectionHint ? `<span class="home-companion-selection-hint">${_escHtml(selectionHint)}</span>` : '') +
    `</div>`
  );
}

/* ── Emote playback ──────────────────────────────────────────────────────────── */

const _emoteTimers = new WeakMap();

function playEmote(hostEl, emote) {
  if (!hostEl || !emote || emote === 'idle') return;
  const def = EMOTE_DEFS[emote];
  if (!def || !def.cls) return;
  const prev = _emoteTimers.get(hostEl);
  if (prev) { clearTimeout(prev); }
  Object.values(EMOTE_DEFS).forEach(d => { if (d.cls) hostEl.classList.remove(d.cls); });
  hostEl.classList.add(def.cls);
  if (def.duration > 0) {
    const t = setTimeout(() => {
      hostEl.classList.remove(def.cls);
      _emoteTimers.delete(hostEl);
    }, def.duration);
    _emoteTimers.set(hostEl, t);
  }
}

/* ── Hatch animation ─────────────────────────────────────────────────────────── */

function playHatchAnimation(hostEl, runtimeId, onComplete) {
  if (!hostEl) { if (onComplete) onComplete(); return; }
  hostEl.classList.add('companion-hatching');
  setTimeout(() => {
    hostEl.classList.add('companion-hatching--crack');
    setTimeout(() => {
      hostEl.classList.remove('companion-hatching', 'companion-hatching--crack');
      hostEl.innerHTML = renderCompanionStage(runtimeId, { size: 72 });
      hostEl.classList.add('companion-hatching--born');
      wireCompanionEvents(hostEl);
      setTimeout(() => {
        hostEl.classList.remove('companion-hatching--born');
        if (onComplete) onComplete();
      }, 1600);
    }, 800);
  }, 700);
}

/* ── Clear all confirmation ──────────────────────────────────────────────────── */

function _showClearAllConfirm(onConfirmed) {
  const existing = document.getElementById('comp-clear-all-confirm');
  if (existing) existing.remove();

  const div = document.createElement('div');
  div.id = 'comp-clear-all-confirm';
  div.className = 'comp-reset-confirm comp-clear-all-confirm';
  div.innerHTML =
    `<div class="comp-reset-confirm-body">` +
    `<p class="comp-reset-title">Clear All Companions?</p>` +
    `<p class="comp-reset-desc">This removes the companions for <strong>all runtimes</strong> — ` +
    `Hermes, OpenClaw, Archon, and Codex. Each runtime will return to Unhatched. ` +
    `Your next hatch will be a completely new random generation.</p>` +
    `<div class="comp-reset-actions">` +
    `<button class="comp-action-btn comp-action-btn--danger" id="comp-clear-all-yes">Clear All</button>` +
    `<button class="comp-action-btn" id="comp-clear-all-no">Cancel</button>` +
    `</div></div>`;

  const panel = document.getElementById('companion-profile-panel-body');
  if (panel) panel.appendChild(div);

  const yesBtn = document.getElementById('comp-clear-all-yes');
  const noBtn  = document.getElementById('comp-clear-all-no');
  if (yesBtn) yesBtn.addEventListener('click', () => { div.remove(); if (onConfirmed) onConfirmed(); });
  if (noBtn)  noBtn.addEventListener('click',  () => { div.remove(); });
}

/* ── Reset confirmation ──────────────────────────────────────────────────────── */

function _showResetConfirm(runtimeId, onConfirmed) {
  const id     = _normalizeId(runtimeId);
  const preset = COMPANION_PRESETS[id] || COMPANION_PRESETS.archon;
  const c      = getCompanion(id);

  const existing = document.getElementById('comp-reset-confirm');
  if (existing) existing.remove();

  const div = document.createElement('div');
  div.id = 'comp-reset-confirm';
  div.className = 'comp-reset-confirm';
  div.innerHTML =
    `<div class="comp-reset-confirm-body">` +
    `<p class="comp-reset-title">Rehatch ${_escHtml(c ? c.name : preset.name)}?</p>` +
    `<p class="comp-reset-desc">Rehatching will replace this companion's visual genome, ` +
    `generated traits, bond progress, and campaign stage. ` +
    `Rarity (${_escHtml(c ? c.rarity : preset.rarity)}) is preserved. ` +
    `This is meant to be rare.</p>` +
    `<div class="comp-reset-actions">` +
    `<button class="comp-action-btn comp-action-btn--danger" id="comp-reset-confirm-yes">Rehatch companion</button>` +
    `<button class="comp-action-btn" id="comp-reset-confirm-no">Cancel</button>` +
    `</div></div>`;

  const panel = document.getElementById('companion-profile-panel-body');
  if (panel) panel.appendChild(div);

  document.getElementById('comp-reset-confirm-yes').addEventListener('click', () => {
    div.remove();
    if (onConfirmed) onConfirmed();
  });
  document.getElementById('comp-reset-confirm-no').addEventListener('click', () => { div.remove(); });
}

/* ── Wire companion events on a container ────────────────────────────────────── */

function wireCompanionEvents(container) {
  if (!container) return;

  // Emote buttons
  container.querySelectorAll('[data-emote]').forEach(btn => {
    btn.addEventListener('click', () => {
      const emote = btn.dataset.emote;
      const rid   = btn.dataset.runtime;
      const mascot = container.querySelector(`[data-companion-svg="${rid}"]`)
        || document.querySelector(`[data-companion-svg="${rid}"]`)
        || container.querySelector('.companion-mascot');
      if (mascot) playEmote(mascot, emote);

      // Emote feedback text
      const fb = container.querySelector('.comp-emote-feedback');
      if (fb && rid) {
        const c = getCompanion(rid);
        const name = c ? c.name : rid;
        const def  = EMOTE_DEFS[emote];
        fb.textContent = name + ' performed ' + (def ? def.label : emote);
        fb.classList.add('comp-emote-feedback--show');
        setTimeout(() => fb.classList.remove('comp-emote-feedback--show'), 2000);
      }
      recordProgressionEvent(rid, 'emote_triggered');
    });
  });

  // Animation state preview cards
  container.querySelectorAll('[data-comp-state]').forEach(card => {
    card.addEventListener('click', () => {
      const state = card.dataset.compState;
      const rid   = card.dataset.runtime;
      const c = getCompanion(rid);
      if (!c) return;
      c.animationState = state;
      saveCompanion(rid, c);
      // Update active card
      container.querySelectorAll('[data-comp-state]').forEach(el => el.classList.remove('comp-state-card--active'));
      card.classList.add('comp-state-card--active');
      // Play corresponding emote on mascot
      const stateEmoteMap = { working: 'working', waiting: 'nod', review: 'scan',
        failed: 'error', alert: 'alert', success: 'success', sleeping: 'sleep', thinking: 'think', scanning: 'scan' };
      const mascot = container.querySelector(`[data-companion-svg="${rid}"]`)
        || document.querySelector(`[data-companion-svg="${rid}"]`);
      if (mascot && stateEmoteMap[state]) playEmote(mascot, stateEmoteMap[state]);
      recordProgressionEvent(rid, 'state_card_clicked');
    });
    card.addEventListener('keydown', e => {
      if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); card.click(); }
    });
  });

  // Set as home companion
  container.querySelectorAll('[data-comp-action="set-home"]').forEach(btn => {
    btn.addEventListener('click', () => {
      setHomeCompanion(btn.dataset.runtime);
      btn.textContent = '✓ Home companion';
      btn.classList.add('comp-action-btn--active');
    });
  });

  // Hatch (first-time)
  container.querySelectorAll('[data-comp-action="hatch"]').forEach(btn => {
    btn.addEventListener('click', () => {
      const rid = btn.dataset.runtime;
      if (getCompanion(rid)) return;
      hatchCompanion(rid);
      recordProgressionEvent(rid, 'companion_hatched');
      const panelBody = document.getElementById('companion-profile-panel-body');
      if (panelBody) {
        panelBody.innerHTML = renderCompanionProfilePanel(rid, {}, null);
        wireCompanionEvents(panelBody);
        const mascot = panelBody.querySelector('.companion-mascot');
        if (mascot) { setTimeout(() => playEmote(mascot, 'hatch'), 50); }
        _loadPanelRuntimeStats(rid, panelBody);
      }
      const stageHost = document.getElementById('drawer-companion-host');
      if (stageHost) playHatchAnimation(stageHost, rid, null);
      if (typeof window._refreshHomeCompanionColumn === 'function') {
        setTimeout(() => window._refreshHomeCompanionColumn(), 50);
      }
    });
  });

  // Reset / Rehatch (fresh roll for this runtime)
  container.querySelectorAll('[data-comp-action="reset"]').forEach(btn => {
    btn.addEventListener('click', () => {
      const rid = btn.dataset.runtime;
      _showResetConfirm(rid, () => {
        resetCompanion(rid);
        const panelBody = document.getElementById('companion-profile-panel-body');
        if (panelBody) {
          panelBody.innerHTML = renderCompanionProfilePanel(rid, {}, null);
          wireCompanionEvents(panelBody);
          _loadPanelRuntimeStats(rid, panelBody);
        }
        const stageHost = document.getElementById('drawer-companion-host');
        if (stageHost) playHatchAnimation(stageHost, rid, null);
        if (typeof window._refreshHomeCompanionColumn === 'function') {
          setTimeout(() => window._refreshHomeCompanionColumn(), 100);
        }
      });
    });
  });

  // Clear all companions (wipe all runtimes, return to unhatched)
  container.querySelectorAll('[data-comp-action="clear-all"]').forEach(btn => {
    btn.addEventListener('click', () => {
      _showClearAllConfirm(() => {
        clearAllCompanions();
        // Close companion panel and return to home
        closeCompanionProfilePanel();
        // Also close drawer if open
        const drawer = document.getElementById('runtime-profile-drawer');
        if (drawer) drawer.classList.remove('home-drawer--open');
        document.body.classList.remove('home-drawer--open');
      });
    });
  });

  // Set color accent
  container.querySelectorAll('[data-comp-action="set-accent"]').forEach(btn => {
    btn.addEventListener('click', () => {
      const rid    = btn.dataset.runtime;
      const accent = btn.dataset.accent;
      const c = getCompanion(rid);
      if (!c) return;
      c.accentColor = accent;
      saveCompanion(rid, c);
      container.querySelectorAll('.comp-accent-btn').forEach(b => b.classList.remove('comp-accent-btn--active'));
      btn.classList.add('comp-accent-btn--active');
      recordProgressionEvent(rid, 'companion_customized');
    });
  });

  // Motion toggle
  container.querySelectorAll('[data-comp-action="motion-toggle"]').forEach(btn => {
    btn.addEventListener('click', () => {
      const rid = btn.dataset.runtime;
      const c = getCompanion(rid);
      if (c) {
        c.motionEnabled = c.motionEnabled !== false ? false : true;
        saveCompanion(rid, c);
        btn.textContent = c.motionEnabled ? 'Motion: On' : 'Motion: Off';
        const panel = document.getElementById('companion-profile-panel');
        if (panel) panel.dataset.motionEnabled = String(c.motionEnabled);
      }
    });
  });

  // Open profile doc
  container.querySelectorAll('[data-comp-action="open-profile"]').forEach(btn => {
    btn.addEventListener('click', () => {
      const rid = btn.dataset.runtime;
      recordProgressionEvent(rid, 'profile_doc_opened');
      if (typeof window._openRuntimeProfileDoc === 'function') window._openRuntimeProfileDoc(rid);
    });
  });

  // Open chat
  container.querySelectorAll('[data-comp-action="open-chat"]').forEach(btn => {
    btn.addEventListener('click', () => {
      recordProgressionEvent(btn.dataset.runtime, 'chat_opened');
      if (typeof window.showPanel === 'function') window.showPanel('chat');
    });
  });

  // Open companion profile panel from anywhere
  container.querySelectorAll('[data-open-companion-profile]').forEach(el => {
    el.addEventListener('click', () => openCompanionProfilePanel(el.dataset.openCompanionProfile));
    el.addEventListener('keydown', e => {
      if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); openCompanionProfilePanel(el.dataset.openCompanionProfile); }
    });
  });
}

/* ── Async runtime stats loader ─────────────────────────────────────────────── */

function _loadPanelRuntimeStats(runtimeId, panelBody) {
  const id  = _normalizeId(runtimeId);
  const api = (window.pywebview && window.pywebview.api) ? window.pywebview.api : null;
  if (!api || typeof api.get_runtime_profile_detail !== 'function') return;
  Promise.resolve(api.get_runtime_profile_detail(id)).then(resp => {
    const d = (resp && resp.ok && resp.data) ? resp.data : {};
    const s = d.stats || {};
    const grid = panelBody.querySelector(`#comp-runtime-stats-${id}`);
    if (grid) {
      grid.innerHTML =
        _cStat('Executions',  s.total_executions  != null ? s.total_executions  : '—', 'info') +
        _cStat('Successful',  s.success_count      != null ? s.success_count      : '—', 'ok') +
        _cStat('Escalated',   s.escalated_count    != null ? s.escalated_count    : '—', 'warn') +
        _cStat('Reliability', s.reliability_rate   != null ? Math.round(s.reliability_rate * 100) + '%' : '—', 'ok');
    }
    syncBondFromRuntimeStats(id, s);
  }).catch(() => {
    const grid = panelBody.querySelector(`#comp-runtime-stats-${id}`);
    if (grid) grid.innerHTML = `<div class="comp-stats-empty">Runtime stats unavailable.</div>`;
  });
}

/* ── Companion profile panel open/close ─────────────────────────────────────── */

function openCompanionProfilePanel(runtimeId) {
  const id      = _normalizeId(runtimeId);
  const panel   = document.getElementById('companion-profile-panel');
  const body    = document.getElementById('companion-profile-panel-body');
  const titleEl = document.querySelector('.companion-panel-title');
  if (!panel || !body) return;

  const preset    = COMPANION_PRESETS[id] || COMPANION_PRESETS.archon;
  const companion = getCompanion(id);
  const compName  = companion ? companion.name : preset.name;
  const rtName    = companion ? companion.runtimeName : preset.runtimeName;
  if (titleEl) {
    titleEl.textContent = compName + ' · Companion Profile';
    const sub = titleEl.parentElement.querySelector('.companion-panel-runtime-label');
    if (sub) sub.textContent = rtName;
    else {
      const lbl = document.createElement('span');
      lbl.className = 'companion-panel-runtime-label';
      lbl.textContent = rtName;
      titleEl.after(lbl);
    }
  }

  body.innerHTML = renderCompanionProfilePanel(id, {}, null);
  // Add feedback span for emote feedback text
  const fbEl = document.createElement('div');
  fbEl.className = 'comp-emote-feedback';
  body.appendChild(fbEl);

  panel.hidden = false;
  requestAnimationFrame(() => panel.classList.add('companion-panel--open'));
  wireCompanionEvents(body);
  _loadPanelRuntimeStats(id, body);
  recordProgressionEvent(id, 'profile_opened');
}

function closeCompanionProfilePanel() {
  const panel = document.getElementById('companion-profile-panel');
  if (!panel) return;
  panel.classList.remove('companion-panel--open');
  setTimeout(() => { panel.hidden = true; }, 250);
}

/* ── Escape helpers ──────────────────────────────────────────────────────────── */

function _escHtml(s) {
  return String(s == null ? '' : s)
    .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;').replace(/'/g, '&#39;');
}
function _esc(s) { return _escHtml(s); }

function _moodIcon(mood) {
  const m = { idle: '◌', alert: '!', watchful: '◉', reflective: '◈', focused: '◎', working: '⚙', celebratory: '+' };
  return m[mood] || '◌';
}
function _cap(s) {
  return s ? String(s).charAt(0).toUpperCase() + String(s).slice(1) : '';
}

/* ── Startup ─────────────────────────────────────────────────────────────────── */
if (typeof window !== 'undefined') {
  setTimeout(_initBackendSync, 50);
}

/* ── Public API ──────────────────────────────────────────────────────────────── */
global.CompanionSystem = {
  // Core store
  getCompanion,
  saveCompanion,
  setHomeCompanion,
  getActiveHomeCompanion,
  resolveHomeCompanionCandidate,
  // Backend sync + usage ranking
  initBackendSync: _initBackendSync,
  flushPendingBackendWrite: _flushPendingBackendWrite,
  getUsageRanking: function() { return _usageRanking ? _usageRanking.slice() : null; },
  // Genome + trait generation + roll system
  generateCompanionGenome,
  generateCompanionTraits,
  rollCompanionAttributes,
  buildGenomeFromRolls,
  calculateOverallRarity,
  clearAllCompanions,
  // Hatch lifecycle
  hatchCompanion,
  resetCompanion,
  generateCompanion: hatchCompanion,   // legacy alias
  // Progression
  recordProgressionEvent,
  incrementBond,
  syncBondFromRuntimeStats,
  getCampaignProgress,
  // Rendering
  renderCompanionSVG,
  renderCompanionPod,
  renderCompanionStage,
  renderCompanionStats,
  renderCompanionTraits,
  renderEmoteControls,
  renderCampaignProgress,
  renderAnimationStates,
  renderRarityBreakdown,
  renderRuntimeBrainLink,
  renderMyCompanionsCollection,
  renderCustomizationPanel,
  renderCompanionProfilePanel,
  renderHomeCompanionColumn,
  // Interaction
  playEmote,
  playHatchAnimation,
  wireCompanionEvents,
  openCompanionProfilePanel,
  closeCompanionProfilePanel,
  // Data
  COMPANION_PRESETS,
  RARITY_CONFIG,
  CAMPAIGN_STAGES,
  EMOTE_DEFS,
  ANIMATION_STATES,
  PROGRESSION_EVENTS,
  GENOME_PARTS,
  TRAIT_POOL,
  COMPANION_ATTRIBUTES,
  TIER_DISPLAY,
  TIER_RANK,
};

})(window);
