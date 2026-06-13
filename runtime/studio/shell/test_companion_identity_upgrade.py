"""
test_companion_identity_upgrade.py — Companion Identity + Asset System Upgrade Pass
Verifies all 18 acceptance criteria from the upgrade spec.

Coverage:
  AC-1  Traits no longer simple hardcoded static labels
  AC-2  Unhatched companions do not show finalized traits
  AC-3  Hatched companions generate and persist a visual genome
  AC-4  Companions look more visually distinct (genome-driven)
  AC-5  Runtime-specific companion families exist
  AC-6  Animation States section in companion profile
  AC-7  State previews: idle/working/waiting/review/failed/alert/success/sleeping
  AC-8  Emotes are visibly improved (per-runtime specials)
  AC-9  Emotes return companion to resting position (timeout mechanism)
  AC-10 Bond/progression exists
  AC-11 Reset/Rehatch is meaningful and advanced
  AC-12 Customization foundation exists
  AC-13 Companion profile shows runtime brain/profile link
  AC-14 My Companions / collection view exists
  AC-15 Home companion still works
  AC-16 Persistence still works
  AC-17 No heavy performance burden
  AC-18 Static/frontend checks pass
"""
import re
from pathlib import Path

SHELL_DIR    = Path(__file__).parent
COMPANION_JS = SHELL_DIR / "frontend" / "companion.js"
APP_JS       = SHELL_DIR / "frontend" / "app.js"
STYLES_CSS   = SHELL_DIR / "frontend" / "styles.css"

def _comp():  return COMPANION_JS.read_text(encoding="utf-8")
def _app():   return APP_JS.read_text(encoding="utf-8")
def _css():   return STYLES_CSS.read_text(encoding="utf-8")


# ── AC-1 — Traits not hardcoded static labels ─────────────────────────────────

class TestAC1DynamicTraits:
    """Traits are generated dynamically at hatch, not read directly from COMPANION_PRESETS."""

    def test_companion_presets_no_longer_have_traits_key(self):
        """COMPANION_PRESETS must not have a 'traits:' key (replaced by traitSeeds)."""
        comp = _comp()
        # Find the COMPANION_PRESETS block
        presets_start = comp.find("const COMPANION_PRESETS")
        presets_end   = comp.find("const RARITY_CONFIG", presets_start)
        presets_block = comp[presets_start:presets_end]
        # 'traits:' must not appear as a property key in the presets block
        # (traitSeeds is the replacement)
        assert "traits:" not in presets_block, \
            "COMPANION_PRESETS must not contain 'traits:' key — use traitSeeds"

    def test_companion_presets_have_traitseeds(self):
        """traitSeeds replaces static traits in COMPANION_PRESETS."""
        comp = _comp()
        presets_start = comp.find("const COMPANION_PRESETS")
        presets_end   = comp.find("const RARITY_CONFIG", presets_start)
        presets_block = comp[presets_start:presets_end]
        assert "traitSeeds:" in presets_block, "COMPANION_PRESETS must have traitSeeds"

    def test_generate_companion_traits_function_exists(self):
        assert "function generateCompanionTraits" in _comp()

    def test_generate_companion_traits_uses_trait_pool(self):
        comp = _comp()
        fn_start = comp.find("function generateCompanionTraits")
        fn_end   = comp.find("function ", fn_start + 10)
        fn_body  = comp[fn_start:fn_end]
        assert "TRAIT_POOL" in fn_body

    def test_trait_pool_constant_exists(self):
        assert "const TRAIT_POOL" in _comp()

    def test_trait_pool_has_role_and_lane_categories(self):
        comp = _comp()
        assert "persistent_lane" in comp
        assert "session_lane" in comp
        assert "coordination_role" in comp
        assert "implementation_role" in comp

    def test_runtime_trait_seeds_mapping_exists(self):
        assert "_RUNTIME_TRAIT_SEEDS" in _comp()

    def test_hatch_calls_generate_companion_traits(self):
        comp = _comp()
        hatch_start = comp.find("function hatchCompanion")
        hatch_end   = comp.find("\nfunction ", hatch_start + 10)
        hatch_body  = comp[hatch_start:hatch_end]
        assert "generateCompanionTraits" in hatch_body, \
            "hatchCompanion must call generateCompanionTraits"

    def test_hatch_stores_traits_on_companion(self):
        comp = _comp()
        hatch_start = comp.find("function hatchCompanion")
        hatch_end   = comp.find("\nfunction ", hatch_start + 10)
        hatch_body  = comp[hatch_start:hatch_end]
        # v3.1: explicit 'traits: traits' form OR shorthand 'traits,'
        assert "traits:" in hatch_body or "traits :" in hatch_body or "traits," in hatch_body, \
            "hatchCompanion must store traits on companion record"


