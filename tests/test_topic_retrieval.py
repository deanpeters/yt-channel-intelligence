import unittest

import numpy as np

from phases.topic_retrieval import (
    _hybrid_relevance,
    infer_query_intent,
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


if __name__ == "__main__":
    unittest.main()
