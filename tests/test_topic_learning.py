import unittest

from phases.topic_learning import (
    _best_passage_for,
    build_case_card,
    build_pattern_matrix,
)

CAUSAL_ORDER = [
    "initial_advantage",
    "structural_constraint",
    "decision",
    "mechanism",
    "consequence",
    "response",
]


def _passage(pid, start, mechanisms, roles, epistemic, summary="s"):
    return {
        "passage_id": pid,
        "video_id": "vid",
        "start_seconds": start,
        "youtube_url": "https://youtu.be/vid",
        "labels": {
            "failure_mechanisms": list(mechanisms),
            "causal_roles": list(roles),
            "evidence_types": ["historical_event"],
            "epistemic_status": epistemic,
            "summary": summary,
        },
    }


class BestPassageTests(unittest.TestCase):
    def test_prefers_direct_source_claim_over_inference(self):
        inference = _passage("p1", 10, ["financial_leverage"], [], "derived_inference")
        direct = _passage("p2", 20, ["financial_leverage"], [], "direct_source_claim")
        best = _best_passage_for([inference, direct], "financial_leverage")
        self.assertEqual(best["passage_id"], "p2")

    def test_returns_none_when_mechanism_absent(self):
        p = _passage("p1", 10, ["financial_leverage"], [], "direct_source_claim")
        self.assertIsNone(_best_passage_for([p], "commoditization"))


class CaseCardTests(unittest.TestCase):
    def setUp(self):
        self.case = {
            "subject": "Alpha",
            "case_role": "failure",
            "subject_type": "company",
            "industry": "restaurants",
            "geography": "US",
            "time_period": "1990-2026",
            "failure_states": ["bankruptcy"],
            "failure_mechanisms": ["financial_leverage", "commoditization"],
        }
        self.passages = [
            _passage("p1", 0, ["financial_leverage"], ["decision"], "direct_source_claim"),
            _passage("p2", 30, ["financial_leverage"], ["mechanism"], "derived_inference"),
            _passage("p3", 60, [], ["initial_advantage"], "direct_source_claim"),
        ]

    def test_causal_chain_follows_taxonomy_order(self):
        card = build_case_card("vid", self.case, self.passages, CAUSAL_ORDER)
        roles = [node["causal_role"] for node in card["causal_chain"]]
        self.assertEqual(roles, ["initial_advantage", "decision", "mechanism"])

    def test_evidence_gap_flags_mechanism_without_direct_claim(self):
        card = build_case_card("vid", self.case, self.passages, CAUSAL_ORDER)
        # commoditization is asserted at case level but no passage carries it.
        self.assertIn("commoditization", card["evidence_gaps"])
        # financial_leverage has a direct-source-claim passage, so no gap.
        self.assertNotIn("financial_leverage", card["evidence_gaps"])

    def test_key_passage_is_source_linked(self):
        card = build_case_card("vid", self.case, self.passages, CAUSAL_ORDER)
        ref = card["key_passages"]["financial_leverage"]
        self.assertEqual(ref["passage_id"], "p1")
        self.assertIn("t=0s", ref["deep_link"])


class PatternMatrixTests(unittest.TestCase):
    def test_matrix_has_one_row_per_case_with_mechanism_counts(self):
        card = build_case_card(
            "vid",
            {
                "subject": "Alpha",
                "case_role": "failure",
                "failure_mechanisms": ["financial_leverage"],
            },
            [
                _passage("p1", 0, ["financial_leverage"], [], "direct_source_claim"),
                _passage("p2", 30, ["financial_leverage"], [], "derived_inference"),
            ],
            CAUSAL_ORDER,
        )
        rows = build_pattern_matrix([card], ["financial_leverage", "commoditization"])
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["financial_leverage"], 2)
        self.assertEqual(rows[0]["commoditization"], 0)


if __name__ == "__main__":
    unittest.main()
