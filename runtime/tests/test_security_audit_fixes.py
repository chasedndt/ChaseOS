"""Security audit fix tests — C-1, C-2, C-3, and provider-agnostic rule assertions.

These tests verify that the three CRITICAL findings from the 2026-05-11 security
audit are enforced in code and cannot silently regress, plus the provider-agnostic
rule (no workflow may call model providers directly).

C-1: sch-strikezone-acquisition-0550.yaml must not autonomously call paid APIs
     without an approval gate. (schedule disabled or requires_approval=true)

C-2: Hermes LLM synthesis must default to False everywhere. No code path may
     call a paid API model by default — operator must explicitly opt in.

C-3: SBP Discord delivery must not post without a draft-review gate.
     sbp_strikezone_digest.yaml declares draft_review_required: true on its discord adapter.

Provider-agnostic rule: Workflow modules must never call provider APIs directly.
     All synthesis must route through execute_synthesis() or the Agent Bus.
"""

from __future__ import annotations

import ast
import inspect
from pathlib import Path
from unittest.mock import patch

import pytest

VAULT_ROOT = Path(__file__).parent.parent.parent


# ── C-2: Hermes LLM synthesis default is False ────────────────────────────────

class TestC2SynthesisOptIn:
    """LLM synthesis must never be called by default — operator must opt in."""

    def test_hermes_watch_synthesize_default_is_false(self):
        """run_hermes_watch must default synthesize=False (not True)."""
        from runtime.workflows import hermes_watch
        import inspect as ins
        sig = ins.signature(hermes_watch.run_hermes_watch)
        # synthesize is read from inputs dict, not a kwarg — verify via source
        source = Path(hermes_watch.__file__).read_text(encoding="utf-8")
        # The default for synthesize in inputs.get() must be False
        assert 'inputs.get("synthesize", False)' in source, (
            "run_hermes_watch must default synthesize=False. "
            "Found 'True' default — C-2 regression."
        )
        assert 'inputs.get("synthesize", True)' not in source, (
            "run_hermes_watch has synthesize=True default — C-2 regression."
        )

    def test_hermes_review_execute_synthesize_default_is_false(self):
        """run_hermes_review_execute must default synthesize=False."""
        from runtime.workflows import hermes_review_execute
        source = Path(hermes_review_execute.__file__).read_text(encoding="utf-8")
        assert 'inputs.get("synthesize", False)' in source
        assert 'inputs.get("synthesize", True)' not in source

    def test_hermes_produce_review_synthesize_default_is_false(self):
        """_produce_review internal function must default synthesize=False."""
        from runtime.workflows.hermes_review_execute import _produce_review
        sig = inspect.signature(_produce_review)
        param = sig.parameters.get("synthesize")
        assert param is not None, "_produce_review missing synthesize param"
        assert param.default is False, (
            f"_produce_review synthesize default is {param.default!r}, expected False. C-2 regression."
        )

    def test_hermes_research_synthesis_default_is_false(self):
        """run_hermes_research_synthesis must default synthesize=False."""
        from runtime.workflows import hermes_research_synthesis
        source = Path(hermes_research_synthesis.__file__).read_text(encoding="utf-8")
        assert 'inputs.get("synthesize", False)' in source
        assert 'inputs.get("synthesize", True)' not in source

    def test_hermes_watch_manifest_declares_llm_synthesis_disabled(self):
        """hermes_watch.yaml must declare llm_synthesis_enabled: false."""
        manifest_path = VAULT_ROOT / "runtime/workflows/registry/hermes_watch.yaml"
        content = manifest_path.read_text(encoding="utf-8")
        assert "llm_synthesis_enabled: false" in content, (
            "hermes_watch.yaml must declare 'llm_synthesis_enabled: false'. C-2 regression."
        )

    def test_run_hermes_watch_does_not_call_synthesis_by_default(self, tmp_path):
        """Invoking run_hermes_watch with no inputs must not call _execute_synthesis."""
        from runtime.workflows.hermes_watch import run_hermes_watch

        synthesis_calls = []

        def mock_synthesis(**kwargs):
            synthesis_calls.append(kwargs)
            return "mock synthesis"

        with patch("runtime.workflows.hermes_review_execute._execute_synthesis", side_effect=mock_synthesis), \
             patch("runtime.agent_bus.bus.list_tasks", return_value=[]), \
             patch("runtime.agent_bus.bus.upsert_heartbeat", return_value=None):
            run_hermes_watch({}, tmp_path)

        assert len(synthesis_calls) == 0, (
            f"_execute_synthesis was called {len(synthesis_calls)} time(s) with no synthesize=True input. "
            "C-2 regression: synthesis must be opt-in."
        )

    def test_run_hermes_watch_calls_synthesis_when_explicitly_enabled(self, tmp_path):
        """When synthesize=True is passed explicitly, synthesis IS invoked (opt-in works)."""
        from runtime.workflows.hermes_watch import run_hermes_watch
        from runtime.agent_bus.bus import create_task

        # Create a real review task so dispatch fires
        task = create_task(
            vault_root=tmp_path,
            sender="OpenClaw",
            recipient="Hermes",
            intent="REVIEW",
            request="test artifact review",
            expected_output="review result",
            notes="artifact_path: 07_LOGS/Build-Logs/test.md\ntask_type: review",
        )

        synthesis_called = []

        def mock_synthesis(**kwargs):
            synthesis_called.append(True)
            return "synthesis result"

        # Create the artifact so the review can read it
        artifact = tmp_path / "07_LOGS/Build-Logs/test.md"
        artifact.parent.mkdir(parents=True, exist_ok=True)
        artifact.write_text("# Test\n\n2026-05-18 content here.\n", encoding="utf-8")

        with patch("runtime.workflows.hermes_review_execute._execute_synthesis", side_effect=mock_synthesis), \
             patch("runtime.agent_bus.bus.upsert_heartbeat", return_value=None):
            run_hermes_watch({"synthesize": True}, tmp_path)

        assert len(synthesis_called) >= 1, (
            "Synthesis was NOT called when synthesize=True was explicitly passed. Opt-in path broken."
        )

    def test_archon_watch_chat_dispatch_synthesize_default_is_false(self):
        """archon_watch._dispatch_chat must default synthesize=False."""
        from runtime.workflows.archon_watch import _dispatch_chat
        sig = inspect.signature(_dispatch_chat)
        param = sig.parameters.get("synthesize")
        assert param is not None, "_dispatch_chat missing synthesize param"
        assert param.default is False, (
            f"archon_watch._dispatch_chat synthesize default is {param.default!r}, expected False."
        )