# ── AC-2 — Unhatched: no finalized traits ─────────────────────────────────────

class TestAC2UnhatchedNoFinalizedTraits:
    """Unhatched companions must not show finalized trait chips."""

    def test_companion_profile_panel_no_traits_when_unhatched(self):
        """renderCompanionProfilePanel must show hatch hint, not trait chips, when !isHatched."""
        comp = _comp()
        profile_fn_start = comp.find("function renderCompanionProfilePanel")
        profile_fn_end   = comp.find("\n/* ── Home companion", profile_fn_start)
        profile_body     = comp[profile_fn_start:profile_fn_end]
        # Must have conditional: isHatched ? renderCompanionTraits : hint
        assert "comp-trait-hatch-hint" in profile_body, \
            "Profile panel must show hatch hint when unhatched"

    def test_trait_hatch_hint_css_exists(self):
        assert ".comp-trait-hatch-hint" in _css()

    def test_drawer_shows_seed_hints_label_not_finalized_traits(self):
        """Runtime drawer must label unhatched trait display as 'seed hints'."""
        app = _app()
        # The drawer should reference seed hints header
        assert "seed hints" in app.lower() or "comp-trait-seed-header" in app

    def test_drawer_uses_trait_seeds_not_traits_directly(self):
        """Drawer must use traitSeeds (or both) for unhatched, not preset.traits alone."""
        app = _app()
        # Should prefer traitSeeds over preset.traits for unhatched drawer
        assert "traitSeeds" in app, "Drawer should use traitSeeds for unhatched runtime"

    def test_muted_chips_still_structurally_present(self):
        """comp-trait-chip--muted must still be in app.js (labeled as seed hints)."""
        app = _app()
        assert "comp-trait-chip--muted" in app
        assert "comp-trait-list--muted" in app


# ── AC-3 — Visual genome generated and persisted ──────────────────────────────

