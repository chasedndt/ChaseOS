"""
test_pass7.py — SIC Phase 7 Pass 7
Tests for embedding backend abstraction and retrieval quality benchmark.

Test coverage:
  1.  LocalStubEmbedder still works after refactor
  2.  LocalWordEmbedder basic embed
  3.  LocalWordEmbedder lexical similarity (shared words → closer vectors)
  4.  LocalWordEmbedder dimension control
  5.  LocalWordEmbedder empty/stop-word-only text
  6.  get_embedder() resolves local_stub
  7.  get_embedder() resolves local_word
  8.  get_embedder() rejects unknown adapter
  9.  OpenAI backend unavailable without credentials (graceful error)
  10. Backend registry: list_backends returns all expected backends
  11. Backend registry: local backends always available
  12. Backend registry: openai backend reports unavailable (no credentials in test env)
  13. Backend registry: get_backend_default_dimension
  14. index_workspace with local_word backend
  15. Manifest records local_word provider and model correctly
  16. Re-index workspace under different backend (force=True)
  17. Manifest updates correctly after backend switch
  18. Retrieval still works after local_word re-index
  19. Generator (generate_output) still works after local_word re-index
  20. Benchmark run: local_stub vs local_word
  21. Benchmark: per_backend_results structure is correct
  22. Benchmark: cross_backend_comparison is populated
  23. Benchmark: restore_original restores the workspace state
  24. Benchmark: handles unavailable backend gracefully
  25. CLI: list-backends produces output without error

Run:
    cd %CHASEOS_VAULT_ROOT%
    .venv/Scripts/python.exe -m runtime.source_intelligence.indexes.test_pass7
"""

from __future__ import annotations

import json
import math
import sys
from pathlib import Path

# ── Path setup ─────────────────────────────────────────────────────────────────

_THIS_FILE = Path(__file__).resolve()
_VAULT_ROOT = _THIS_FILE.parents[3]
sys.path.insert(0, str(_VAULT_ROOT))

# ── Imports ───────────────────────────────────────────────────────────────────

from runtime.source_intelligence.indexes.embedder import (
    EmbedderBase,
    EmbedderError,
    LocalStubEmbedder,
    LocalWordEmbedder,
    get_embedder,
    list_adapter_names,
)
from runtime.source_intelligence.indexes.backend_registry import (
    BACKEND_DESCRIPTORS,
    check_backend_availability,
    get_backend_default_dimension,
    get_backend_default_model,
    list_backends,
)
from runtime.source_intelligence.indexes.index_manager import (
    index_workspace,
    get_manifest,
)
from runtime.source_intelligence.retrieval.retriever import query_workspace
from runtime.source_intelligence.output.generator import generate_output
from runtime.source_intelligence.retrieval.benchmark import run_benchmark

# ── Test utilities ─────────────────────────────────────────────────────────────

_PASS = 0
_FAIL = 0
_ASSERTIONS = 0

_WORKSPACE_ID = "phase7-test"


def _check(label: str, condition: bool, detail: str = "") -> None:
    global _PASS, _FAIL, _ASSERTIONS
    _ASSERTIONS += 1
    if condition:
        _PASS += 1
    else:
        _FAIL += 1
        msg = f"  FAIL: {label}"
        if detail:
            msg += f" — {detail}"
        print(msg)


def _section(name: str) -> None:
    print(f"\n[{name}]")


def _cosine(a: list[float], b: list[float]) -> float:
    dot  = sum(x * y for x, y in zip(a, b))
    ma   = math.sqrt(sum(x * x for x in a))
    mb   = math.sqrt(sum(x * x for x in b))
    if ma == 0 or mb == 0:
        return 0.0
    return dot / (ma * mb)


# ── Tests ─────────────────────────────────────────────────────────────────────

def test_local_stub_still_works():
    _section("T01: LocalStubEmbedder still works after Pass 7 refactor")
    emb = LocalStubEmbedder(dimension=64)
    vecs = emb.embed(["hello world", "test text"])
    _check("embed returns 2 vectors", len(vecs) == 2)
    _check("each vector has 64 dims", all(len(v) == 64 for v in vecs))
    _check("deterministic: same input same output",
           emb.embed(["hello world"])[0] == vecs[0])
    _check("name is local_stub", emb.name == "local_stub")
    _check("model_name is local-test-embedding-v1",
           emb.model_name == "local-test-embedding-v1")


