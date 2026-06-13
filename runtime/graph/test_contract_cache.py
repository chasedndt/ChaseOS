"""Tests for the fingerprint-keyed graph scan cache (the 'loads slow' fix)."""

from __future__ import annotations

from pathlib import Path

from runtime.graph.contract_cache import (
    clear_scan_memo,
    incremental_parse,
    memo_lookup,
    memo_store,
    scanner_cache_lookup,
    scanner_cache_store,
    vault_md_fingerprint,
)


def _seed_vault(tmp_path: Path) -> Path:
    vault = tmp_path / "vault"
    notes = vault / "notes"
    notes.mkdir(parents=True)
    (notes / "a.md").write_text("# A\nLinks to [[B]].\n", encoding="utf-8")
    (notes / "b.md").write_text("# B\nBack to [[A]].\n", encoding="utf-8")
    return vault


def test_fingerprint_is_deterministic(tmp_path: Path) -> None:
    vault = _seed_vault(tmp_path)
    fp1, n1 = vault_md_fingerprint(vault)
    fp2, n2 = vault_md_fingerprint(vault)
    assert fp1 == fp2
    assert n1 == n2 == 2


def test_fingerprint_changes_when_a_file_changes(tmp_path: Path) -> None:
    vault = _seed_vault(tmp_path)
    fp_before, _ = vault_md_fingerprint(vault)
    (vault / "notes" / "a.md").write_text("# A\nLinks to [[B]].\nAdded a new line.\n", encoding="utf-8")
    fp_after, _ = vault_md_fingerprint(vault)
    assert fp_before != fp_after


def test_fingerprint_changes_when_a_file_is_added(tmp_path: Path) -> None:
    vault = _seed_vault(tmp_path)
    fp_before, count_before = vault_md_fingerprint(vault)
    (vault / "notes" / "c.md").write_text("# C\n", encoding="utf-8")
    fp_after, count_after = vault_md_fingerprint(vault)
    assert fp_before != fp_after
    assert count_after == count_before + 1


