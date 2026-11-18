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
        pull_request = self.news_workflow.split("  pull_request:", 1)[1]
        paths = pull_request.split("permissions:", 1)[0]
        self.assertIn("'.github/workflows/article-seo.yml'", paths)
        self.assertIn("'scripts/build_article_seo.py'", paths)
        self.assertIn("'tests/test_article_seo_workflow.py'", paths)
        self.assertIn("'tests/test_article_photo.py'", paths)

    def test_seo_generated_commit_does_not_retrigger_news_pipeline(self):
        self.assertIn(
            "if: github.event_name != 'push' || github.event.head_commit.message != 'Update crawlable article pages'",
            self.news_workflow,
        )
        self.assertIn("cron: '7,22,37,52 * * * *'", self.news_workflow)
        self.assertIn("workflow_dispatch:", self.news_workflow)
        self.assertIn("      - 'index.html'", self.news_workflow)

    def test_generated_editorial_archive_overrides_are_committed(self):
        self.assertIn(
            "git add articulos/ sitemap-articulos.xml robots.txt index.html archivo/index.html archivo/",
            self.workflow,
        )

    def test_manual_and_periodic_fallbacks_remain(self):
        self.assertIn('  workflow_dispatch:\n', self.workflow)
        self.assertIn("cron: '23 */3 * * *'", self.workflow)

    def test_only_main_can_publish_generated_pages(self):
        self.assertIn('branches: [main]', self.workflow)
        self.assertIn("github.ref == 'refs/heads/main'", self.workflow)

    def test_news_schedule_uses_fallback_triggers_and_dedup_guard(self):
        self.assertIn("id: schedule_guard", self.news_workflow)
        self.assertIn("run: python scripts/news_schedule_guard.py", self.news_workflow)
        self.assertEqual(
            8,
            self.news_workflow.count("steps.schedule_guard.outputs.should_run == 'true'"),
        )


if __name__ == "__main__":
    unittest.main()
