from pathlib import Path
import unittest


class NewsWorkflowTimeoutTests(unittest.TestCase):
    def test_news_workflow_allows_a_full_rebuild_after_rebase_conflict(self):
        repo_root = Path(__file__).resolve().parents[1]
        workflow = (repo_root / ".github" / "workflows" / "news.yml").read_text(encoding="utf-8")

        self.assertRegex(workflow, r"(?m)^\s*timeout-minutes:\s*25\s*$")
        self.assertIn("queue: max", workflow)
        self.assertIn("cancel-in-progress: false", workflow)
        self.assertIn("cron: '17 * * * *'", workflow)


if __name__ == "__main__":
    unittest.main()