def test_cache_store_and_lookup_roundtrip(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("CHASEOS_GRAPH_SCAN_CACHE_DIR", str(tmp_path / "scancache"))
    vault = _seed_vault(tmp_path)
    params = {"folder_path": None, "max_files": 50}

    miss, fp, key = scanner_cache_lookup(vault, params)
    assert miss is None  # cold cache

    contract = {"graph_input": {"nodes": [{"id": "x"}], "edges": []}, "ok": True}
    assert scanner_cache_store(key, fp, contract) is True

    hit, fp2, key2 = scanner_cache_lookup(vault, params)
    assert hit is not None
    assert hit["_scan_cache"]["hit"] is True
    assert hit["graph_input"]["nodes"] == [{"id": "x"}]


def test_cache_invalidated_when_vault_changes(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("CHASEOS_GRAPH_SCAN_CACHE_DIR", str(tmp_path / "scancache"))
    vault = _seed_vault(tmp_path)
    params = {"folder_path": None, "max_files": 50}
    _miss, fp, key = scanner_cache_lookup(vault, params)
    scanner_cache_store(key, fp, {"graph_input": {"nodes": [{"id": "x"}]}})

    # change the vault → fingerprint changes → lookup misses
    (vault / "notes" / "a.md").write_text("# A\nLinks to [[B]].\nchanged\n", encoding="utf-8")
    miss, _fp2, _key2 = scanner_cache_lookup(vault, params)
    assert miss is None


def test_empty_scan_is_not_cached(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("CHASEOS_GRAPH_SCAN_CACHE_DIR", str(tmp_path / "scancache"))
    vault = _seed_vault(tmp_path)
    _miss, fp, key = scanner_cache_lookup(vault, {"max_files": 50})
    # a blocked/empty scan (no nodes) must not poison the cache
    assert scanner_cache_store(key, fp, {"graph_input": {"nodes": []}}) is False


def test_disabled_via_env(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("CHASEOS_GRAPH_SCAN_CACHE_DIR", str(tmp_path / "scancache"))
    monkeypatch.setenv("CHASEOS_GRAPH_SCAN_CACHE", "0")
    vault = _seed_vault(tmp_path)
    params = {"max_files": 50}
    _miss, fp, key = scanner_cache_lookup(vault, params)
    assert scanner_cache_store(key, fp, {"graph_input": {"nodes": [{"id": "x"}]}}) is False
    miss, _fp, _key = scanner_cache_lookup(vault, params)
    assert miss is None


def test_scanner_wrapper_caches_unchanged_vault(tmp_path: Path, monkeypatch) -> None:
    """End-to-end: the real scanner returns a cache hit on the second call."""
    monkeypatch.setenv("CHASEOS_GRAPH_SCAN_CACHE_DIR", str(tmp_path / "scancache"))
    from runtime.studio.graph_scanner_parser import build_graph_scanner_parser

    vault = _seed_vault(tmp_path)
    r1 = build_graph_scanner_parser(vault, max_files=50)
    assert "_scan_cache" not in r1  # first call is a fresh build
    assert (r1.get("graph_input") or {}).get("nodes")  # produced nodes

    r2 = build_graph_scanner_parser(vault, max_files=50)
    assert r2.get("_scan_cache", {}).get("hit") is True  # second call hits cache

    # change the vault → next call rebuilds (miss)
    # (memo TTL must be 0 here so the file-fingerprint path is exercised)
    monkeypatch.setenv("CHASEOS_GRAPH_SCAN_MEMO_TTL", "0")
    (vault / "notes" / "a.md").write_text("# A\nLinks to [[B]].\nchanged content here.\n", encoding="utf-8")
    r3 = build_graph_scanner_parser(vault, max_files=50)
    assert "_scan_cache" not in r3


# ── in-process memo (resolves "scan runs 2-3x per load") ────────────────────

def test_memo_roundtrip_and_source(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("CHASEOS_GRAPH_SCAN_MEMO_TTL", "100")
    clear_scan_memo()
    vault = _seed_vault(tmp_path)
    params = {"max_files": 50}
    assert memo_lookup(vault, params) is None
    memo_store(vault, params, {"graph_input": {"nodes": [{"id": "x"}]}})
    hit = memo_lookup(vault, params)
    assert hit is not None
    assert hit["_scan_cache"] == {"hit": True, "source": "memo"}


def test_memo_is_immune_to_vault_writes_within_ttl(tmp_path: Path, monkeypatch) -> None:
    """The memo does not re-stat, so it stays a hit even when files change —
    this is what keeps loads fast while Hermes writes the vault."""
    monkeypatch.setenv("CHASEOS_GRAPH_SCAN_MEMO_TTL", "100")
    clear_scan_memo()
    vault = _seed_vault(tmp_path)
    params = {"max_files": 50}
    memo_store(vault, params, {"graph_input": {"nodes": [{"id": "x"}]}})
    # a concurrent write would change the fingerprint — but the memo ignores it
    (vault / "notes" / "a.md").write_text("# A\nLinks to [[B]].\nhermes wrote here.\n", encoding="utf-8")
    assert memo_lookup(vault, params) is not None


def test_memo_expires_at_zero_ttl(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("CHASEOS_GRAPH_SCAN_MEMO_TTL", "0")
    clear_scan_memo()
    vault = _seed_vault(tmp_path)
    params = {"max_files": 50}
    memo_store(vault, params, {"graph_input": {"nodes": [{"id": "x"}]}})
    assert memo_lookup(vault, params) is None


def test_scanner_runs_once_under_repeated_and_concurrent_calls(tmp_path: Path, monkeypatch) -> None:
    """The actual (uncached) scan runs ONCE across repeated calls — even when the
    vault changes between calls — collapsing the 2-3 scans per load to one."""
    monkeypatch.setenv("CHASEOS_GRAPH_SCAN_CACHE_DIR", str(tmp_path / "scancache"))
    monkeypatch.setenv("CHASEOS_GRAPH_SCAN_MEMO_TTL", "100")
    clear_scan_memo()
    import runtime.studio.graph_scanner_parser as gsp

    real = gsp._build_graph_scanner_parser_uncached
    calls = {"n": 0}

    def _counting(*args, **kwargs):
        calls["n"] += 1
        return real(*args, **kwargs)

    monkeypatch.setattr(gsp, "_build_graph_scanner_parser_uncached", _counting)

    vault = _seed_vault(tmp_path)
    gsp.build_graph_scanner_parser(vault, max_files=50)
    gsp.build_graph_scanner_parser(vault, max_files=50)
    # simulate a concurrent write between internal scans of the same load
    (vault / "notes" / "a.md").write_text("# A\nLinks to [[B]].\nconcurrent.\n", encoding="utf-8")
    gsp.build_graph_scanner_parser(vault, max_files=50)
    assert calls["n"] == 1  # memo collapsed all three into a single real scan

    # an explicit refresh drops the memo → next call rescans
    clear_scan_memo()
    gsp.build_graph_scanner_parser(vault, max_files=50)
    assert calls["n"] == 2


# ── persistent incremental parse (kills the COLD-load cost) ─────────────────

def _parse_one_counter():
    calls: list[str] = []

    def parse_one(path: Path) -> dict:
        calls.append(path.name)
        return {"path": path.name, "parsed": {"size": path.stat().st_size}}

    return parse_one, calls


def test_incremental_parse_reuses_unchanged_files(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("CHASEOS_GRAPH_PARSE_INDEX_DIR", str(tmp_path / "pidx"))
    vault = tmp_path / "vault"
    vault.mkdir()
    fa = vault / "a.md"
    fa.write_text("alpha", encoding="utf-8")
    fb = vault / "b.md"
    fb.write_text("beta", encoding="utf-8")
    parse_one, calls = _parse_one_counter()

    _recs, stats = incremental_parse([fa, fb], vault, 1000, parse_one, vault_root=vault)
    assert stats == {"reused": 0, "reparsed": 2, "total": 2}
    assert sorted(calls) == ["a.md", "b.md"]

    # second run, nothing changed → everything reused, no parsing
    calls.clear()
    _recs2, stats2 = incremental_parse([fa, fb], vault, 1000, parse_one, vault_root=vault)
    assert stats2["reused"] == 2 and stats2["reparsed"] == 0
    assert calls == []

    # change ONE file → only that file is reparsed
    fa.write_text("alpha changed and longer", encoding="utf-8")
    calls.clear()
    _recs3, stats3 = incremental_parse([fa, fb], vault, 1000, parse_one, vault_root=vault)
    assert stats3["reparsed"] == 1 and stats3["reused"] == 1
    assert calls == ["a.md"]


def test_incremental_parse_reparses_all_when_byte_limit_changes(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("CHASEOS_GRAPH_PARSE_INDEX_DIR", str(tmp_path / "pidx"))
    vault = tmp_path / "vault"
    vault.mkdir()
    fa = vault / "a.md"
    fa.write_text("alpha", encoding="utf-8")
    parse_one, calls = _parse_one_counter()
    incremental_parse([fa], vault, 1000, parse_one, vault_root=vault)
    calls.clear()
    # different byte_limit → different index → reparse
    _r, stats = incremental_parse([fa], vault, 2000, parse_one, vault_root=vault)
    assert stats["reparsed"] == 1
    assert calls == ["a.md"]


def test_incremental_parse_disabled_parses_all(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("CHASEOS_GRAPH_PARSE_INDEX_DIR", str(tmp_path / "pidx"))
    monkeypatch.setenv("CHASEOS_GRAPH_SCAN_CACHE", "0")
    vault = tmp_path / "vault"
    vault.mkdir()
    fa = vault / "a.md"
    fa.write_text("alpha", encoding="utf-8")
    parse_one, calls = _parse_one_counter()
    incremental_parse([fa], vault, 1000, parse_one, vault_root=vault)
    calls.clear()
    _r, stats = incremental_parse([fa], vault, 1000, parse_one, vault_root=vault)
    assert stats["reparsed"] == 1  # cache disabled → always parse


def test_real_scanner_reparses_only_changed_file(tmp_path: Path, monkeypatch) -> None:
    """End-to-end: a cold rescan after one file changes re-reads only that file."""
    monkeypatch.setenv("CHASEOS_GRAPH_SCAN_CACHE_DIR", str(tmp_path / "sc"))
    monkeypatch.setenv("CHASEOS_GRAPH_PARSE_INDEX_DIR", str(tmp_path / "pidx"))
    monkeypatch.setenv("CHASEOS_GRAPH_SCAN_MEMO_TTL", "0")  # force the build path
    clear_scan_memo()
    import runtime.studio.graph_scanner_parser as gsp

    real_scan_file = gsp._scan_file
    counted: list[str] = []

    def _counting(path, target, byte_limit):
        counted.append(Path(path).name)
        return real_scan_file(path, target, byte_limit)

    monkeypatch.setattr(gsp, "_scan_file", _counting)

    vault = tmp_path / "vault"
    notes = vault / "notes"
    notes.mkdir(parents=True)
    (notes / "a.md").write_text("# A\n[[B]]\n", encoding="utf-8")
    (notes / "b.md").write_text("# B\n[[A]]\n", encoding="utf-8")
    (notes / "c.md").write_text("# C\n", encoding="utf-8")

    gsp.build_graph_scanner_parser(vault, max_files=50)
    assert sorted(counted) == ["a.md", "b.md", "c.md"]  # cold build parses all

    counted.clear()
    (notes / "a.md").write_text("# A changed\n[[B]]\nextra line\n", encoding="utf-8")
    gsp.build_graph_scanner_parser(vault, max_files=50)
    assert counted == ["a.md"]  # incremental: only the changed file is reparsed