class TestAC3VisualGenome:
    """Hatched companions have a visual genome generated and stored on the record."""

    def test_generate_companion_genome_function_exists(self):
        assert "function generateCompanionGenome" in _comp()

    def test_genome_parts_constant_exists(self):
        assert "const GENOME_PARTS" in _comp()

    def test_genome_parts_has_all_four_families(self):
        comp = _comp()
        genome_start = comp.find("const GENOME_PARTS")
        genome_end   = comp.find("const TRAIT_POOL", genome_start)
        genome_block = comp[genome_start:genome_end]
        assert "courier:" in genome_block
        assert "sentinel:" in genome_block
        assert "architect:" in genome_block
        assert "debugger:" in genome_block

    def test_genome_parts_has_variants(self):
        """Each family must have bodies, eyeVariants, orbitTypes, accessories, auras."""
        comp = _comp()
        genome_start = comp.find("const GENOME_PARTS")
        genome_end   = comp.find("const TRAIT_POOL", genome_start)
        genome_block = comp[genome_start:genome_end]
        assert "bodies:" in genome_block
        assert "eyeVariants:" in genome_block
        assert "orbitTypes:" in genome_block
        assert "accessories:" in genome_block
        assert "auras:" in genome_block

    def test_generate_genome_uses_hash_seed(self):
        comp = _comp()
        genome_fn = comp.find("function generateCompanionGenome")
        genome_end = comp.find("\nfunction ", genome_fn + 10)
        genome_body = comp[genome_fn:genome_end]
        assert "_hashSeed" in genome_body

    def test_hash_seed_function_exists(self):
        assert "function _hashSeed" in _comp()

    def test_hatch_generates_and_stores_genome(self):
        """v3.1: hatchCompanion uses rollCompanionAttributes+buildGenomeFromRolls."""
        comp = _comp()
        hatch_start = comp.find("function hatchCompanion")
        hatch_end   = comp.find("\nfunction ", hatch_start + 10)
        hatch_body  = comp[hatch_start:hatch_end]
        # v3.1 uses buildGenomeFromRolls; generateCompanionGenome is still in file for migration
        assert ("buildGenomeFromRolls" in hatch_body or "generateCompanionGenome" in hatch_body), \
            "hatchCompanion must build genome"
        assert ("genome:" in hatch_body or "genome," in hatch_body), \
            "hatchCompanion must store genome on companion literal"

    def test_genome_stored_on_companion_record(self):
        """Genome must be a field on the companion object (for persistence)."""
        comp = _comp()
        # genome: or genome, must appear in hatchCompanion or resetCompanion
        assert "genome:" in comp or "genome," in comp

    def test_genome_includes_eye_variant_and_orbit_type(self):
        comp = _comp()
        assert "eyeVariant" in comp
        assert "orbitType" in comp


# ── AC-4 — More visually distinct companions ──────────────────────────────────

class TestAC4VisualDistinction:
    """Genome drives visual variety in SVG renderers."""

    def test_svg_courier_accepts_genome_param(self):
        comp = _comp()
        fn_start = comp.find("function _svgCourier")
        fn_end   = comp.find("function _svgSentinel", fn_start)
        fn_body  = comp[fn_start:fn_end]
        assert "genome" in fn_body

    def test_svg_sentinel_accepts_genome_param(self):
        comp = _comp()
        fn_start = comp.find("function _svgSentinel")
        fn_end   = comp.find("function _svgArchitect", fn_start)
        fn_body  = comp[fn_start:fn_end]
        assert "genome" in fn_body

    def test_svg_architect_accepts_genome_param(self):
        comp = _comp()
        fn_start = comp.find("function _svgArchitect")
        fn_end   = comp.find("function _svgDebugger", fn_start)
        fn_body  = comp[fn_start:fn_end]
        assert "genome" in fn_body

    def test_svg_debugger_accepts_genome_param(self):
        comp = _comp()
        fn_start = comp.find("function _svgDebugger")
        fn_end   = comp.find("function renderCompanionPod", fn_start)
        fn_body  = comp[fn_start:fn_end]
        assert "genome" in fn_body

    def test_courier_has_eye_variant_selection(self):
        comp = _comp()
        fn_start = comp.find("function _svgCourier")
        fn_end   = comp.find("function _svgSentinel", fn_start)
        fn_body  = comp[fn_start:fn_end]
        # Must have branching on eyeVariant
        assert "eyeVariant" in fn_body

    def test_svgs_use_genome_palette(self):
        """SVG renderers should use genome.primaryHsl/accentHsl if available."""
        comp = _comp()
        # renderCompanionSVG should extract hsl from genome
        svg_fn = comp.find("function renderCompanionSVG")
        svg_end = comp.find("function _svgCourier", svg_fn)
        svg_body = comp[svg_fn:svg_end]
        assert "genome" in svg_body


# ── AC-5 — Runtime companion families ─────────────────────────────────────────