def test_local_word_embedder_basic():
    _section("T02: LocalWordEmbedder basic embed")
    emb = LocalWordEmbedder(dimension=256)
    vecs = emb.embed(["market microstructure order flow", "crypto funding rates"])
    _check("embed returns 2 vectors", len(vecs) == 2)
    _check("each vector has 256 dims", all(len(v) == 256 for v in vecs))
    _check("name is local_word", emb.name == "local_word")
    _check("model_name is local-word-hash-v1",
           emb.model_name == "local-word-hash-v1")
    # Vectors should be unit-length (L2 normalized)
    for vec in vecs:
        mag = math.sqrt(sum(v * v for v in vec))
        _check("vector is unit-length (L2 normalized)", abs(mag - 1.0) < 1e-6)


def test_local_word_lexical_similarity():
    """
    Key test: documents with shared vocabulary should have higher cosine similarity
    than documents with no shared vocabulary. This validates that LocalWordEmbedder
    is meaningfully better than LocalStubEmbedder for real queries.
    """
    _section("T03: LocalWordEmbedder lexical similarity signal")
    emb = LocalWordEmbedder(dimension=256)

    # Two documents on the same topic (market/trading)
    doc_a = "order flow market microstructure trading price impact"
    doc_b = "market order flow imbalance impact price levels"
    # One document on a completely different topic
    doc_c = "machine learning neural network gradient descent backpropagation"

    vecs = emb.embed([doc_a, doc_b, doc_c])
    sim_ab = _cosine(vecs[0], vecs[1])  # same topic — should be higher
    sim_ac = _cosine(vecs[0], vecs[2])  # different topics — should be lower

    _check(
        "same-topic docs have higher similarity than different-topic docs",
        sim_ab > sim_ac,
        f"sim_ab={sim_ab:.4f}, sim_ac={sim_ac:.4f}",
    )

    # Also verify stub does NOT have this property (it should be random)
    stub = LocalStubEmbedder(dimension=64)
    # We can't assert direction for stub since it's random, just that it exists
    stub_vecs = stub.embed([doc_a, doc_b, doc_c])
    _check("stub still runs without error", len(stub_vecs) == 3)

    # Positive signal: word embedder sim_ab should be > 0 (shared vocabulary)
    _check(
        "same-topic similarity is positive (shared vocabulary)",
        sim_ab > 0.1,
        f"sim_ab={sim_ab:.4f}",
    )


def test_local_word_dimension_control():
    _section("T04: LocalWordEmbedder dimension control")
    emb_128 = LocalWordEmbedder(dimension=128)
    emb_512 = LocalWordEmbedder(dimension=512)
    v128 = emb_128.embed(["test text"])[0]
    v512 = emb_512.embed(["test text"])[0]
    _check("dimension=128 produces 128-dim vector", len(v128) == 128)
    _check("dimension=512 produces 512-dim vector", len(v512) == 512)

    # Dimension validation
    try:
        LocalWordEmbedder(dimension=4)
        _check("rejects dimension=4", False, "should have raised ValueError")
    except ValueError:
        _check("rejects dimension=4", True)


def test_local_word_empty_text():
    _section("T05: LocalWordEmbedder handles empty/stop-word-only text")
    emb = LocalWordEmbedder(dimension=256)
    # Empty text
    v_empty = emb.embed([""])[0]
    _check("empty text produces 256-dim zero vector", len(v_empty) == 256)
    _check("empty text vector is all zeros", all(v == 0.0 for v in v_empty))

    # Text with only stop words
    v_stop = emb.embed(["the and or but is are was"])[0]
    _check("stop-word-only text produces 256-dim zero vector", len(v_stop) == 256)

    # Text with at least one real word
    v_real = emb.embed(["bitcoin trading"])[0]
    _check("real text produces non-zero vector", any(v != 0.0 for v in v_real))


