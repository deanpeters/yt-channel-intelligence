import unittest

from phases.topic_pedagogy import run_pedagogy_checks


def _card(video_id, subject, case_role, gaps, mech_counts):
    return {
        "video_id": video_id,
        "subject": subject,
        "case_role": case_role,
        "evidence_gaps": gaps,
        "passage_mechanism_counts": mech_counts,
        "key_passages": {},
        "causal_chain": [
            {"causal_role": "decision", "passages": [{"start_seconds": 100}]},
        ],
    }


class PedagogyCheckTests(unittest.TestCase):
    def _clean_notes(self):
        return {
            "lessons": [{"lesson": "x", "evidence": "100s"}],
            "boundary_conditions": ["only in restaurants"],
            "cannot_yet_claim": ["commoditization not directly shown"],
            "counterexample_notes": [],
        }

    def test_all_pass_on_clean_inputs(self):
        cards = [_card("v1", "Alpha", "failure", ["commoditization"], {"financial_leverage": 2})]
        checks = run_pedagogy_checks(cards, {"v1": self._clean_notes()})
        self.assertTrue(checks["overall_pass"])

    def test_hallucinated_citation_fails_gate(self):
        cards = [_card("v1", "Alpha", "failure", [], {"financial_leverage": 1})]
        notes = self._clean_notes()
        notes["lessons"] = [{"lesson": "x", "evidence": "999s"}]
        notes["cannot_yet_claim"] = []
        checks = run_pedagogy_checks(cards, {"v1": notes})
        self.assertFalse(checks["citation_integrity"]["pass"])
        self.assertFalse(checks["overall_pass"])

    def test_counterexample_case_without_notes_fails(self):
        cards = [_card("v1", "Crocs", "turnaround_counterexample", [], {"strategic_drift": 1})]
        notes = self._clean_notes()  # counterexample_notes is empty
        checks = run_pedagogy_checks(cards, {"v1": notes})
        self.assertFalse(checks["counterexample_coverage"]["pass"])
        self.assertIn("Crocs", checks["counterexample_coverage"]["failures"])

    def test_undisclosed_evidence_gap_fails(self):
        cards = [_card("v1", "Alpha", "failure", ["commoditization"], {"financial_leverage": 1})]
        notes = self._clean_notes()
        notes["cannot_yet_claim"] = []
        checks = run_pedagogy_checks(cards, {"v1": notes})
        self.assertFalse(checks["evidence_gap_disclosure"]["pass"])

    def test_single_case_mechanism_is_flagged_provisional(self):
        cards = [
            _card("v1", "Alpha", "failure", [], {"financial_leverage": 2}),
            _card("v2", "Beta", "failure", [], {"financial_leverage": 1, "commoditization": 3}),
        ]
        notes = {"v1": self._clean_notes(), "v2": self._clean_notes()}
        checks = run_pedagogy_checks(cards, notes)
        # financial_leverage spans 2 cases; commoditization only 1 -> provisional.
        provisional = checks["pattern_recurrence"]["provisional_single_case"]
        self.assertIn("commoditization", provisional)
        self.assertNotIn("financial_leverage", provisional)


if __name__ == "__main__":
    unittest.main()