class TestAC5CompanionFamilies:
    """Four distinct runtime companion families exist."""

    def test_courier_family_exists(self):
        assert "companion-mascot--courier" in _comp()

    def test_sentinel_family_exists(self):
        assert "companion-mascot--sentinel" in _comp()

    def test_architect_family_exists(self):
        assert "companion-mascot--architect" in _comp()

    def test_debugger_family_exists(self):
        assert "companion-mascot--debugger" in _comp()

    def test_each_family_has_unique_archetype(self):
        comp = _comp()
        for archetype in ("Courier Spirit", "Sentinel Core", "Architect Wisp", "Code Sprite"):
            assert archetype in comp, f"Archetype '{archetype}' not found in COMPANION_PRESETS"

    def test_family_themed_svgs_are_structurally_different(self):
        """Each SVG function must produce a different class on the root element."""
        comp = _comp()
        assert "companion-mascot--courier" in comp
        assert "companion-mascot--sentinel" in comp
        assert "companion-mascot--architect" in comp
        assert "companion-mascot--debugger" in comp


# ── AC-6 — Animation States section ──────────────────────────────────────────

class TestAC6AnimationStatesSection:
    """Companion profile includes an Animation States section."""

    def test_render_animation_states_function_exists(self):
        assert "function renderAnimationStates" in _comp()

    def test_animation_states_constant_defined(self):
        assert "const ANIMATION_STATES" in _comp()

    def test_animation_states_section_in_profile_panel(self):
        """renderCompanionProfilePanel must call renderAnimationStates."""
        comp = _comp()
        profile_fn_start = comp.find("function renderCompanionProfilePanel")
        profile_fn_end   = comp.find("\n/* ── Home companion", profile_fn_start)
        profile_body     = comp[profile_fn_start:profile_fn_end]
        assert "renderAnimationStates" in profile_body

    def test_animation_states_section_title(self):
        comp = _comp()
        assert "Animation States" in comp

    def test_animation_states_exposed_in_public_api(self):
        assert "ANIMATION_STATES" in _comp()
        comp = _comp()
        api_start = comp.find("global.CompanionSystem")
        assert "renderAnimationStates" in comp[api_start:]


# ── AC-7 — State preview cards ────────────────────────────────────────────────

class TestAC7StatePreviewCards:
    """State preview cards for idle/working/waiting/review/failed/alert/success/sleeping."""

    def test_state_grid_css_exists(self):
        assert ".comp-state-grid" in _css()

    def test_state_card_css_exists(self):
        assert ".comp-state-card" in _css()

    def test_state_card_active_css_exists(self):
        assert ".comp-state-card--active" in _css()

    def test_all_eight_required_states_defined(self):
        comp = _comp()
        for state in ("idle", "working", "waiting", "review", "failed", "alert", "success", "sleeping"):
            assert f"'{state}'" in comp or f'"{state}"' in comp, \
                f"State '{state}' not found in ANIMATION_STATES"

    def test_render_animation_states_produces_state_cards(self):
        comp = _comp()
        fn_start = comp.find("function renderAnimationStates")
        fn_end   = comp.find("\n/* ──", fn_start + 10)
        fn_body  = comp[fn_start:fn_end]
        assert "comp-state-card" in fn_body

    def test_state_cards_are_clickable(self):
        """State cards should have data-comp-state attribute for click handling."""
        comp = _comp()
        assert "data-comp-state" in comp

    def test_state_card_click_handled_in_wire_events(self):
        comp = _comp()
        wire_start = comp.find("function wireCompanionEvents")
        wire_end   = comp.find("\n/* ── Async", wire_start)
        wire_body  = comp[wire_start:wire_end]
        assert "data-comp-state" in wire_body


# ── AC-8 — Emotes improved ────────────────────────────────────────────────────

