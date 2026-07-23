import tempfile
import unittest
from pathlib import Path

from phases.topic_package import plan_archive_contents


class PlanArchiveTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        root = Path(self.tmp.name)
        self.ws = root / "ws"
        (self.ws / "enrichment").mkdir(parents=True)
        (self.ws / "exports").mkdir()
        (self.ws / "audio").mkdir()
        (self.ws / "index" / "chroma_db").mkdir(parents=True)
        (self.ws / "corpus.json").write_text("{}")
        (self.ws / "enrichment" / "passages.jsonl").write_text("{}\n")
        (self.ws / "exports" / "passages.parquet").write_text("x")
        (self.ws / "audio" / "vid1.m4a").write_text("audio")
        (self.ws / "index" / "chroma_db" / "data.bin").write_text("idx")
        tdir = self.ws / "transcripts" / "vid1"
        tdir.mkdir(parents=True)
        (tdir / "transcript.md").write_text("# t")
        self.config_path = str(root / "taxonomy.yaml")
        Path(self.config_path).write_text("corpus_slug: x\n")
        self.config = {"workspace": str(self.ws), "corpus_slug": "x"}
        self.manifest = {
            "records": [
                {"video_id": "vid1", "canonical_transcript": str(tdir / "transcript.md")}
            ]
        }

    def tearDown(self):
        self.tmp.cleanup()

    def _arcnames(self):
        items = plan_archive_contents(self.config_path, self.config, self.manifest)
        return {arc for _, arc in items}

    def test_includes_core_data_files(self):
        arcs = self._arcnames()
        self.assertIn("corpus.json", arcs)
        self.assertIn("taxonomy.yaml", arcs)
        self.assertIn("enrichment/passages.jsonl", arcs)
        self.assertIn("exports/passages.parquet", arcs)
        self.assertIn("transcripts/vid1.md", arcs)

    def test_excludes_audio_and_chroma_index(self):
        arcs = self._arcnames()
        self.assertFalse(any("audio" in a or ".m4a" in a for a in arcs))
        self.assertFalse(any("chroma" in a for a in arcs))


if __name__ == "__main__":
    unittest.main()
