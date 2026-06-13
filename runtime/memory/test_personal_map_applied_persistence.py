from __future__ import annotations

import json
import shutil
import unittest
from pathlib import Path

from runtime.memory.candidate_store import (
    approve_personal_map_candidate,
    edit_personal_map_candidate,
    import_personal_map_candidates_from_source,
    load_personal_map_candidates,
)
from runtime.memory.personal_map import (
    apply_approved_personal_map_candidates,
    build_personal_map_apply_preview,
    load_applied_personal_map_graph,
    personal_map_graph_path,
)


_TMP_ROOT = Path(__file__).resolve().parent / "_tmp_personal_map_applied"


class PersonalMapAppliedPersistenceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp_root = _TMP_ROOT
        self._clean_tmp_root()
        self.tmp_root.mkdir(parents=True, exist_ok=True)
        self.source_path = self.tmp_root / "approved_sources" / "personal_map_seed.json"
        self.source_path.parent.mkdir(parents=True, exist_ok=True)
        self.source_path.write_text(
            json.dumps(
                {
                    "nodes": [
                        {
                            "node_id": "domain_chaseos",
                            "node_type": "project",
                            "label": "ChaseOS",
                            "summary": "Local operating-system project.",
                            "tags": ["os"],
                        },
                        {
                            "node_id": "domain_pulse",
                            "node_type": "domain",
                            "label": "ChaseOS Pulse",
                            "summary": "Proactive intelligence domain.",
                        },
                    ],
                    "edges": [
                        {
                            "edge_id": "edge_chaseos_pulse",
                            "source_node_id": "domain_chaseos",
                            "target_node_id": "domain_pulse",
                            "relation": "contains",
                            "confidence": 0.82,
                        }
                    ],
                }
            ),
            encoding="utf-8",
        )

    def tearDown(self) -> None:
        self._clean_tmp_root()

    def _clean_tmp_root(self) -> None:
        if self.tmp_root.exists():
            resolved = self.tmp_root.resolve()
            if resolved.name != "_tmp_personal_map_applied":
                raise AssertionError(f"refusing to remove unexpected path: {resolved}")
            shutil.rmtree(resolved)

    def test_import_edit_approve_apply_persists_inspectable_graph_with_history(self) -> None:
        artifacts = import_personal_map_candidates_from_source(
            self.tmp_root,
            self.source_path,
            approved_sources=[self.source_path],
            data_class="project",
            created_at="2026-05-12T12:00:00+00:00",
        )
        self.assertEqual(len(artifacts), 3)

        candidates = load_personal_map_candidates(self.tmp_root)
        self.assertEqual({candidate.status for candidate in candidates}, {"pending_review"})
        first_node = next(candidate for candidate in candidates if candidate.candidate_type == "node")
        edited = edit_personal_map_candidate(
            self.tmp_root,
            first_node.candidate_id,
            {"summary": "Edited safe local operating-system project summary."},
            editor="operator",
            edited_at="2026-05-12T12:05:00+00:00",
        )
        self.assertEqual(edited.node.summary, "Edited safe local operating-system project summary.")
        self.assertEqual(edited.status_history[-1]["status"], "pending_review")
        self.assertEqual(edited.revisions[-1]["editor"], "operator")

        for candidate in load_personal_map_candidates(self.tmp_root):
            approve_personal_map_candidate(
                self.tmp_root,
                candidate.candidate_id,
                reviewer="operator",
                reviewed_at="2026-05-12T12:10:00+00:00",
            )

        preview = build_personal_map_apply_preview(self.tmp_root)
        self.assertEqual(preview["ready_candidate_count"], 3)
        self.assertEqual(preview["planned_node_writes"], ["domain_chaseos", "domain_pulse"])
        self.assertEqual(preview["planned_edge_writes"], ["edge_chaseos_pulse"])
        self.assertEqual(preview["blocked_writes"], ["SOUL.md", "00_HOME/Operating-System.md", "00_HOME/Principles.md", "02_KNOWLEDGE/"])

        result = apply_approved_personal_map_candidates(
            self.tmp_root,
            operator_confirmed=True,
            applied_at="2026-05-12T12:15:00+00:00",
        )
        self.assertTrue((self.tmp_root / personal_map_graph_path()).exists())
        self.assertEqual(result["applied_node_ids"], ["domain_chaseos", "domain_pulse"])
        self.assertEqual(result["applied_edge_ids"], ["edge_chaseos_pulse"])
        self.assertEqual(result["protected_docs_mutated"], False)
        self.assertEqual(result["canonical_writeback_allowed"], False)

        graph = load_applied_personal_map_graph(self.tmp_root)
        payload = graph.to_dict()
        self.assertEqual(payload["nodes"]["domain_chaseos"]["status"], "applied")
        self.assertEqual(payload["nodes"]["domain_chaseos"]["history"][-1]["event"], "applied")
        self.assertEqual(payload["edges"]["edge_chaseos_pulse"]["status"], "applied")
        self.assertTrue(payload["nodes"]["domain_chaseos"]["evidence"])

        second = apply_approved_personal_map_candidates(
            self.tmp_root,
            operator_confirmed=True,
            applied_at="2026-05-12T12:16:00+00:00",
        )
        self.assertEqual(second["applied_node_ids"], [])
        self.assertEqual(second["already_applied_candidate_count"], 3)

    def test_import_refuses_unapproved_sources_and_secret_like_payloads(self) -> None:
        outside = self.tmp_root / "unapproved.json"
        outside.write_text(json.dumps({"nodes": []}), encoding="utf-8")
        with self.assertRaises(ValueError):
            import_personal_map_candidates_from_source(
                self.tmp_root,
                outside,
                approved_sources=[self.source_path],
            )

        secret_source = self.tmp_root / "approved_sources" / "secret.json"
        secret_source.write_text(
            json.dumps(
                {
                    "nodes": [
                        {
                            "node_id": "bad_secret",
                            "node_type": "preference",
                            "label": "API token",
                            "summary": "test-key-test_1234567890abcdef1234567890abcdef",
                        }
                    ]
                }
            ),
            encoding="utf-8",
        )
        with self.assertRaises(ValueError):
            import_personal_map_candidates_from_source(
                self.tmp_root,
                secret_source,
                approved_sources=[secret_source],
            )
        self.assertFalse((self.tmp_root / "07_LOGS").exists())

    def test_apply_requires_explicit_operator_confirmation_and_keeps_protected_docs_unchanged(self) -> None:
        soul = self.tmp_root / "SOUL.md"
        os_doc = self.tmp_root / "00_HOME" / "Operating-System.md"
        principles = self.tmp_root / "00_HOME" / "Principles.md"
        for path, content in (
            (soul, "soul-before"),
            (os_doc, "os-before"),
            (principles, "principles-before"),
        ):
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content, encoding="utf-8")
        before = {path: path.read_text(encoding="utf-8") for path in (soul, os_doc, principles)}

        import_personal_map_candidates_from_source(
            self.tmp_root,
            self.source_path,
            approved_sources=[self.source_path],
        )
        for candidate in load_personal_map_candidates(self.tmp_root):
            approve_personal_map_candidate(self.tmp_root, candidate.candidate_id)

        with self.assertRaises(ValueError):
            apply_approved_personal_map_candidates(self.tmp_root, operator_confirmed=False)

        after = {path: path.read_text(encoding="utf-8") for path in (soul, os_doc, principles)}
        self.assertEqual(before, after)
        self.assertFalse((self.tmp_root / personal_map_graph_path()).exists())


if __name__ == "__main__":
    unittest.main()
