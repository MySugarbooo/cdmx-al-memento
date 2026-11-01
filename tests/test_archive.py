"""Pruebas básicas del archivo de un año y metadatos editoriales."""
import json
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import patch
import update_news as news


def fake(title, date, published_at=None):
    return {
        "title": title, "source": "Medio de prueba",
        "url": "https://news.google.com/rss/articles/example" + date.replace("-", ""),
        "date": date, "published_at": published_at,
        "category": "CDMX",
    }


class BoroughAndArchiveTests(unittest.TestCase):
    def test_first_boroughs_and_exact_mentions(self):
        self.assertEqual(news.BOROUGHS[:2], ("La Magdalena Contreras", "Álvaro Obregón"))
        self.assertEqual(news.identify_location("Noticias en Magdalena Contreras")[0], "La Magdalena Contreras")
        self.assertEqual(news.identify_location("Cierre vial en Álvaro Obregón CDMX")[0], "Álvaro Obregón")
        self.assertEqual(news.identify_location("Incidente en Iztapalapa")[0], "Iztapalapa")
        self.assertEqual(news.identify_location("En Coyoacán y Tlalpan")[0], "")
        self.assertEqual(news.identify_location("Los planes del Metro CDMX")[0], "")

    def test_unambiguous_outside_region_is_not_promoted_or_mislocated(self):
        title = "Muere conductor tras chocar contra autobús en Carretera a Laredo en Escobedo"
        self.assertTrue(news.outside_cdmx_scope(title))
        spain = "México confirma once connacionales heridos en el accidente de tren en España"
        self.assertTrue(news.outside_cdmx_scope(spain))
        self.assertEqual(news.identify_location(spain)[1], "España (fuera de CDMX)")
        self.assertFalse(news.outside_cdmx_scope("Exposición sobre trenes de España en CDMX"))
        self.assertFalse(news.outside_cdmx_scope("Familias acuden a panteones de CdMx y Monterrey"))
        self.assertFalse(news.outside_cdmx_scope("Cierre vial en la alcaldía Xochimilco"))
        self.assertFalse(news.outside_cdmx_scope("CDMX y Escobedo: carreteras a Laredo en discusión"))
        date = datetime.now(timezone.utc).date().isoformat()
        outside = news.standardize(fake(title, date))
        local = news.standardize(fake("Cierre vial en Xochimilco CDMX", date))
        self.assertEqual(outside["location"], "Escobedo, Nuevo León (fuera de CDMX)")
        self.assertEqual(news.homepage_articles([outside, local], [], datetime.now(timezone.utc)),
                         [local])
        # El registro puede conservarse en la hemeroteca; solo se evita
        # su incorporación a la portada de noticias de CDMX.

    def test_source_time_is_real_or_missing(self):
        now="2026-10-11T23:40:00Z"
        article=news.standardize(fake("Una noticia sobre Xochimilco en CDMX", "2026-10-11", now))
        self.assertEqual(article["published_at"], now)
        self.assertEqual(article["borough"], "Xochimilco")
        self.assertEqual(article["date"], "2026-10-11")
        legacy=news.standardize(fake("Una noticia sobre Xochimilco en CDMX", "2026-10-11"))
        self.assertIsNone(legacy["published_at"])
        self.assertEqual(legacy["location"], "Xochimilco (mencionada en el titular)")

    def test_older_than_365_days_expires_even_within_month(self):
        now=datetime.now(timezone.utc)
        cutoff=now-timedelta(days=365)
        expired=(now-timedelta(days=366)).date().isoformat()
        kept=(now-timedelta(days=364)).date().isoformat()
        old=news.standardize(fake("Titular antiguo del Metro CDMX", expired))
        current=news.standardize(fake("Titular reciente en Xochimilco", kept))
        self.assertFalse(news.still_valid(old, cutoff))
        self.assertTrue(news.still_valid(current, cutoff))

    def test_months_merge_and_old_files_deleted(self):
        now=datetime.now(timezone.utc)
        date=(now-timedelta(days=1)).date().isoformat()
        earlier=(now-timedelta(days=400)).date().isoformat()
        story=news.standardize(fake("Reunión comunitaria en Magdalena Contreras", date))
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            archive=root/"archivo"
            archive.mkdir()
            # Un archivo de un mes vencido no debe mantenerse.
            news.write_json(archive/(earlier[:7]+".json"), {
                "month":earlier[:7],
                "articles":[news.standardize(fake("Información vencida en CDMX", earlier))]
            })
            with patch.multiple(news, ARCHIVE_DIR=archive,
                                BOROUGH_DIR=root/"alcaldias", DEST=root/"news.json"):
                months=news.consolidate_archive([story], now-timedelta(days=365), "Prueba")
                self.assertEqual(len(months), 1)
                self.assertEqual(months[0]["month"], date[:7])
                self.assertFalse((archive/(earlier[:7]+".json")).exists())
                saved=json.loads((archive/(date[:7]+".json")).read_text(encoding="utf-8"))
                self.assertEqual(len(saved["articles"]), 1)
                self.assertEqual(saved["articles"][0]["borough"], "La Magdalena Contreras")
                directory=json.loads((root/"alcaldias"/"noticias.json").read_text(encoding="utf-8"))
                self.assertEqual(len(directory["boroughs"]), 16)


    def test_archive_repairs_unrelated_photo_and_preserves_verified_photo(self):
        now = datetime.now(timezone.utc)
        date = (now - timedelta(days=1)).date().isoformat()
        old = news.standardize(fake("Muévete en Bici recorre seis alcaldías", date))
        old["category"] = "Seguridad"  # Etiqueta RSS anterior, corregida al releer.
        old["photo"] = {
            "id": "patrullas", "kind": "representativa",
            "category": "Seguridad", "topic": "Entrega de patrullas",
            "url": "/assets/fotos/patrullas.jpg",
        }
        verified = news.standardize(fake("Ciclistas recorren avenida de CDMX", date))
        verified["photo"] = {
            "id": "hecho_confirmado", "kind": "hecho", "verified": True,
            "category": "Movilidad", "topic": "Ciclistas en la avenida",
            "url": "/assets/fotos/hecho_confirmado.jpg",
        }

        def assign_replacement(items):
            self.assertEqual(len(items), 1)
            self.assertEqual(items[0]["category"], "Movilidad")
            items[0]["photo"] = {
                "id": "bicicletas", "kind": "representativa",
                "category": "Movilidad", "topic": "Estación de bicicletas",
                "url": "/assets/fotos/bicicletas.jpg",
            }
            return {"assigned": 1}

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            archive = root / "archivo"
            archive.mkdir()
            news.write_json(archive / (date[:7] + ".json"), {
                "month": date[:7], "articles": [old, verified],
            })
            with patch.multiple(news, ARCHIVE_DIR=archive,
                                BOROUGH_DIR=root / "alcaldias",
                                DEST=root / "news.json"):
                with patch.object(news, "assign_photos", side_effect=assign_replacement) as replacement:
                    news.consolidate_archive([], now - timedelta(days=365), "Prueba")
                    replacement.assert_called_once()
            saved = json.loads((archive / (date[:7] + ".json")).read_text(encoding="utf-8"))
            self.assertEqual(len(saved["articles"]), 2)
            by_title = {item["title"]: item for item in saved["articles"]}
            self.assertEqual(by_title[old["title"]]["photo"]["id"], "bicicletas")
            self.assertEqual(by_title[verified["title"]]["photo"]["id"], "hecho_confirmado")


    def test_archive_prioritizes_recent_mismatched_photos(self):
        now = datetime.now(timezone.utc)
        records = {}
        for age in range(26, 0, -1):
            day = (now - timedelta(days=age)).date().isoformat()
            item = news.standardize(fake(f"Muévete en Bici recorre seis alcaldías {age}", day))
            item["category"] = "Seguridad"
            item["photo"] = {
                "id": f"patrullas_{age}", "kind": "representativa",
                "category": "Seguridad", "topic": "Entrega de patrullas",
                "url": "/assets/fotos/patrullas.jpg",
            }
            records.setdefault(day[:7], []).append(item)

        selected = []

        def repair(items):
            selected.extend(item["date"] for item in items)
            for item in items:
                item["photo"] = {
                    "id": "bici", "kind": "representativa",
                    "category": "Movilidad", "topic": "Bicicletas",
                    "url": "/assets/fotos/bicicletas.jpg",
                }
            return {"assigned": len(items)}

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            archive = root / "archivo"
            archive.mkdir()
            for month, articles in records.items():
                news.write_json(archive / (month + ".json"), {
                    "month": month, "articles": articles,
                })
            with patch.multiple(news, ARCHIVE_DIR=archive,
                                BOROUGH_DIR=root / "alcaldias",
                                DEST=root / "news.json"):
                with patch.object(news, "assign_photos", side_effect=repair):
                    news.consolidate_archive([], now - timedelta(days=365), "Prueba")

        self.assertEqual(len(selected), 24)
        self.assertEqual(selected[0], (now - timedelta(days=1)).date().isoformat())
        self.assertEqual(selected[-1], (now - timedelta(days=24)).date().isoformat())


if __name__ == "__main__":
    unittest.main()