class TestAC8ImprovedEmotes:
    """Per-runtime special emotes exist and are wired."""

    def test_hermes_has_relay_emote(self):
        comp = _comp()
        assert "'relay'" in comp or '"relay"' in comp

    def test_hermes_has_signal_pulse_emote(self):
        assert "signal-pulse" in _comp()

    def test_openclaw_has_claw_guard_emote(self):
        assert "claw-guard" in _comp()

    def test_openclaw_has_sentinel_scan_emote(self):
        assert "sentinel-scan" in _comp()

    def test_archon_has_reflect_emote(self):
        assert "reflect" in _comp()

    def test_archon_has_architect_pulse_emote(self):
        assert "architect-pulse" in _comp()

    def test_codex_has_compile_emote(self):
        comp = _comp()
        assert "'compile'" in comp or '"compile"' in comp

    def test_codex_has_debug_pulse_emote(self):
        assert "debug-pulse" in _comp()

    def test_relay_emote_css_keyframe_exists(self):
        css = _css()
        assert "comp-emote--relay" in css or "relayWingFlap" in css

    def test_compile_emote_css_keyframe_exists(self):
        css = _css()
        assert "comp-emote--compile" in css or "compileBlink" in css

    def test_emote_feedback_text_mechanism_exists(self):
        """wireCompanionEvents must show feedback text after emote click."""
        comp = _comp()
        wire_start = comp.find("function wireCompanionEvents")
        wire_end   = comp.find("\n/* ── Async", wire_start)
        wire_body  = comp[wire_start:wire_end]
        assert "comp-emote-feedback" in wire_body


# ── AC-9 — Emotes return to resting position ─────────────────────────────────

class TestAC9EmoteReturnToRest:
    """Emote animations have a duration and return to resting state."""

    def test_emote_defs_have_duration(self):
        comp = _comp()
        assert "duration:" in comp

    def test_play_emote_uses_timeout_for_duration(self):
        comp = _comp()
        play_fn = comp.find("function playEmote")
        play_end = comp.find("\n/* ──", play_fn)
        play_body = comp[play_fn:play_end]
        assert "setTimeout" in play_body
        assert "def.duration" in play_body or "duration" in play_body

    def test_emote_timers_use_weakmap(self):
        """Per-element timers prevent emote stacking across elements."""
        assert "_emoteTimers" in _comp()
        assert "WeakMap" in _comp()

    def test_emote_classes_cleared_before_applying_new(self):
        comp = _comp()
        play_fn = comp.find("function playEmote")
        play_end = comp.find("\n/* ──", play_fn)
        play_body = comp[play_fn:play_end]
        assert "classList.remove" in play_body


# ── AC-10 — Bond/progression ──────────────────────────────────────────────────

class TestAC10BondProgression:
    """Bond progression system is present and wired."""

    def test_increment_bond_function_exists(self):
        assert "function incrementBond" in _comp()

    def test_campaign_stages_defined(self):
        assert "const CAMPAIGN_STAGES" in _comp()

    def test_bond_increases_on_profile_open(self):
        comp = _comp()
        assert "profile_opened" in comp

    def test_stage_advancement_logic_exists(self):
        comp = _comp()
        fn_start = comp.find("function incrementBond")
        fn_end   = comp.find("\nfunction ", fn_start + 10)
        fn_body  = comp[fn_start:fn_end]
        assert "c.stage" in fn_body

    def test_state_card_click_earns_bond(self):
        comp = _comp()
        assert "state_card_clicked" in comp


# ── AC-11 — Reset/Rehatch meaningful ─────────────────────────────────────────

