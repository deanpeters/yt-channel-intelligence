import unittest

from phases.topic_teaching import (
    _counterexample_directive,
    render_teaching_md,
    valid_timestamps,
    validate_citations,
)


def _card():
    return {
        "subject": "Alpha",
        "case_role": "failure",
        "industry": "restaurants",
        "failure_states": ["bankruptcy"],
        "evidence_gaps": ["commoditization"],
        "key_passages": {
            "financial_leverage": {
                "start_seconds": 100,
                "epistemic_status": "direct_source_claim",
                "summary": "debt load",
            },
        },
        "causal_chain": [
            {"causal_role": "decision", "passages": [{"start_seconds": 200}]},
        ],
    }


class ValidTimestampTests(unittest.TestCase):
    def test_collects_key_passage_and_chain_timestamps(self):
        self.assertEqual(valid_timestamps(_card()), {100, 200})


class CitationValidationTests(unittest.TestCase):
    def test_valid_citation_is_marked_ok(self):
        notes = {"lessons": [{"lesson": "x", "evidence": "100s"}]}
        invalid = validate_citations(notes, {100, 200})
        self.assertEqual(invalid, 0)
        self.assertTrue(notes["lessons"][0]["citation_ok"])

    def test_hallucinated_timestamp_is_flagged(self):
        notes = {"lessons": [{"lesson": "x", "evidence": "999s"}]}
        invalid = validate_citations(notes, {100, 200})
        self.assertEqual(invalid, 1)
        self.assertFalse(notes["lessons"][0]["citation_ok"])

    def test_missing_citation_is_flagged(self):
        notes = {"lessons": [{"lesson": "x", "evidence": ""}]}
        invalid = validate_citations(notes, {100, 200})
        self.assertEqual(invalid, 1)


class CounterexampleDirectiveTests(unittest.TestCase):
    def test_counterexample_role_requires_notes(self):
        card = _card()
        card["case_role"] = "turnaround_counterexample"
        self.assertIn("MUST", _counterexample_directive(card))

    def test_plain_failure_role_leaves_notes_empty(self):
        directive = _counterexample_directive(_card())
        self.assertIn("empty", directive)
        self.assertNotIn("MUST", directive)


class RenderTests(unittest.TestCase):
    def test_uncited_lesson_gets_a_warning_marker(self):
        card = _card()
        notes = {
            "lessons": [
                {"lesson": "good", "evidence": "100s", "type": "source-supported"},
                {"lesson": "bad", "evidence": "999s", "type": "analyst-inference"},
            ],
            "cannot_yet_claim": ["commoditization is not directly evidenced"],
        }
        validate_citations(notes, valid_timestamps(card))
        md = render_teaching_md(card, notes)
        self.assertIn("⚠ uncited", md)
        self.assertIn("Cannot yet claim", md)
        # The source-supported, correctly-cited lesson has no warning on its line.
        good_line = [line for line in md.splitlines() if "good" in line][0]
        self.assertNotIn("uncited", good_line)


if __name__ == "__main__":
    unittest.main()