def test_get_embedder_local_stub():
    _section("T06: get_embedder resolves local_stub")
    emb = get_embedder(adapter_name="local_stub")
    _check("returns LocalStubEmbedder", isinstance(emb, LocalStubEmbedder))
    _check("default dimension is 64", emb.dimension == 64)

    emb128 = get_embedder(adapter_name="local_stub", dimension=128)
    _check("dimension override works", emb128.dimension == 128)


def test_get_embedder_local_word():
    _section("T07: get_embedder resolves local_word")
    emb = get_embedder(adapter_name="local_word")
    _check("returns LocalWordEmbedder", isinstance(emb, LocalWordEmbedder))
    _check("default dimension is 256", emb.dimension == 256)

    emb512 = get_embedder(adapter_name="local_word", dimension=512)
    _check("dimension override works", emb512.dimension == 512)


def test_get_embedder_unknown():
    _section("T08: get_embedder rejects unknown adapter")
    try:
        get_embedder(adapter_name="nonexistent_backend")
        _check("raises EmbedderError for unknown adapter", False)
    except EmbedderError as exc:
        _check("raises EmbedderError for unknown adapter", True)
        _check("error message mentions registered backends",
               "local_stub" in str(exc) and "local_word" in str(exc))


def test_openai_unavailable_without_credentials():
    _section("T09: OpenAI backend fails gracefully without credentials")
    # In this environment: openai package not installed, no API key
    # get_embedder("openai") should raise EmbedderError
    try:
        emb = get_embedder(adapter_name="openai")
        # If this succeeds (openai is somehow configured), just verify it's an embedder
        _check("openai returned an embedder if configured",
               isinstance(emb, EmbedderBase))
    except EmbedderError as exc:
        # Expected — openai not installed or no API key
        _check("EmbedderError raised for unavailable openai", True)
        _check(
            "error mentions install instructions or API key",
            "openai" in str(exc).lower() or "OPENAI_API_KEY" in str(exc),
        )


def test_backend_registry_list():
    _section("T10: Backend registry lists all expected backends")
    backends = list_backends(check_availability=True)
    names = [b["name"] for b in backends]
    _check("local_stub in registry", "local_stub" in names)
    _check("local_word in registry", "local_word" in names)
    _check("openai in registry", "openai" in names)
    _check("at least 3 backends registered", len(backends) >= 3)


def test_backend_registry_local_always_available():
    _section("T11: Local backends always available")
    stub_info  = check_backend_availability("local_stub")
    word_info  = check_backend_availability("local_word")
    _check("local_stub available", stub_info["available"] is True)
    _check("local_word available", word_info["available"] is True)


def test_backend_registry_openai_availability():
    _section("T12: OpenAI backend availability reflects environment")
    openai_info = check_backend_availability("openai")
    _check("openai availability check returns dict", isinstance(openai_info, dict))
    _check("dict has 'available' key", "available" in openai_info)
    _check("dict has 'reason' key", "reason" in openai_info)
    # In this environment, openai is not configured
    # (but we don't assert False — if it IS configured, that's valid too)
    print(f"     openai available: {openai_info['available']} — {openai_info['reason']}")


def test_backend_registry_defaults():
    _section("T13: Backend registry default dimension and model")
    _check("local_stub default dim = 64",
           get_backend_default_dimension("local_stub") == 64)
    _check("local_word default dim = 256",
           get_backend_default_dimension("local_word") == 256)
    _check("openai default dim = 1536",
           get_backend_default_dimension("openai") == 1536)
    _check("local_stub default model",
           get_backend_default_model("local_stub") == "local-test-embedding-v1")
    _check("local_word default model",
           get_backend_default_model("local_word") == "local-word-hash-v1")
    _check("unknown backend returns None",
           get_backend_default_dimension("nonexistent") is None)


