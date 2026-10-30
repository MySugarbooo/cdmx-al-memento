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

    def test_context_photo_matches_exact_metro_line_not_another_line(self):
        article = dict(ARTICLE, title="Usuarios del Metro caminan por la Línea 12", category="Metro")
        line_two = dict(context_photo("linea_2"), topic="Metro Línea 2 CDMX", category="Metro")
        generic = dict(context_photo("metro_generico"), topic="Metro de la Ciudad de México", category="Metro")
        line_twelve = dict(context_photo("linea_12"), topic="Metro Línea 12 CDMX", category="Metro")
        old_accident = dict(context_photo("accidente_2021"),
                            topic="Incidente Línea 12 Ciudad México 2021", category="Metro")
        self.assertLess(photos._photo_score(article, line_two), 0)
        self.assertLess(photos._photo_score(article, old_accident), 0)
        self.assertGreater(photos._photo_score(article, line_twelve),
                           photos._photo_score(article, generic))
        with patch.object(photos, "_pool", return_value=[line_two, generic, line_twelve, old_accident]):
            with patch.object(photos, "VERIFIED_EVENTS", Path("/tmp/never-loaded-photo-registry.json")):
                photos.assign_photos([article])
        self.assertEqual(article["photo"]["id"], "linea_12")
        self.assertEqual(article["photo"]["kind"], "representativa")

    def test_subject_outranks_generic_category_or_unrelated_picture(self):
        examples = (
            ("Desfile de Catrinas en el Zócalo de CDMX", "Cultura",
             ("desfile", "Desfile de Catrinas Ciudad de México", "CDMX"),
             ("museo", "Palacio de Bellas Artes Ciudad de México", "Cultura")),
            ("Rescatan perritos en parque de la capital", "Seguridad",
             ("animales", "Animales Bosque de Tlalpan", "Medio Ambiente"),
             ("patrulla", "Patrulla CDMX", "Seguridad")),
            ("Problemas en Iztapalapa", "CDMX",
             ("iztapalapa", "Panorama de Iztapalapa", "Alcaldías"),
             ("reforma", "Paseo de la Reforma", "CDMX")),
        )
        for title, category, preferred, other in examples:
            with self.subTest(title=title):
                article=dict(ARTICLE,title=title,category=category)
                if "Iztapalapa" in title:
                    article["borough"]="Iztapalapa"
                important=dict(context_photo(preferred[0]),topic=preferred[1],category=preferred[2])
                generic=dict(context_photo(other[0]),topic=other[1],category=other[2])
                self.assertGreater(photos._photo_score(article,important),
                                   photos._photo_score(article,generic))

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
