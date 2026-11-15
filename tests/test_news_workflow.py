import re
import unittest
from pathlib import Path


class NewsWorkflowRuntimeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.workflow = (Path(__file__).resolve().parents[1] / ".github" / "workflows" / "news.yml").read_text(encoding="utf-8")

    def test_news_job_timeout_allows_publication_retries(self):
        match = re.search(r"(?m)^    timeout-minutes:\s*(\d+)\s*$", self.workflow)
        self.assertIsNotNone(match, "El workflow debe declarar un límite de tiempo para el job de noticias.")
        self.assertGreaterEqual(
            int(match.group(1)),
            15,
            "El límite debe dejar margen para reintentar la publicación tras un rebase de main.",
        )

    def test_main_news_runs_remain_queued_without_cancellation(self):
        self.assertRegex(self.workflow, r"(?m)^  queue:\s*max\s*$")
        self.assertRegex(self.workflow, r"(?m)^  cancel-in-progress:\s*false\s*$")


if __name__ == "__main__":
    unittest.main()
