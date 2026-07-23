import unittest

from phases.topic_corroboration import (
    _corpus_claims,
    naming_gate,
    render_report,
    summarize,
    validate_claim_checks,
)


class CorpusClaimTests(unittest.TestCase):
    def test_claims_come_from_card_key_passages(self):
        card = {
            "key_passages": {
                "fraud_or_asset_misappropriation": {
                    "epistemic_status": "direct_source_claim",
                    "summary": "customer funds moved to Alameda",
                }
            }
        }
        claims = _corpus_claims(card)
        self.assertEqual(claims[0]["mechanism"], "fraud_or_asset_misappropriation")


class StatusValidationTests(unittest.TestCase):
    def test_invalid_status_is_coerced_and_counted(self):
        result = {"claim_checks": [{"mechanism": "x", "status": "made_up"}]}
        invalid = validate_claim_checks(result)
        self.assertEqual(invalid, 1)
        self.assertEqual(result["claim_checks"][0]["status"], "uncorroborated")

    def test_valid_statuses_pass(self):
        result = {"claim_checks": [{"mechanism": "x", "status": "corroborated"}]}
        self.assertEqual(validate_claim_checks(result), 0)


class SummaryTests(unittest.TestCase):
    def test_counts_by_status(self):
        result = {
            "claim_checks": [
                {"status": "corroborated"},
                {"status": "corroborated"},
                {"status": "uncorroborated"},
                {"status": "contradicted"},
            ],
            "omissions": ["a"],
        }
        summary = summarize(result)
        self.assertEqual(summary["corroborated"], 2)
        self.assertEqual(summary["uncorroborated"], 1)
        self.assertEqual(summary["contradicted"], 1)
        self.assertEqual(summary["omissions"], 1)


class NamingGateTests(unittest.TestCase):
    def test_gate_states_not_domain_intelligence(self):
        gate = naming_gate(1, 20)
        self.assertIn("1/20", gate)
        self.assertIn("NOT domain intelligence", gate)


class RenderTests(unittest.TestCase):
    def test_report_includes_gate_and_sources(self):
        reference = {
            "subject": "FTX",
            "source": "public record",
            "facts": [{"fact": "filed Chapter 11", "citation": "http://example.com"}],
        }
        result = {
            "claim_checks": [
                {"mechanism": "fraud_or_asset_misappropriation",
                 "status": "corroborated", "rationale": "matches filing"}
            ],
            "omissions": ["full repayment expected"],
        }
        md = render_report(reference, result, naming_gate(1, 20))
        self.assertIn("NOT domain intelligence", md)
        self.assertIn("corroborated", md)
        self.assertIn("http://example.com", md)
        self.assertIn("omits", md)


if __name__ == "__main__":
    unittest.main()
