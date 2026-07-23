import tempfile
import unittest
from pathlib import Path

from phases.topic_enrich import _apply_overrides, _passages_needing_labels
from phases.topic_review import (
    review_to_overrides,
    stratified_sample,
    write_review_worksheet,
)


def _passage(passage_id, subject, mechanisms, playlist_index=1, start=0):
    return {
        "passage_id": passage_id,
        "video_id": passage_id.split("-")[0],
        "start_seconds": start,
        "end_seconds": start + 30,
        "text": f"text for {passage_id}",
        "is_sponsor": False,
        "include_in_index": True,
        "playlist_index": playlist_index,
        "youtube_url": f"https://youtu.be/{passage_id}",
        "case": {"subject": subject},
        "labels": {
            "causal_roles": [],
            "failure_mechanisms": list(mechanisms),
            "actors": [],
            "evidence_types": [],
            "epistemic_status": "direct_source_claim",
            "summary": f"summary {passage_id}",
            "review_status": "machine_workup",
        },
    }


class StratifiedSampleTests(unittest.TestCase):
    def setUp(self):
        self.passages = [
            _passage("a-000000-000030", "Alpha", ["strategic_drift"], 1, 0),
            _passage("a-000030-000060", "Alpha", ["financial_leverage"], 1, 30),
            _passage("a-000060-000090", "Alpha", [], 1, 60),
            _passage("b-000000-000030", "Beta", ["commoditization"], 2, 0),
        ]

    def test_covers_every_case_stratum(self):
        sample = stratified_sample(self.passages, per_stratum=1, stratify_by="case")
        subjects = {p["case"]["subject"] for p in sample}
        self.assertEqual(subjects, {"Alpha", "Beta"})

    def test_sampling_is_deterministic_for_a_seed(self):
        first = stratified_sample(self.passages, 1, "case", seed=7)
        second = stratified_sample(self.passages, 1, "case", seed=7)
        self.assertEqual(
            [p["passage_id"] for p in first],
            [p["passage_id"] for p in second],
        )

    def test_small_stratum_returns_all_members(self):
        sample = stratified_sample(self.passages, per_stratum=5, stratify_by="case")
        self.assertEqual(len(sample), 4)

    def test_output_sorted_by_playlist_then_start(self):
        sample = stratified_sample(self.passages, per_stratum=5, stratify_by="case")
        keys = [(p["playlist_index"], p["start_seconds"]) for p in sample]
        self.assertEqual(keys, sorted(keys))


class WorksheetRoundTripTests(unittest.TestCase):
    def test_worksheet_columns_convert_back_to_overrides(self):
        passages = [_passage("a-000000-000030", "Alpha", ["strategic_drift"])]
        with tempfile.TemporaryDirectory() as tmp:
            path = str(Path(tmp) / "review.csv")
            write_review_worksheet(passages, path)
            # Simulate a reviewer marking one fix and rewriting the file.
            text = Path(path).read_text(encoding="utf-8")
            header, row = text.splitlines()[0], text.splitlines()[1]
            columns = header.split(",")

            def _set(col, value):
                nonlocal cells
                cells[columns.index(col)] = value

            cells = row.split(",")
            _set("verdict", "fix")
            _set("remove_failure_mechanisms", "strategic_drift")
            _set("add_failure_mechanisms", "commoditization")
            _set("set_epistemic_status", "derived_inference")
            Path(path).write_text(
                header + "\n" + ",".join(cells) + "\n", encoding="utf-8"
            )
            overrides, summary = review_to_overrides(path)

        self.assertEqual(summary["reviewed"], 1)
        self.assertEqual(summary["corrected"], 1)
        entry = overrides["a-000000-000030"]
        self.assertEqual(entry["remove_failure_mechanisms"], ["strategic_drift"])
        self.assertEqual(entry["add_failure_mechanisms"], ["commoditization"])
        self.assertEqual(entry["set_epistemic_status"], "derived_inference")


class LabelSelectionTests(unittest.TestCase):
    def _labeled(self, status, summary):
        passage = _passage("a-000000-000030", "Alpha", ["strategic_drift"])
        passage["labels"]["review_status"] = status
        passage["labels"]["summary"] = summary
        return passage

    def test_blank_summary_is_selected_even_when_not_unlabeled(self):
        curated_blank = self._labeled("curated_workup", "")
        selected = _passages_needing_labels([curated_blank], relabel_all=False)
        self.assertEqual(len(selected), 1)

    def test_labeled_passage_with_summary_is_left_alone(self):
        machine_ok = self._labeled("machine_workup", "a real summary")
        selected = _passages_needing_labels([machine_ok], relabel_all=False)
        self.assertEqual(selected, [])

    def test_sponsor_passage_is_never_selected(self):
        sponsor = self._labeled("machine_workup", "")
        sponsor["include_in_index"] = False
        sponsor["is_sponsor"] = True
        selected = _passages_needing_labels([sponsor], relabel_all=False)
        self.assertEqual(selected, [])


class OverrideApplicationTests(unittest.TestCase):
    def test_remove_and_set_epistemic_are_applied(self):
        passages = [_passage("a-000000-000030", "Alpha", ["strategic_drift"])]
        overrides = {
            "a-000000-000030": {
                "remove_failure_mechanisms": ["strategic_drift"],
                "add_failure_mechanisms": ["commoditization"],
                "set_epistemic_status": "derived_inference",
                "note": "narrator opinion, not a source claim",
            }
        }
        _apply_overrides(passages, overrides)
        labels = passages[0]["labels"]
        self.assertEqual(labels["failure_mechanisms"], ["commoditization"])
        self.assertEqual(labels["epistemic_status"], "derived_inference")
        self.assertEqual(labels["review_status"], "curated_workup")

    def test_add_only_override_is_backward_compatible(self):
        passages = [_passage("a-000000-000030", "Alpha", ["strategic_drift"])]
        _apply_overrides(
            passages,
            {"a-000000-000030": {"add_causal_roles": ["mechanism"]}},
        )
        self.assertEqual(passages[0]["labels"]["causal_roles"], ["mechanism"])
        self.assertEqual(
            passages[0]["labels"]["failure_mechanisms"], ["strategic_drift"]
        )


if __name__ == "__main__":
    unittest.main()