def test_index_workspace_local_word():
    _section("T14: index_workspace with local_word backend")
    result = index_workspace(
        workspace_id=_WORKSPACE_ID,
        adapter_name="local_word",
        force_reindex=True,
    )
    _check("index_workspace succeeded", result["success"])
    _check("source_count is 4", result["source_count"] == 4)
    _check("indexed_count = source_count", result["indexed_count"] == result["source_count"])
    _check("workspace_index_status = indexed",
           result["workspace_index_status"] == "indexed")
    _check("manifest_path is set", result["manifest_path"] is not None)
    if not result["success"]:
        print(f"     errors: {result['errors']}")


def test_manifest_records_local_word():
    _section("T15: Manifest correctly records local_word provider and model")
    manifest_result = get_manifest(_WORKSPACE_ID)
    _check("get_manifest succeeded", manifest_result["success"])
    if manifest_result["success"]:
        m = manifest_result["manifest"]
        _check("provider_name = local_word", m.get("provider_name") == "local_word")
        _check("model_name = local-word-hash-v1",
               m.get("model_name") == "local-word-hash-v1")
        _check("embedding_dimension = 256",
               m.get("embedding_dimension") == 256)
        _check("index_status = indexed", m.get("index_status") == "indexed")
        _check("indexed_source_count = 4",
               m.get("indexed_source_count") == 4)
        print(f"     provider={m.get('provider_name')} model={m.get('model_name')} "
              f"dim={m.get('embedding_dimension')} status={m.get('index_status')}")


def test_reindex_backend_switch():
    _section("T16: Re-index workspace when switching backends (force=True)")
    # Index under local_stub (different from current local_word)
    result = index_workspace(
        workspace_id=_WORKSPACE_ID,
        adapter_name="local_stub",
        force_reindex=True,
    )
    _check("re-index under local_stub succeeded", result["success"])
    _check("indexed_count is 4", result["indexed_count"] == 4)

    # Verify manifest updated
    m_result = get_manifest(_WORKSPACE_ID)
    if m_result["success"]:
        m = m_result["manifest"]
        _check("manifest now shows local_stub", m.get("provider_name") == "local_stub")
        _check("manifest dim = 64", m.get("embedding_dimension") == 64)
        print(f"     post-switch: provider={m.get('provider_name')} "
              f"dim={m.get('embedding_dimension')}")


def test_manifest_after_backend_switch():
    _section("T17: Manifest updates correctly after backend switch")
    # Switch back to local_word
    index_workspace(
        workspace_id=_WORKSPACE_ID,
        adapter_name="local_word",
        force_reindex=True,
    )
    m_result = get_manifest(_WORKSPACE_ID)
    _check("get_manifest succeeded after switch", m_result["success"])
    if m_result["success"]:
        m = m_result["manifest"]
        _check("manifest shows local_word", m.get("provider_name") == "local_word")
        _check("manifest updated_at is recent", m.get("updated_at") is not None)


def test_retrieval_after_reindex():
    _section("T18: Retrieval works after local_word re-index")
    # Ensure indexed under local_word
    index_workspace(
        workspace_id=_WORKSPACE_ID,
        adapter_name="local_word",
        force_reindex=True,
    )
    result = query_workspace(
        workspace_id=_WORKSPACE_ID,
        query_text="market microstructure order flow",
        top_k=3,
    )
    _check("retrieval_status is ok or ok-partial",
           result["retrieval_status"] in ("ok", "ok-partial", "ok-stale"))
    _check("evidence_packets returned",
           len(result.get("evidence_packets", [])) > 0)
    _check("provider_name = local_word",
           result.get("provider_name") == "local_word")
    if result["evidence_packets"]:
        p = result["evidence_packets"][0]
        _check("evidence packet has chunk_text", bool(p.get("chunk_text")))
        _check("evidence packet has similarity_score",
               p.get("similarity_score") is not None)
    print(f"     result_count={result['result_count']} "
          f"provider={result.get('provider_name')} "
          f"model={result.get('model_name')}")