# ── Provider-agnostic rule ────────────────────────────────────────────────────

class TestProviderAgnosticRule:
    """Workflows must not call model providers directly.

    All synthesis must route through execute_synthesis() or the Agent Bus.
    Direct urllib calls to api.anthropic.com / api.openai.com in workflow
    modules are a governance violation.
    """

    def test_hermes_research_synthesis_no_direct_anthropic_url(self):
        """hermes_research_synthesis.py must not embed the Anthropic API URL."""
        from runtime.workflows import hermes_research_synthesis
        source = Path(hermes_research_synthesis.__file__).read_text(encoding="utf-8")
        assert "api.anthropic.com" not in source, (
            "hermes_research_synthesis.py embeds Anthropic API URL directly — "
            "provider-agnostic rule violation. Route through execute_synthesis()."
        )

    def test_hermes_research_synthesis_no_hardcoded_model(self):
        """hermes_research_synthesis.py must not hardcode a model ID."""
        from runtime.workflows import hermes_research_synthesis
        source = Path(hermes_research_synthesis.__file__).read_text(encoding="utf-8")
        assert '"claude-haiku-4-5-20251001"' not in source, (
            "hermes_research_synthesis.py hardcodes model 'claude-haiku-4-5-20251001' — "
            "provider-agnostic rule violation. Model must be resolved via model_config.yaml."
        )

    def test_hermes_research_synthesis_no_direct_api_key_read(self):
        """hermes_research_synthesis.py must not read ANTHROPIC_API_KEY directly."""
        from runtime.workflows import hermes_research_synthesis
        source = Path(hermes_research_synthesis.__file__).read_text(encoding="utf-8")
        assert 'ANTHROPIC_API_KEY' not in source, (
            "hermes_research_synthesis.py reads ANTHROPIC_API_KEY directly — "
            "provider-agnostic rule violation. Key resolution belongs in execute_synthesis()."
        )

    def test_hermes_research_synthesis_routes_via_execute_synthesis(self):
        """_execute_llm_synthesis must import and call execute_synthesis."""
        from runtime.workflows import hermes_research_synthesis
        source = Path(hermes_research_synthesis.__file__).read_text(encoding="utf-8")
        assert "execute_synthesis" in source, (
            "hermes_research_synthesis.py does not call execute_synthesis() — "
            "synthesis must route through the execution adapter."
        )
        assert "execution_adapters.execute" in source, (
            "hermes_research_synthesis.py does not import from execution_adapters.execute."
        )

    def test_hermes_research_synthesis_llm_synthesis_calls_adapter(self, tmp_path):
        """_execute_llm_synthesis routes to execute_synthesis, not urllib."""
        from unittest.mock import patch, MagicMock
        from runtime.workflows.hermes_research_synthesis import _execute_llm_synthesis

        mock_result = MagicMock()
        mock_result.text = "synthesized output"

        with patch("runtime.execution_adapters.execute.execute_synthesis", return_value=mock_result) as mock_synth:
            result = _execute_llm_synthesis("ws-test", [{"content": "test data"}], vault_root=tmp_path)

        assert result == "synthesized output"
        mock_synth.assert_called_once()
        call_kwargs = mock_synth.call_args[1]
        assert call_kwargs["execution_adapter"] == "hermes"
        assert "ws-test" in call_kwargs["prompt_user"]

    def test_hermes_research_synthesis_llm_synthesis_fail_open(self, tmp_path):
        """_execute_llm_synthesis returns None if execute_synthesis raises."""
        from unittest.mock import patch
        from runtime.workflows.hermes_research_synthesis import _execute_llm_synthesis
        from runtime.execution_adapters.execute import ExecutionAdapterCredentialError

        with patch("runtime.execution_adapters.execute.execute_synthesis",
                   side_effect=ExecutionAdapterCredentialError("no key")):
            result = _execute_llm_synthesis("ws-test", [{"content": "x"}], vault_root=tmp_path)

        assert result is None, (
            "_execute_llm_synthesis must be fail-open: return None on any adapter error."
        )

    def test_hermes_review_execute_no_direct_anthropic_url(self):
        """hermes_review_execute.py must not embed the Anthropic API URL."""
        from runtime.workflows import hermes_review_execute
        source = Path(hermes_review_execute.__file__).read_text(encoding="utf-8")
        assert "api.anthropic.com" not in source, (
            "hermes_review_execute.py embeds Anthropic URL directly — "
            "provider-agnostic rule violation."
        )

    def test_proof_module_has_execute_false_default(self):
        """personal_context_import_provider_execution_proof must default execute=False."""
        import inspect
        from runtime.studio import personal_context_import_provider_execution_proof as pm
        sig = inspect.signature(pm.build_personal_context_import_provider_execution_proof)
        execute_param = sig.parameters.get("execute")
        assert execute_param is not None, "execute param missing from proof module"
        assert execute_param.default is False, (
            f"proof module execute default is {execute_param.default!r}, expected False. "
            "Approved exception requires execute=False default."
        )

    def test_proof_module_has_provider_agnostic_exception_comment(self):
        """Proof module docstring must declare APPROVED EXCEPTION status."""
        from runtime.studio import personal_context_import_provider_execution_proof as pm
        source = Path(pm.__file__).read_text(encoding="utf-8")
        assert "APPROVED EXCEPTION" in source, (
            "personal_context_import_provider_execution_proof.py is missing its "
            "APPROVED EXCEPTION governance annotation. All direct-provider modules "
            "must be explicitly documented."
        )

    def test_provider_agnostic_rule_doc_exists(self):
        """06_AGENTS/Provider-Agnostic-Rule.md must be present."""
        doc_path = VAULT_ROOT / "06_AGENTS/Provider-Agnostic-Rule.md"
        assert doc_path.exists(), (
            "Provider-Agnostic-Rule.md not found at 06_AGENTS/. "
            "Governance doc must exist before enforcement tests pass."
        )

    def test_provider_agnostic_rule_doc_names_approved_exception(self):
        """Provider-Agnostic-Rule.md must document the proof module as an approved exception."""
        doc_path = VAULT_ROOT / "06_AGENTS/Provider-Agnostic-Rule.md"
        content = doc_path.read_text(encoding="utf-8")
        assert "personal_context_import_provider_execution_proof" in content, (
            "Provider-Agnostic-Rule.md must list the proof module as the approved exception."
        )
        assert "Approved Exception" in content or "APPROVED EXCEPTION" in content.upper(), (
            "Provider-Agnostic-Rule.md must have an 'Approved Exceptions' section."
        )


