import unittest

from phases.topic_synthesis import (
    _evidence_block,
    render_answer_md,
    validate_answer_citations,
)


def _hit(subject, start, text):
    return {
        "text": text,
        "deep_link": f"https://youtu.be/x?t={start}s",
        "metadata": {
            "subject": subject,
            "start_seconds": start,
            "epistemic_status": "direct_source_claim",
            "summary": f"{subject} summary",
        },
    }


class EvidenceBlockTests(unittest.TestCase):
    def test_tags_are_sequential_and_carry_provenance(self):
        block = _evidence_block([_hit("Alpha", 10, "a"), _hit("Beta", 20, "b")])
        self.assertEqual([e["tag"] for e in block], ["E1", "E2"])
        self.assertEqual(block[0]["subject"], "Alpha")
        self.assertEqual(block[1]["timestamp"], 20)


class CitationValidationTests(unittest.TestCase):
    def test_valid_tags_pass(self):
        answer = {"answer": [{"claim": "x", "evidence": ["E1", "E2"]}]}
        self.assertEqual(validate_answer_citations(answer, {"E1", "E2"}), 0)
        self.assertTrue(answer["answer"][0]["citation_ok"])

    def test_unknown_tag_is_flagged(self):
        answer = {"answer": [{"claim": "x", "evidence": ["E9"]}]}
        self.assertEqual(validate_answer_citations(answer, {"E1"}), 1)
        self.assertFalse(answer["answer"][0]["citation_ok"])

    def test_uncited_claim_is_flagged(self):
        answer = {"answer": [{"claim": "x", "evidence": []}]}
        self.assertEqual(validate_answer_citations(answer, {"E1"}), 1)


class RenderTests(unittest.TestCase):
    def test_renders_links_limitations_and_uncited_marker(self):
        evidence = _evidence_block([_hit("Alpha", 10, "a")])
        answer = {
            "answer": [
                {"claim": "grounded", "evidence": ["E1"], "type": "source-supported"},
                {"claim": "floating", "evidence": ["E9"], "type": "analyst-inference"},
            ],
            "limitations": ["single source only"],
        }
        validate_answer_citations(answer, {"E1"})
        md = render_answer_md("Q?", answer, evidence)
        self.assertIn("Alpha @ 10s", md)
        self.assertIn("## Limitations", md)
        self.assertIn("⚠ uncited", md)
        grounded = [line for line in md.splitlines() if "grounded" in line][0]
        self.assertNotIn("uncited", grounded)


if __name__ == "__main__":
    unittest.main()
