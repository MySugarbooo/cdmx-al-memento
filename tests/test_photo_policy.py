"""Regresión: fotografía real del hecho solo si coincide y admite reutilización."""
import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from scripts import notas_locales as photos


ARTICLE = {
    "title": "Incidente verificado en CDMX",
    "url": "https://news.google.com/rss/articles/evento-test",
    "date": "2026-10-30",
    "category": "CDMX",
    "borough": "",
}


def approval(**overrides):
    data = {
        "article_url": ARTICLE["url"],
        "article_title": ARTICLE["title"],
        "url": "https://upload.wikimedia.org/wikipedia/commons/a/ab/evento.jpg",
        "source": "https://commons.wikimedia.org/wiki/File:Evento.jpg",
        "evidence_url": "https://ejemplo.org/cobertura/acontecimiento",
        "author": "Fotógrafa acreditada",
        "license": "CC BY-SA 4.0",
        "licenseUrl": "https://creativecommons.org/licenses/by-sa/4.0/",
        "topic": "Acontecimiento documentado",
        "event_match_confirmed": True,
        "rights_confirmed": True,
        "reviewed_by": "Edición responsable",
        "reviewed_at": "2026-10-30T10:00:00Z",
    }
    data.update(overrides)
    return data


def context_photo(id_="archivo_prueba"):
    return {
        "id": id_, "kind": "representativa",
        "url": "/assets/fotos/" + id_ + ".jpg",
        "category": "CDMX", "borough": "",
        "topic": "Vista general de la ciudad",
        "source": "https://commons.wikimedia.org/wiki/File:Ciudad.jpg",
        "author": "Autor de contexto",
        "license": "CC BY 4.0",
        "licenseUrl": "https://creativecommons.org/licenses/by/4.0/",
    }


class NewsPhotoPolicyTests(unittest.TestCase):
    def test_only_reviewed_licensed_exact_event_can_be_labelled_as_such(self):
        result = photos.verified_event_photo(ARTICLE, [approval()])
        self.assertEqual(result["kind"], "hecho")
        self.assertTrue(result["verified"])
        self.assertEqual(result["author"], "Fotógrafa acreditada")

    def test_similar_title_copyright_or_unproven_event_never_count_as_real(self):
        for changes in (
            {"article_title": "Otra noticia del mismo tema"},
            {"article_url": "https://news.google.com/rss/articles/otra"},
            {"event_match_confirmed": False},
            {"rights_confirmed": False},
            {"evidence_url": ""},
            {"reviewed_by": ""},
            {"reviewed_at": "no revisado"},
            {"license": "CC BY-NC 4.0"},
            {"licenseUrl": "https://creativecommons.org/licenses/by-nc/4.0/"},
            {"source": "https://unperiodico.example/foto.jpg"},
            {"url": "https://medio.example/foto.jpg"},
        ):
            with self.subTest(changes=changes):
                self.assertIsNone(photos.verified_event_photo(ARTICLE, [approval(**changes)]))

    def test_exact_preferred_then_licensed_representative(self):
        with TemporaryDirectory() as tmp:
            registry = Path(tmp) / "hechos.json"
            registry.write_text(json.dumps({"photos": [approval()]}), encoding="utf-8")
            with patch.object(photos, "VERIFIED_EVENTS", registry), patch.object(
                photos, "_pool", return_value=[context_photo()]
            ):
                article = dict(ARTICLE)
                stats = photos.assign_photos([article])
                self.assertEqual(stats["del_hecho_verificadas"], 1)
                self.assertEqual(article["photo"]["kind"], "hecho")
                registry.write_text(json.dumps({"photos": []}), encoding="utf-8")
                article["photo"] = approval(kind="hecho", verified=True, id="hecho_antiguo")
                stats = photos.assign_photos([article])
                self.assertEqual(stats["del_hecho_verificadas"], 0)
                self.assertEqual(article["photo"]["kind"], "representativa")
                self.assertFalse(article["photo"].get("verified", False))


if __name__ == "__main__":
    unittest.main()