# ── C-3: SBP Discord draft-review gate ───────────────────────────────────────

class TestC3DiscordDraftReviewGate:
    """Discord delivery must not post to community without operator review."""

    def test_strikezone_digest_manifest_declares_draft_review_required(self):
        """sbp_strikezone_digest.yaml discord adapter must have draft_review_required: true."""
        import yaml
        manifest_path = VAULT_ROOT / "runtime/workflows/registry/sbp_strikezone_digest.yaml"
        assert manifest_path.exists(), "sbp_strikezone_digest.yaml not found"
        data = yaml.safe_load(manifest_path.read_text(encoding="utf-8"))
        sbp_config = data.get("sbp_config") or {}
        delivery_adapters = sbp_config.get("delivery_adapters") or []
        discord_adapters = [a for a in delivery_adapters if a.get("type") == "discord"]
        assert discord_adapters, (
            "sbp_strikezone_digest.yaml has no discord delivery adapter — "
            "C-3 cannot be verified."
        )
        for da in discord_adapters:
            assert da.get("draft_review_required") is True, (
                f"discord adapter in sbp_strikezone_digest.yaml has "
                f"draft_review_required={da.get('draft_review_required')!r}. "
                "C-3: must be true to prevent unreviewed AI output reaching Discord."
            )

    def test_discord_adapter_routes_to_draft_when_flag_set(self, tmp_path):
        """DiscordDeliveryAdapter must write draft and NOT POST when draft_review_required=True."""
        from runtime.sbp.delivery_adapters import DiscordDeliveryAdapter

        adapter = DiscordDeliveryAdapter()
        context = {
            "vault_root": str(tmp_path),
            "pipeline_id": "test-pipeline",
            "date": "2026-05-18",
            "draft_review_required": True,
            "webhook_env_var": "TEST_WEBHOOK_URL",
        }
        result = adapter.deliver("# Test content\n\nDraft post.", context)

        assert result.get("draft_written") is True, (
            "DiscordDeliveryAdapter must write draft when draft_review_required=True."
        )
        assert result.get("success") is False, (
            "DiscordDeliveryAdapter must NOT report success when writing draft — "
            "operator must promote before counting as delivered."
        )
        draft_path = tmp_path / "07_LOGS" / "SBP-Runs" / "_drafts" / "2026-05-18-test-pipeline-discord-draft.md"
        assert draft_path.exists(), f"Draft file not written to expected path: {draft_path}"
        assert "Draft post" in draft_path.read_text(encoding="utf-8")

    def test_discord_adapter_does_not_post_when_draft_required(self, tmp_path):
        """DiscordDeliveryAdapter must never call urlopen when draft_review_required=True."""
        from unittest.mock import patch
        from runtime.sbp.delivery_adapters import DiscordDeliveryAdapter

        adapter = DiscordDeliveryAdapter()
        context = {
            "vault_root": str(tmp_path),
            "pipeline_id": "sbp",
            "date": "2026-05-18",
            "draft_review_required": True,
        }
        with patch("runtime.sbp.delivery_adapters.urllib.request.urlopen") as mock_urlopen:
            adapter.deliver("content", context)
        mock_urlopen.assert_not_called(), (
            "DiscordDeliveryAdapter must not call urlopen when draft_review_required=True. "
            "C-3: no network call before operator review."
        )

    def test_discord_adapter_writes_draft_even_when_webhook_env_var_set(self, tmp_path):
        """draft_review_required=True overrides webhook presence — draft is always written first."""
        from unittest.mock import patch
        from runtime.sbp.delivery_adapters import DiscordDeliveryAdapter

        adapter = DiscordDeliveryAdapter()
        context = {
            "vault_root": str(tmp_path),
            "pipeline_id": "sbp",
            "date": "2026-05-18",
            "draft_review_required": True,
            "webhook_env_var": "STRIKEZONE_DISCORD_WEBHOOK_URL",
        }
        with patch.dict("os.environ", {"STRIKEZONE_DISCORD_WEBHOOK_URL": "https://discord.com/api/webhooks/test"}, clear=False):
            with patch("runtime.sbp.delivery_adapters.urllib.request.urlopen") as mock_urlopen:
                result = adapter.deliver("content", context)
        mock_urlopen.assert_not_called()
        assert result.get("draft_written") is True


