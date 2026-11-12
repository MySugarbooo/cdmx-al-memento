"""Regresión: el HTML SEO se actualiza tras publicar noticias en GitHub Actions."""
import unittest
from pathlib import Path

WORKFLOW = Path(__file__).resolve().parents[1] / ".github/workflows/article-seo.yml"
HEADERS = Path(__file__).resolve().parents[1] / "_headers"


class ArticleSeoWorkflowTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.workflow = WORKFLOW.read_text(encoding="utf-8")
        cls.headers = HEADERS.read_text(encoding="utf-8")

    def test_article_pages_revalidate_after_editorial_updates(self):
        self.assertIn(
            "/articulos/*\n  Cache-Control: no-cache, must-revalidate",
            self.headers,
        )

    def test_refresh_follows_successful_news_run_on_main(self):
        self.assertIn('  workflow_run:\n', self.workflow)
        trigger = self.workflow.split('  workflow_run:\n', 1)[1].split('  push:\n', 1)[0]
        self.assertIn('workflows: ["Actualizar noticias CDMX AL MEMENTO"]', trigger)
        self.assertIn('types: [completed]', trigger)
        self.assertIn('branches: [main]', trigger)
        self.assertIn("github.event.workflow_run.conclusion == 'success'", self.workflow)

    def test_manual_and_periodic_fallbacks_remain(self):
        self.assertIn('  workflow_dispatch:\n', self.workflow)
        self.assertIn("cron: '23 */3 * * *'", self.workflow)
        self.assertIn("'.github/workflows/article-seo.yml'", self.workflow)

    def test_only_main_can_publish_generated_pages(self):
        push_trigger = self.workflow.split('  push:\n', 1)[1].split('permissions:\n', 1)[0]
        self.assertIn('branches: [main]', push_trigger)
        self.assertIn("github.ref == 'refs/heads/main'", self.workflow)


if __name__ == "__main__":
    unittest.main()
