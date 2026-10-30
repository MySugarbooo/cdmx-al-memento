"""Comprobaciones sin red para la fototeca editorial de CDMX AL MEMENTO."""
import json
import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CATALOG = ROOT / "assets/fotos/catalogo-editorial-1100.json"
DISCLAIMER = (
    "Imagen de carácter ilustrativo y referencial; "
    "no constituye evidencia gráfica de los hechos descritos."
)
LICENSES = re.compile(r"^CC BY(?:-SA)? (?:2\.0|2\.5|3\.0|4\.0)$|^CC0(?: 1\.0)?$", re.I)


class FototecaEditorialTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = json.loads(CATALOG.read_text(encoding="utf-8"))
        cls.photos = cls.data["photos"]

    def test_count_and_no_duplicate_files(self):
        self.assertGreater(len(self.photos), 900)
        self.assertEqual(self.data["count"], len(self.photos))
        names = [re.sub(r"[^a-z0-9]", "", x["file"].casefold()) for x in self.photos]
        self.assertEqual(len(names), len(set(names)))
        ids = [x["id"] for x in self.photos]
        self.assertEqual(len(ids), len(set(ids)))

    def test_creative_commons_and_source(self):
        for p in self.photos:
            with self.subTest(file=p["file"]):
                self.assertTrue(p["author"].strip())
                self.assertRegex(p["license"], LICENSES)
                self.assertTrue(p["licenseUrl"].startswith("https://creativecommons.org/"))
                self.assertTrue(p["source"].startswith("https://commons.wikimedia.org/wiki/File:"))
                self.assertTrue(p["topic"].strip())
                self.assertEqual(p["context"], DISCLAIMER)

    def test_only_real_asset_paths_or_commons_previews(self):
        for p in self.photos:
            url = p["url"]
            if url.startswith("/assets/fotos/"):
                self.assertRegex(url, r"^/assets/fotos/[a-z0-9_]+\.jpg$")
                self.assertTrue((ROOT / url.lstrip("/")).is_file(), url)
            else:
                self.assertRegex(url, r"^https://(?:upload|thumb)\.wikimedia\.org/wikipedia/commons/")

    def test_no_known_wrong_cities_or_obvious_nonphotos(self):
        bad = re.compile(r"louisville|kentucky|zacatecas|chihuahua|san francisco|"
                         r"california|bogot[aá]|medell[ií]n|screenshot|\bmapa\b|\bes[c]?udo\b",
                         re.I)
        for p in self.photos:
            with self.subTest(file=p["file"]):
                self.assertIsNone(bad.search(p["file"]))

    def test_frontend_uses_catalog_and_formal_notice(self):
        gallery = (ROOT / "assets/neo-gallery.js").read_text(encoding="utf-8")
        credits = (ROOT / "assets/creditos.js").read_text(encoding="utf-8")
        self.assertIn("/assets/fotos/indice-noticias-1100.json", gallery)
        self.assertIn("/assets/fotos/catalogo-editorial-1100.json", credits)
        news_script = (ROOT / "assets/fotos.js").read_text(encoding="utf-8")
        self.assertIn("/assets/fotos/indice-noticias-1100.json", news_script)
        fast_index = json.loads((ROOT / "assets/fotos/indice-noticias-1100.json").read_text(encoding="utf-8"))
        self.assertEqual(len(fast_index["photos"]), len(self.photos))
        self.assertLess(len(json.dumps(fast_index)), len(json.dumps(self.data)))
        self.assertEqual(
            {p["id"] for p in fast_index["photos"]},
            {p["id"] for p in self.photos}
        )
        self.assertIn(DISCLAIMER, (ROOT / "assets/neo-gallery.js").read_text(encoding="utf-8"))
        self.assertIn(DISCLAIMER, (ROOT / "assets/noticias-locales.js").read_text(encoding="utf-8"))
        self.assertIn(DISCLAIMER, (ROOT / "assets/neo-home.js").read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