# ── C-1: Strikezone acquisition schedule state ────────────────────────────────

class TestC1AcquisitionScheduleGate:
    """Acquisition schedule must not fire autonomous paid API calls without a gate."""

    def test_strikezone_acquisition_schedule_exists(self):
        """The schedule file must be present (we verify its state, not delete it)."""
        schedule_path = VAULT_ROOT / "runtime/schedules/sch-strikezone-acquisition-0550.yaml"
        assert schedule_path.exists(), "Schedule file not found at expected path."

    def test_strikezone_acquisition_schedule_is_disabled_or_gated(self):
        """Schedule must be disabled=true OR have approval_gate: true.

        Either is an acceptable remediation for C-1.
        shadow_mode: true + approval_gate: true = C-1 remediation complete 2026-05-18.
        """
        import yaml
        schedule_path = VAULT_ROOT / "runtime/schedules/sch-strikezone-acquisition-0550.yaml"
        data = yaml.safe_load(schedule_path.read_text(encoding="utf-8"))
        enabled = data.get("enabled", True)
        approval_gate = data.get("approval_gate", False)
        assert (not enabled) or approval_gate, (
            f"sch-strikezone-acquisition-0550.yaml: enabled={enabled}, approval_gate={approval_gate}. "
            "C-1: schedule must be disabled or gated behind approval_gate=true."
        )