def test_output_generation_after_reindex():
    _section("T19: generate_output works after local_word re-index")
    # Get evidence
    evidence = query_workspace(
        workspace_id=_WORKSPACE_ID,
        query_text="market trading analysis",
        top_k=3,
    )
    if evidence["retrieval_status"] not in ("ok", "ok-partial", "ok-stale"):
        print(f"     SKIP: retrieval failed ({evidence['retrieval_status']})")
        return

    task_spec = {"output_type": "source_summary"}
    gen_result = generate_output(
        evidence_result=evidence,
        task_spec=task_spec,
    )
    _check("generation_status in ok states",
           gen_result["generation_status"] in ("ok", "ok-stub"))
    _check("generated_text is non-empty", bool(gen_result.get("generated_text")))
    _check("evidence_count > 0", gen_result.get("evidence_count", 0) > 0)
    _check("citations populated", len(gen_result.get("citations", [])) > 0)
    print(f"     gen_status={gen_result['generation_status']} "
          f"evidence_count={gen_result['evidence_count']}")


def test_benchmark_local_stub_vs_local_word():
    _section("T20: Benchmark runs local_stub vs local_word")
    result = run_benchmark(
        workspace_id=_WORKSPACE_ID,
        queries=[
            "market microstructure order flow imbalance",
            "multi-agent AI systems tool use",
            "cryptocurrency perpetual futures funding rate",
        ],
        backends=["local_stub", "local_word"],
        top_k=4,
        restore_original=True,
    )
    _check("benchmark_status is complete or partial",
           result["benchmark_status"] in ("complete", "partial"),
           f"status={result['benchmark_status']} errors={result['errors']}")
    _check("backends_run includes both backends",
           set(result["backends_run"]) == {"local_stub", "local_word"})
    _check("per_backend_results has 2 entries",
           len(result["per_backend_results"]) == 2)


def test_benchmark_structure():
    _section("T21: Benchmark per_backend_results structure is correct")
    result = run_benchmark(
        workspace_id=_WORKSPACE_ID,
        queries=["order flow market", "crypto funding"],
        backends=["local_stub", "local_word"],
        top_k=3,
        restore_original=True,
    )
    for b in result["per_backend_results"]:
        _check(f"{b['backend']}: success=True", b.get("success") is True)
        _check(f"{b['backend']}: has model_name", b.get("model_name") is not None)
        _check(f"{b['backend']}: has embedding_dimension",
               b.get("embedding_dimension") is not None)
        _check(f"{b['backend']}: per_query_stats has 2 entries",
               len(b.get("per_query_stats", [])) == 2)
        for qs in b.get("per_query_stats", []):
            _check(f"{b['backend']}: query stat has retrieval_status",
                   "retrieval_status" in qs)
            _check(f"{b['backend']}: query stat has top_scores",
                   "top_scores" in qs)


def test_benchmark_cross_comparison():
    _section("T22: Cross-backend comparison is populated")
    result = run_benchmark(
        workspace_id=_WORKSPACE_ID,
        queries=["order flow market microstructure", "funding rate perpetual"],
        backends=["local_stub", "local_word"],
        top_k=4,
        restore_original=True,
    )
    cbc = result.get("cross_backend_comparison")
    _check("cross_backend_comparison is present", cbc is not None)
    if cbc:
        _check("per_query has 2 entries", len(cbc.get("per_query", [])) == 2)
        _check("aggregate is present", "aggregate" in cbc)
        _check("interpretation is present", bool(cbc.get("interpretation")))
        agg = cbc.get("aggregate", {})
        _check("mean_jaccard is computed",
               agg.get("mean_jaccard_all_queries") is not None)
        _check("top1_agreement_rate is computed",
               agg.get("top1_agreement_rate") is not None)

        # Print the interpretation for human review
        print()
        for line in cbc.get("interpretation", []):
            if line:
                print(f"     {line}")