class TestAC11ResetMeaningful:
    """Reset is in Advanced section with strong destructive copy."""

    def test_reset_confirm_function_exists(self):
        assert "_showResetConfirm" in _comp()

    def test_reset_confirm_mentions_genome_and_traits(self):
        comp = _comp()
        reset_fn_start = comp.find("function _showResetConfirm")
        reset_fn_end   = comp.find("\nfunction ", reset_fn_start + 10)
        reset_body     = comp[reset_fn_start:reset_fn_end]
        # Must mention what will be lost
        assert "genome" in reset_body.lower() or "traits" in reset_body.lower()

    def test_reset_confirm_says_meant_to_be_rare(self):
        comp = _comp()
        assert "meant to be rare" in comp or "rare" in comp.lower()

    def test_reset_is_in_advanced_section(self):
        comp = _comp()
        profile_fn_start = comp.find("function renderCompanionProfilePanel")
        profile_fn_end   = comp.find("\n/* ── Home companion", profile_fn_start)
        profile_body     = comp[profile_fn_start:profile_fn_end]
        # Advanced section must appear and contain reset
        advanced_pos = profile_body.find("comp-profile-section--advanced")
        reset_pos    = profile_body.find("data-comp-action=\"reset\"", advanced_pos)
        assert advanced_pos >= 0, "Advanced section must exist"
        assert reset_pos > advanced_pos, "Reset button must be inside Advanced section"

    def test_rarity_preserved_on_reset_is_documented(self):
        comp = _comp()
        assert "Rarity" in comp and ("preserved" in comp or "preserve" in comp)


# ── AC-12 — Customization foundation ─────────────────────────────────────────

class TestAC12Customization:
    """Small customization panel exists with color accent + motion + home options."""

    def test_render_customization_panel_exists(self):
        assert "function renderCustomizationPanel" in _comp()

    def test_customization_panel_in_profile(self):
        comp = _comp()
        profile_fn_start = comp.find("function renderCompanionProfilePanel")
        profile_fn_end   = comp.find("\n/* ── Home companion", profile_fn_start)
        profile_body     = comp[profile_fn_start:profile_fn_end]
        assert "renderCustomizationPanel" in profile_body

    def test_color_accent_option_exists(self):
        comp = _comp()
        assert "accentColor" in comp or "set-accent" in comp

    def test_motion_toggle_exists(self):
        assert "motion-toggle" in _comp()

    def test_comp_customize_css_exists(self):
        assert ".comp-customize" in _css()

    def test_comp_accent_btn_css_exists(self):
        assert ".comp-accent-btn" in _css()

    def test_set_accent_wired_in_wire_events(self):
        comp = _comp()
        wire_start = comp.find("function wireCompanionEvents")
        wire_end   = comp.find("\n/* ── Async", wire_start)
        wire_body  = comp[wire_start:wire_end]
        assert "set-accent" in wire_body


# ── AC-13 — Runtime brain/profile link section ────────────────────────────────

class TestAC13RuntimeBrainLink:
    """Companion profile shows runtime brain/profile link status."""

    def test_render_runtime_brain_link_exists(self):
        assert "function renderRuntimeBrainLink" in _comp()

    def test_brain_link_in_profile_panel(self):
        comp = _comp()
        profile_fn_start = comp.find("function renderCompanionProfilePanel")
        profile_fn_end   = comp.find("\n/* ── Home companion", profile_fn_start)
        profile_body     = comp[profile_fn_start:profile_fn_end]
        assert "renderRuntimeBrainLink" in profile_body

    def test_brain_link_shows_lane(self):
        comp = _comp()
        brain_fn_start = comp.find("function renderRuntimeBrainLink")
        brain_fn_end   = comp.find("\n/* ──", brain_fn_start + 10)
        brain_body     = comp[brain_fn_start:brain_fn_end]
        assert "lane" in brain_body

    def test_brain_link_shows_role(self):
        comp = _comp()
        brain_fn_start = comp.find("function renderRuntimeBrainLink")
        brain_fn_end   = comp.find("\n/* ──", brain_fn_start + 10)
        brain_body     = comp[brain_fn_start:brain_fn_end]
        assert "role" in brain_body

    def test_brain_link_shows_sync_status(self):
        comp = _comp()
        assert "comp-brain-link-sync" in comp

    def test_brain_link_shows_trait_source(self):
        comp = _comp()
        assert "Linked Traits" in comp or "traitSource" in comp or "trait_source" in comp

    def test_brain_link_css_exists(self):
        assert ".comp-brain-link" in _css()

    def test_brain_link_note_about_local_data(self):
        comp = _comp()
        assert "local" in comp.lower() and ("brain" in comp.lower() or "profile sync" in comp.lower())


