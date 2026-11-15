"""Regresión: el HTML SEO se actualiza después de publicar noticias en GitHub Actions."""
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / ".github/workflows/article-seo.yml"
NEWS_WORKFLOW = ROOT / ".github/workflows/news.yml"
HEADERS = ROOT / "_headers"


class ArticleSeoWorkflowTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.workflow = WORKFLOW.read_text(encoding="utf-8")
        cls.news_workflow = NEWS_WORKFLOW.read_text(encoding="utf-8")
        cls.headers = HEADERS.read_text(encoding="utf-8")

    def test_article_pages_revalidate_after_editorial_updates(self):
        self.assertIn(
            "/articulos/*\n  Cache-Control: no-cache, must-revalidate",
            self.headers,
        )

    def test_refresh_follows_successful_news_run_on_main(self):
        self.assertNotRegex(self.workflow, r"(?m)^  push:")
        self.assertIn('  workflow_run:\n', self.workflow)
        trigger = self.workflow.split('  workflow_run:\n', 1)[1].split('permissions:\n', 1)[0]
        self.assertIn('workflows: ["Actualizar noticias CDMX AL MEMENTO"]', trigger)
        self.assertIn('types: [completed]', trigger)
        self.assertIn('branches: [main]', trigger)
        self.assertIn("github.event.workflow_run.conclusion == 'success'", self.workflow)

    def test_editorial_source_changes_trigger_news_before_seo(self):
        self.assertIn("'.github/workflows/article-seo.yml'", self.news_workflow)
        self.assertIn("'scripts/build_article_seo.py'", self.news_workflow)
        self.assertIn("'tests/test_article_seo_workflow.py'", self.news_workflow)

    def test_manual_and_periodic_fallbacks_remain(self):
        self.assertIn('  workflow_dispatch:\n', self.workflow)
        self.assertIn("cron: '23 */3 * * *'", self.workflow)

    def test_only_main_can_publish_generated_pages(self):
        self.assertIn('branches: [main]', self.workflow)
        self.assertIn("github.ref == 'refs/heads/main'", self.workflow)


if __name__ == "__main__":
    unittest.main()