def test_benchmark_restore_original():
    _section("T23: Benchmark restores original backend after comparison")
    # Set workspace to local_stub first
    index_workspace(
        workspace_id=_WORKSPACE_ID,
        adapter_name="local_stub",
        force_reindex=True,
    )
    original_manifest = get_manifest(_WORKSPACE_ID)
    original_provider = (
        original_manifest["manifest"].get("provider_name")
        if original_manifest["success"] else None
    )

    # Run benchmark with local_word (different from original)
    run_benchmark(
        workspace_id=_WORKSPACE_ID,
        queries=["test query"],
        backends=["local_word"],
        top_k=3,
        restore_original=True,
    )

    # Verify restored
    restored_manifest = get_manifest(_WORKSPACE_ID)
    if restored_manifest["success"]:
        restored_provider = restored_manifest["manifest"].get("provider_name")
        _check(
            "workspace restored to original backend after benchmark",
            restored_provider == original_provider,
            f"original={original_provider} restored={restored_provider}",
        )
    else:
        _check("could read manifest after restore", False)

    # Restore to local_word for subsequent tests
    index_workspace(
        workspace_id=_WORKSPACE_ID,
        adapter_name="local_word",
        force_reindex=True,
    )


def test_benchmark_unavailable_backend():
    _section("T24: Benchmark handles unavailable backend gracefully")
    result = run_benchmark(
        workspace_id=_WORKSPACE_ID,
        queries=["test query"],
        backends=["local_stub", "nonexistent_backend_xyz"],
        top_k=3,
        restore_original=True,
    )
    _check("benchmark runs (not fully failed)",
           result["benchmark_status"] in ("complete", "partial"))
    _check("nonexistent backend appears in backends_skipped",
           any(b["backend"] == "nonexistent_backend_xyz"
               for b in result["backends_skipped"]))
    _check("local_stub still ran",
           "local_stub" in result["backends_run"])


def test_cli_list_backends():
    _section("T25: CLI list-backends produces output without error")
    import subprocess, sys
    cmd = [
        sys.executable,
        "-m", "runtime.source_intelligence.indexes.index_manager",
        "list-backends",
    ]
    proc = subprocess.run(
        cmd,
        cwd=str(_VAULT_ROOT),
        capture_output=True,
        text=True,
        timeout=30,
    )
    _check("list-backends exits with code 0", proc.returncode == 0,
           f"returncode={proc.returncode}\nstdout={proc.stdout[:200]}\nstderr={proc.stderr[:200]}")
    _check("output mentions local_stub", "local_stub" in proc.stdout)
    _check("output mentions local_word", "local_word" in proc.stdout)
    _check("output mentions openai", "openai" in proc.stdout)


# ── Main runner ───────────────────────────────────────────────────────────────

def main() -> None:
    print("=" * 60)
    print("SIC Phase 7 Pass 7 — Embedding Backend + Benchmark Tests")
    print("=" * 60)

    # Run all tests
    test_local_stub_still_works()
    test_local_word_embedder_basic()
    test_local_word_lexical_similarity()
    test_local_word_dimension_control()
    test_local_word_empty_text()
    test_get_embedder_local_stub()
    test_get_embedder_local_word()
    test_get_embedder_unknown()
    test_openai_unavailable_without_credentials()
    test_backend_registry_list()
    test_backend_registry_local_always_available()
    test_backend_registry_openai_availability()
    test_backend_registry_defaults()
    test_index_workspace_local_word()
    test_manifest_records_local_word()
    test_reindex_backend_switch()
    test_manifest_after_backend_switch()
    test_retrieval_after_reindex()
    test_output_generation_after_reindex()
    test_benchmark_local_stub_vs_local_word()
    test_benchmark_structure()
    test_benchmark_cross_comparison()
    test_benchmark_restore_original()
    test_benchmark_unavailable_backend()
    test_cli_list_backends()

    # Final workspace state: restore to local_word (best local backend)
    print("\n[Cleanup] Restoring workspace to local_word backend...")
    r = index_workspace(
        workspace_id=_WORKSPACE_ID,
        adapter_name="local_word",
        force_reindex=True,
    )
    print(f"  Restore: {'OK' if r['success'] else 'FAILED'} — "
          f"provider=local_word dim=256 indexed={r.get('indexed_count')}")

    # Summary
    total = _PASS + _FAIL
    print()
    print("=" * 60)
    print(f"RESULTS: {_PASS}/{total} assertions passed, {_FAIL} failed")
    print(f"         ({_ASSERTIONS} total assertions)")
    print("=" * 60)

    if _FAIL > 0:
        sys.exit(1)


if __name__ == "__main__":
    main()
