import tempfile
import unittest
from pathlib import Path

import yaml

from phases.topic_intake import _render_snippet, _timestamped_transcript

SRT = """1
00:00:00,000 --> 00:00:05,000
Intro line one.

2
00:00:05,000 --> 00:00:12,000
Intro line two continues.

3
00:00:25,000 --> 00:00:30,000
A later segment after the bucket boundary.
"""


class TimestampedTranscriptTests(unittest.TestCase):
    def test_buckets_start_with_seconds_marker(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "x.srt"
            path.write_text(SRT, encoding="utf-8")
            out = _timestamped_transcript(str(path), step_seconds=10)
        lines = out.splitlines()
        self.assertTrue(lines[0].startswith("[0s] "))
        self.assertIn("Intro line one.", lines[0])
        # The third segment starts a new bucket at its own timestamp.
        self.assertTrue(any(line.startswith("[25s] ") for line in lines))


class RenderSnippetTests(unittest.TestCase):
    def test_snippet_is_valid_yaml_under_cases_key(self):
        drafts = {
            "vid1": {
                "subject": "Alpha",
                "case_role": "failure",
                "failure_mechanisms": ["financial_leverage"],
                "sponsor_intervals": [{"start": 30, "end": 90, "sponsor": "Acme"}],
            }
        }
        snippet = _render_snippet(drafts)
        parsed = yaml.safe_load(snippet)
        self.assertIn("vid1", parsed["cases"])
        self.assertEqual(parsed["cases"]["vid1"]["case_role"], "failure")


if __name__ == "__main__":
    unittest.main()