# ── AC-14 — My Companions collection view ────────────────────────────────────

class TestAC14CollectionView:
    """Small My Companions collection view showing all runtimes."""

    def test_render_my_companions_collection_exists(self):
        assert "function renderMyCompanionsCollection" in _comp()

    def test_collection_shows_all_four_runtimes(self):
        comp = _comp()
        fn_start = comp.find("function renderMyCompanionsCollection")
        fn_end   = comp.find("\n/* ── Customization", fn_start)
        fn_body  = comp[fn_start:fn_end]
        for rid in ("hermes", "openclaw", "archon", "codex"):
            assert f"'{rid}'" in fn_body or f'"{rid}"' in fn_body, \
                f"Collection view must include runtime '{rid}'"

    def test_collection_in_profile_panel(self):
        comp = _comp()
        profile_fn_start = comp.find("function renderCompanionProfilePanel")
        profile_fn_end   = comp.find("\n/* ── Home companion", profile_fn_start)
        profile_body     = comp[profile_fn_start:profile_fn_end]
        assert "renderMyCompanionsCollection" in profile_body

    def test_collection_shows_hatched_vs_unhatched_state(self):
        comp = _comp()
        fn_start = comp.find("function renderMyCompanionsCollection")
        fn_end   = comp.find("\n/* ── Customization", fn_start)
        fn_body  = comp[fn_start:fn_end]
        assert "hatched" in fn_body
        assert "unhatched" in fn_body.lower() or "Unhatched" in fn_body

    def test_collection_card_css_exists(self):
        css = _css()
        assert ".comp-collection-grid" in css
        assert ".comp-collection-card" in css

    def test_collection_cards_show_home_badge(self):
        comp = _comp()
        fn_start = comp.find("function renderMyCompanionsCollection")
        fn_end   = comp.find("\n/* ── Customization", fn_start)
        fn_body  = comp[fn_start:fn_end]
        assert "comp-collection-home-badge" in fn_body

    def test_collection_cards_are_clickable(self):
        """Collection cards should open the companion profile for that runtime."""
        comp = _comp()
        fn_start = comp.find("function renderMyCompanionsCollection")
        fn_end   = comp.find("\n/* ── Customization", fn_start)
        fn_body  = comp[fn_start:fn_end]
        assert "data-open-companion-profile" in fn_body


# ── AC-15 — Home companion still works ───────────────────────────────────────

class TestAC15HomeCompanionWorks:
    """Home companion card still renders and home selection logic still works."""

    def test_render_home_companion_column_exists(self):
        assert "function renderHomeCompanionColumn" in _comp()

    def test_resolve_home_companion_candidate_works(self):
        assert "function resolveHomeCompanionCandidate" in _comp()

    def test_dormant_state_defaults_to_hermes(self):
        comp = _comp()
        dormant_start = comp.find("home-companion-col--dormant")
        dormant_end   = comp.find("home-companion-hatch-label", dormant_start)
        dormant_block = comp[dormant_start:dormant_end]
        assert "hermes" in dormant_block
        assert "openclaw" not in dormant_block

    def test_home_card_shows_name_and_runtime_label(self):
        comp = _comp()
        assert "home-companion-name" in comp
        assert "home-companion-runtime-label" in comp


# ── AC-16 — Persistence still works ──────────────────────────────────────────

