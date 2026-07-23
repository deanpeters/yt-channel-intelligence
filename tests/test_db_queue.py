import sqlite3
import unittest

import db


class QueueTests(unittest.TestCase):
    def setUp(self):
        self.conn = sqlite3.connect(":memory:")
        self.conn.row_factory = sqlite3.Row
        db._init_schema(self.conn)

    def tearDown(self):
        self.conn.close()

    def _add(self, video_id, playlist_index):
        db.upsert_video(
            self.conn,
            video_id=video_id,
            title=f"Video {playlist_index}",
            published="",
            duration=100,
            playlist_index=playlist_index,
        )

    def test_capture_boundary_leaves_later_queue_items_planned(self):
        self._add("first", 1)
        self._add("later", 21)
        queue = db.get_download_queue(
            self.conn,
            max_playlist_index=20,
        )
        self.assertEqual(["first"], [item["video_id"] for item in queue])

    def test_attempt_history_and_success_state_are_recorded(self):
        self._add("one", 1)
        attempt_id = db.begin_attempt(
            self.conn,
            "one",
            "download",
            "worker-1",
        )
        db.finish_attempt(
            self.conn,
            attempt_id,
            "one",
            "succeeded",
            status="downloaded",
            audio_path="audio/one.m4a",
        )
        video = self.conn.execute(
            "SELECT * FROM videos WHERE video_id = 'one'"
        ).fetchone()
        attempt = self.conn.execute(
            "SELECT * FROM capture_attempts WHERE attempt_id = ?",
            (attempt_id,),
        ).fetchone()
        self.assertEqual("downloaded", video["status"])
        self.assertEqual(1, video["attempt_count"])
        self.assertEqual("succeeded", attempt["outcome"])

    def test_discovery_refresh_does_not_reset_completed_status(self):
        self._add("one", 1)
        db.set_status(self.conn, "one", "transcribed")
        self._add("one", 1)
        status = self.conn.execute(
            "SELECT status FROM videos WHERE video_id = 'one'"
        ).fetchone()["status"]
        self.assertEqual("transcribed", status)


if __name__ == "__main__":
    unittest.main()
