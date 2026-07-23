import unittest

from phases.topic_domain import DOMAIN_COVERAGE_THRESHOLD, assess_domain


def _result(subject, checks):
    return {
        "subject": subject,
        "source": "public record",
        "summary": {},
        "claim_checks": [{"mechanism": m, "status": s, "rationale": "r"} for m, s in checks],
    }


class AssessDomainTests(unittest.TestCase):
    def test_low_coverage_is_not_domain_intelligence(self):
        results = [_result("FTX", [("fraud", "corroborated")])]
        a = assess_domain(total_cases=50, results=results)
        self.assertFalse(a["is_domain_intelligence"])
        self.assertEqual(a["corroborated_cases"], 1)
        self.assertAlmostEqual(a["coverage"], 0.02)

    def test_contradiction_blocks_domain_even_at_full_coverage(self):
        results = [
            _result("A", [("m", "corroborated")]),
            _result("B", [("m", "contradicted")]),
        ]
        a = assess_domain(total_cases=2, results=results)  # 100% coverage
        self.assertFalse(a["is_domain_intelligence"])
        self.assertEqual(len(a["contradictions"]), 1)
        self.assertEqual(a["contradictions"][0]["subject"], "B")

    def test_broad_clean_coverage_earns_the_label(self):
        n = 10
        results = [_result(f"C{i}", [("m", "corroborated")]) for i in range(n)]
        a = assess_domain(total_cases=n, results=results)  # 100%, no contradiction
        self.assertGreaterEqual(a["coverage"], DOMAIN_COVERAGE_THRESHOLD)
        self.assertTrue(a["is_domain_intelligence"])

    def test_claim_totals_are_summed(self):
        results = [
            _result("A", [("m1", "corroborated"), ("m2", "uncorroborated")]),
            _result("B", [("m3", "corroborated")]),
        ]
        a = assess_domain(total_cases=50, results=results)
        self.assertEqual(a["claim_totals"]["corroborated"], 2)
        self.assertEqual(a["claim_totals"]["uncorroborated"], 1)


if __name__ == "__main__":
    unittest.main()
