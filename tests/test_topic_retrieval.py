import unittest

import numpy as np

from phases.topic_retrieval import (
    _hybrid_relevance,
    build_scope_filter,
    infer_query_intent,
    resolve_case_tokens,
)


class QueryIntentTests(unittest.TestCase):
    def test_infers_multiple_mechanisms_without_case_ids(self):
        intent = infer_query_intent(
            "Where were warnings ignored or inconvenient feedback suppressed?"
        )
        self.assertIn(
            "feedback_suppression",
            intent["failure_mechanisms"],
        )

    def test_turnaround_infers_response_and_failed_transformation(self):
        intent = infer_query_intent(
            "What turnaround or replacement strategies were attempted?"
        )
        self.assertIn(
            "failed_transformation",
            intent["failure_mechanisms"],
        )
        self.assertIn("response", intent["causal_roles"])

    def test_passage_label_scores_above_case_label_only(self):
        semantic = np.asarray([0.5, 0.5])
        metadatas = [
            {
                "failure_mechanisms": "financial_leverage",
                "case_failure_mechanisms": "financial_leverage",
                "causal_roles": "",
            },
            {
                "failure_mechanisms": "",
                "case_failure_mechanisms": "financial_leverage",
                "causal_roles": "",
            },
        ]
        intent = {
            "failure_mechanisms": ["financial_leverage"],
            "causal_roles": [],
            "case_roles": [],
        }
        scores = _hybrid_relevance(semantic, metadatas, intent)
        self.assertGreater(scores[0], scores[1])

    def test_successful_adaptation_infers_resilience_case(self):
        intent = infer_query_intent(
            "Which case is a successful adaptation that avoided decline?"
        )
        self.assertIn(
            "resilience_counterexample",
            intent["case_roles"],
        )


class ScopeFilterTests(unittest.TestCase):
    def test_no_scope_returns_none(self):
        self.assertIsNone(build_scope_filter())

    def test_single_dimension_has_no_and_wrapper(self):
        where = build_scope_filter(industries=["restaurants"])
        self.assertEqual(where, {"industry": {"$in": ["restaurants"]}})

    def test_multiple_dimensions_are_anded(self):
        where = build_scope_filter(
            case_roles=["failure"],
            playlist_min=1,
            playlist_max=10,
        )
        self.assertIn("$and", where)
        self.assertIn({"case_role": {"$in": ["failure"]}}, where["$and"])
        self.assertIn({"playlist_index": {"$gte": 1}}, where["$and"])
        self.assertIn({"playlist_index": {"$lte": 10}}, where["$and"])


class ResolveCaseTokenTests(unittest.TestCase):
    def setUp(self):
        self.config = {
            "cases": {
                "vid_pizza": {"subject": "Pizza Hut"},
                "vid_five": {"subject": "Five Guys"},
                "vid_panda": {"subject": "Panda Express"},
            }
        }

    def test_exact_video_id_passes_through(self):
        self.assertEqual(
            resolve_case_tokens(self.config, ["vid_panda"]),
            ["vid_panda"],
        )

    def test_subject_substring_is_case_insensitive(self):
        self.assertEqual(
            resolve_case_tokens(self.config, ["pizza"]),
            ["vid_pizza"],
        )

    def test_deduplicates_overlapping_tokens(self):
        self.assertEqual(
            resolve_case_tokens(self.config, ["vid_pizza", "pizza"]),
            ["vid_pizza"],
        )

    def test_unmatched_token_raises(self):
        with self.assertRaises(ValueError):
            resolve_case_tokens(self.config, ["nonexistent"])


if __name__ == "__main__":
    unittest.main()
