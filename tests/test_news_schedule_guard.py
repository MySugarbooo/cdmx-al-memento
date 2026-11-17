"""Pruebas para la protección contra ejecuciones horarias duplicadas."""
import unittest
from datetime import datetime, timezone

from scripts.news_schedule_guard import should_run


class NewsScheduleGuardTests(unittest.TestCase):
    def setUp(self):
        self.now = datetime(2026, 11, 17, 10, 7, tzinfo=timezone.utc)

    def test_skips_schedule_when_feed_is_recent(self):
        self.assertFalse(
            should_run("schedule", {"updated": "2026-11-17 09:30 UTC"}, self.now)
        )

    def test_runs_schedule_at_fifty_minutes(self):
        self.assertTrue(
            should_run("schedule", {"updated": "2026-11-17 09:17 UTC"}, self.now)
        )

    def test_runs_schedule_when_feed_is_stale(self):
        self.assertTrue(
            should_run("schedule", {"updated": "2026-11-17 08:00 UTC"}, self.now)
        )

    def test_non_schedule_events_are_never_suppressed(self):
        fresh = {"updated": "2026-11-17 10:00 UTC"}
        for event in ("push", "pull_request", "workflow_dispatch"):
            with self.subTest(event=event):
                self.assertTrue(should_run(event, fresh, self.now))

    def test_missing_or_invalid_timestamp_runs(self):
        for feed in ({}, {"updated": "now"}, None):
            with self.subTest(feed=feed):
                self.assertTrue(should_run("schedule", feed, self.now))

    def test_future_timestamp_does_not_block_recovery(self):
        self.assertTrue(
            should_run("schedule", {"updated": "2026-11-17 10:30 UTC"}, self.now)
        )


if __name__ == "__main__":
    unittest.main()