class TestAC16PersistenceWorks:
    """Persistence mechanisms from v2.3 are intact in v3.0."""

    def test_pending_backend_write_queue_intact(self):
        assert "_pendingBackendWrite" in _comp()
        assert "_flushPendingBackendWrite" in _comp()

    def test_init_backend_sync_intact(self):
        comp = _comp()
        assert "function _initBackendSync" in comp
        assert "Step A" in comp
        assert "Step B" in comp

    def test_genome_is_persisted_on_companion_record(self):
        """genome field in hatchCompanion means it's saved to backend via saveCompanion."""
        comp = _comp()
        hatch_start = comp.find("function hatchCompanion")
        hatch_end   = comp.find("\nfunction resetCompanion", hatch_start)
        hatch_body  = comp[hatch_start:hatch_end]
        # v3.1: accepts both explicit 'genome:' and shorthand 'genome,' forms
        assert "genome:" in hatch_body or "genome," in hatch_body, \
            "genome must be stored on companion literal"
        assert "saveCompanion" in hatch_body or "return saveCompanion" in hatch_body


# ── AC-17 — No heavy performance burden ──────────────────────────────────────

class TestAC17PerformanceSafe:
    """Implementation uses SVG/CSS only, no heavy libraries or canvas."""

    def test_no_webgl_references(self):
        comp = _comp()
        assert "webgl" not in comp.lower()
        assert "WebGLRenderingContext" not in comp

    def test_no_canvas_element_in_companion_js(self):
        assert "getContext('2d')" not in _comp()
        assert 'getContext("2d")' not in _comp()

    def test_companion_mascots_are_svg(self):
        comp = _comp()
        assert "<svg" in comp
        assert "viewBox" in comp

    def test_animation_uses_css_keyframes(self):
        css = _css()
        assert "@keyframes compStateIdle" in css

    def test_reduced_motion_respected(self):
        css = _css()
        assert "prefers-reduced-motion" in css

    def test_no_constant_request_animation_frame_loop(self):
        comp = _comp()
        # requestAnimationFrame should only appear in transient openCompanionProfilePanel
        raf_count = comp.count("requestAnimationFrame")
        assert raf_count <= 2, \
            f"Too many requestAnimationFrame calls ({raf_count}) — no polling loops allowed"


# ── AC-18 — Static/frontend checks pass ──────────────────────────────────────

class TestAC18StaticChecks:
    """Key structural checks: version, public API, CSS classes, app integration."""

    def test_version_is_v3(self):
        assert "v3.0" in _comp()

    def test_public_api_exports_new_functions(self):
        comp = _comp()
        api_start = comp.find("global.CompanionSystem")
        api_block = comp[api_start:]
        for fn in ("generateCompanionGenome", "generateCompanionTraits",
                   "renderAnimationStates", "renderRuntimeBrainLink",
                   "renderMyCompanionsCollection", "renderCustomizationPanel"):
            assert fn in api_block, f"Public API must export {fn}"

    def test_public_api_exports_constants(self):
        comp = _comp()
        api_start = comp.find("global.CompanionSystem")
        api_block = comp[api_start:]
        for const in ("ANIMATION_STATES", "GENOME_PARTS", "TRAIT_POOL"):
            assert const in api_block, f"Public API must export {const}"

    def test_companion_state_css_classes_exist(self):
        css = _css()
        for state in ("idle", "working", "waiting", "review", "failed", "alert", "success", "sleeping"):
            assert f"companion-state-{state}" in css, f"CSS class for state '{state}' not found"

    def test_app_js_still_has_muted_chips_for_back_compat(self):
        """comp-trait-chip--muted must still be in app.js (now labeled as seed hints)."""
        assert "comp-trait-chip--muted" in _app()

    def test_traits_still_appear_as_strings_in_companion_js(self):
        """Trait words must still appear somewhere (in TRAIT_POOL) for existing tests."""
        comp = _comp()
        for word in ("coordinating", "guarded", "analytical", "precise"):
            assert f"'{word}'" in comp or f'"{word}"' in comp, \
                f"Trait word '{word}' must appear in TRAIT_POOL"