# ── N-1: start_runtime_daemon must not hardcode --synthesize ─────────────────

class TestN1DaemonSynthesizeNotHardcoded:
    """N-1 (HIGH): start_runtime_daemon must never unconditionally pass --synthesize.

    Hardcoding --synthesize bypasses the C-2 security fix.  The flag must only be
    appended when the caller explicitly opts in.
    """

    def test_start_runtime_daemon_does_not_hardcode_synthesize(self):
        """api.py start_runtime_daemon must not put '--synthesize' in the unconditional cmd list."""
        api_path = VAULT_ROOT / "runtime/studio/shell/api.py"
        source = api_path.read_text(encoding="utf-8")
        # Locate the start_runtime_daemon method body
        method_start = source.find("def start_runtime_daemon(")
        assert method_start != -1, "start_runtime_daemon not found in api.py"
        # Find the next top-level def after the method (to bound the search)
        method_end = source.find("\n    def ", method_start + 1)
        method_body = source[method_start:method_end] if method_end != -1 else source[method_start:]
        # The cmd list must not contain "--synthesize" as a hardcoded element
        # A conditional append (`if synthesize: cmd.append("--synthesize")`) is acceptable.
        # We detect the regression by looking for "--synthesize" inside the list literal.
        import ast
        # Simple heuristic: the line `"--synthesize",` inside a list literal is the problem.
        # The safe pattern is `cmd.append("--synthesize")` guarded by an `if`.
        unsafe_patterns = [
            '"--synthesize",\n',   # list element with trailing comma
            '"--synthesize"\n',    # list element without trailing comma
            "'--synthesize',\n",
            "'--synthesize'\n",
        ]
        for pattern in unsafe_patterns:
            # Only flag if it appears before the conditional guard comment
            if pattern in method_body:
                # Check that it's guarded by `if synthesize`
                idx = method_body.find(pattern)
                # Look back 120 chars for the guard
                context = method_body[max(0, idx - 120):idx]
                assert "if synthesize" in context, (
                    f"N-1: '--synthesize' appears as a hardcoded cmd element without an "
                    f"`if synthesize` guard in start_runtime_daemon. "
                    f"This bypasses the C-2 security fix."
                )

    def test_start_runtime_daemon_accepts_synthesize_param(self):
        """start_runtime_daemon must accept a synthesize parameter (explicit opt-in)."""
        import inspect
        from runtime.studio.shell import api as studio_api
        # StudioAPI is instantiated with a vault_root
        sig = inspect.signature(studio_api.StudioAPI.start_runtime_daemon)
        assert "synthesize" in sig.parameters, (
            "N-1: start_runtime_daemon must declare a synthesize parameter "
            "so callers can explicitly opt in."
        )
        param = sig.parameters["synthesize"]
        assert param.default is False, (
            f"N-1: start_runtime_daemon synthesize default is {param.default!r}, "
            "expected False. Default must be False (opt-out)."
        )

    def test_hermes_daemon_loop_cmd_does_not_pass_synthesize(self):
        """hermes-daemon-loop.cmd must not pass --synthesize to the daemon on non-comment lines."""
        loop_path = Path("C:/Users/chaseos/.hermes/hermes-daemon-loop.cmd")
        if not loop_path.exists():
            pytest.skip("hermes-daemon-loop.cmd not present on this machine")
        content = loop_path.read_text(encoding="utf-8")
        # Only check non-comment lines (CMD comments start with rem or ::)
        active_lines = [
            line for line in content.splitlines()
            if line.strip() and not line.strip().lower().startswith("rem") and not line.strip().startswith("::")
        ]
        active_text = "\n".join(active_lines)
        assert "--synthesize" not in active_text, (
            "N-1: hermes-daemon-loop.cmd passes --synthesize on an active (non-comment) line. "
            "Remove it — synthesis must be operator opt-in."
        )


# ── N-10: vault root must be JSON-encoded, not repr()-encoded ────────────────

class TestN10VaultRootJsonEncoding:
    """N-10 (LOW): vault root path injected into JS must use json.dumps(), not repr().

    repr() produces Python-specific quoting (e.g. backslashes on Windows paths)
    that can break JS string parsing. json.dumps() produces valid JSON strings.
    """

    def test_main_py_uses_json_dumps_not_repr_for_vault_root(self):
        """main.py must use json.dumps(vault_root) when injecting into evaluate_js."""
        main_path = VAULT_ROOT / "runtime/studio/shell/main.py"
        source = main_path.read_text(encoding="utf-8")
        # Must NOT use repr() for the vault root injection
        assert "repr(str(vault_root))" not in source, (
            "N-10: main.py uses repr() to inject vault_root into JS. "
            "Replace with json.dumps() to produce valid JSON string literals."
        )
        # Must use json.dumps (or _json.dumps after aliased import)
        has_json_dumps = "json.dumps(str(vault_root))" in source or "_json.dumps(str(vault_root))" in source
        assert has_json_dumps, (
            "N-10: main.py does not use json.dumps() for vault_root JS injection. "
            "Ensure json.dumps(str(vault_root)) is used in evaluate_js()."
        )
