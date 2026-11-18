"""Regresiones: fotografías locales en artículos HTML indexables."""
import json
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from build_article_seo import apply_editorial_record_overrides, render, render_photo


class ArticlePhotoTests(unittest.TestCase):
    def test_historic_airport_article_does_not_show_unrelated_monument(self):
        page = (Path(__file__).resolve().parents[1] /
                "articulos/16c3ecff879d86a90e17/index.html").read_text(encoding="utf-8")
        self.assertIn("Aeropuerto Internacional de la Ciudad de México", page)
        self.assertNotIn("Monumento_a_Col", page)
        self.assertIn("Sin fotografía del aeropuerto", page)

    def test_article_preserves_exact_confirmed_location(self):
        item = {
            "title": "Asamblea comunitaria determina relevo de autoridades auxiliares en Álvaro Obregón",
            "source": "Meganoticias.mx", "date": "2026-11-01",
            "local_url": "/noticias/?id=69e99bd8aec5a3438db7&mes=2026-11",
            "location": "Álvaro Obregón, Juchitán, Oaxaca (fuera de CDMX)",
            "category": "CDMX",
        }
        page = render(item, "69e99bd8aec5a3438db7")
        self.assertIn("<p>Álvaro Obregón, Juchitán, Oaxaca (fuera de CDMX) · 2026-11-01", page)
        self.assertNotIn("<p>CDMX · 2026-11-01", page)

        item["location"] = "Coyoacán (mencionada en el titular)"
        page = render(item, "69e99bd8aec5a3438db7")
        self.assertIn("<p>Coyoacán (mencionada en el titular) · 2026-11-01", page)
        self.assertNotIn("<p>CDMX · 2026-11-01", page)

        item["location"] = "Gustavo A. Madero, Ciudad de México (Línea 1 del Cablebús)"
        page = render(item, "69e99bd8aec5a3438db7")
        self.assertIn("<p>Gustavo A. Madero, Ciudad de México (Línea 1 del Cablebús) · 2026-11-01", page)

    def test_verified_infobae_source_url_is_clickable(self):
        source_url = (
            "https://www.infobae.com/mexico/2026/11/13/"
            "maria-leon-presento-su-nueva-era-de-villana-en-el-teatro-metropolitan-"
            "de-la-cdmx-entre-invitados-nostalgia-y-canciones-ineditas/"
        )
        item = {
            "title": "María León presentó su nueva “Era de Villana” en el Teatro Metropólitan de la CDMX",
            "source": "Infobae",
            "source_url": source_url,
            "url": "https://news.google.com/rss/articles/example?oc=5",
            "date": "2026-11-13",
            "published_at": "2026-11-13T07:53:32Z",
            "local_url": "/noticias/?id=8e02d29b62c66ba3eff6&mes=2026-11",
            "brief": {
                "lead": "Infobae informó que María León presentó su espectáculo en Ciudad de México.",
                "context": "La presentación tuvo lugar en el Teatro Metropólitan.",
                "pending": "No se anuncian fechas futuras en la fuente consultada.",
                "method": "Síntesis editorial basada en la publicación de Infobae.",
            },
        }
        page = render(item, "8e02d29b62c66ba3eff6")
        self.assertIn('href="' + source_url + '"', page)
        self.assertIn("Ver fuente original", page)
        self.assertIn('rel="nofollow noopener noreferrer"', page)
        self.assertNotIn('href="' + item["url"] + '"', page)


    def test_hoy_tamaulipas_original_source_url_is_clickable(self):
        source_url = (
            "https://www.hoytamaulipas.net/notas/607182/"
            "El-Mante-presente-en-la-Asamblea-Nacional-de-Seguridad-Publica-Municipal-2025.html"
        )
        item = {
            "title": "Participa Patty Chio en Primera Asamblea de Seguridad Publica Municipal en CDMX",
            "source": "Hoy Tamaulipas",
            "source_url": source_url,
            "url": "https://news.google.com/rss/articles/example?oc=5",
            "date": "2025-12-10",
            "published_at": "2025-12-11T01:31:04Z",
            "local_url": "/noticias/?id=5a9a1f1ebbab943a2f55&mes=2026-11",
            "brief": {"lead": "La alcaldesa de El Mante participó en la asamblea de seguridad municipal."},
        }
        page = render(item, "5a9a1f1ebbab943a2f55")
        self.assertIn('href="' + source_url + '"', page)
        self.assertIn("Ver fuente original", page)
        self.assertNotIn('href="' + item["url"] + '"', page)

    def test_la_jornada_garbage_uses_verified_direct_source_instead_of_rss(self):
        source_url = (
            "https://www.jornada.com.mx/noticia/2026/11/14/espectaculos/"
            "garbage-reune-a-mas-de-90-mil-personas-en-concierto-en-la-ciudad-de-mexico"
        )
        rss_url = "https://news.google.com/rss/articles/example?oc=5"
        item = {
            "title": "Garbage reúne a más de 90 mil personas durante su concierto en el Zócalo de la CDMX",
            "source": "La Jornada",
            "url": rss_url,
            "date": "2026-11-14",
            "published_at": "2026-11-15T04:54:00Z",
            "local_url": "/noticias/?id=3297b71001da632dcb3e&mes=2026-11",
            "brief": {
                "lead": "La Jornada reportó que el concierto gratuito de Garbage en el Zócalo reunió a más de 90 mil personas.",
                "context": "La SSC desplegó elementos para vigilar el evento.",
                "pending": "Las cifras se atribuyen a las autoridades citadas por La Jornada.",
                "method": "Síntesis editorial basada en La Jornada.",
            },
        }
        page = render(item, "3297b71001da632dcb3e")
        self.assertIn('href="' + source_url + '"', page)
        self.assertIn("Ver fuente original", page)
        self.assertIn('rel="nofollow noopener noreferrer"', page)
        self.assertNotIn('href="' + rss_url + '"', page)

    def test_sociedad_noticias_garbage_uses_verified_direct_source_instead_of_rss(self):
        source_url = (
            "https://sociedad-noticias.com/2026/11/15/"
            "garbage-reune-a-mas-de-90-mil-personas-en-el-zocalo-de-la-cdmx/"
        )
        rss_url = "https://news.google.com/rss/articles/example?oc=5"
        item = {
            "title": "Garbage reúne a más de 90 mil personas en el Zócalo de la Cdmx",
            "source": "Sociedad Noticias",
            "url": rss_url,
            "date": "2026-11-15",
            "published_at": "2026-11-15T06:30:00Z",
            "local_url": "/noticias/?id=effab44940f001e64f19&mes=2026-11",
            "brief": {
                "lead": "Sociedad Noticias reportó más de 90 mil personas en el concierto gratuito de Garbage.",
                "method": "Síntesis editorial basada en Sociedad Noticias.",
            },
        }
        page = render(item, "effab44940f001e64f19")
        self.assertIn('href="' + source_url + '"', page)
        self.assertIn("Ver fuente original", page)
        self.assertIn('rel="nofollow noopener noreferrer"', page)
        self.assertNotIn('href="' + rss_url + '"', page)

    def test_la_razon_garbage_uses_verified_direct_source_instead_of_rss(self):
        source_url = (
            "https://www.razon.com.mx/ciudad/2026/11/15/"
            "asisten-mas-de-90-mil-personas-a-concierto-de-garbage-en-el-zocalo-de-la-cdmx/"
        )
        rss_url = "https://news.google.com/rss/articles/example?oc=5"
        item = {
            "title": "Asisten más de 90 mil personas a concierto de Garbage en el Zócalo de la CDMX",
            "source": "La Razón de México",
            "url": rss_url,
            "date": "2026-11-15",
            "published_at": "2026-11-15T06:19:54Z",
            "local_url": "/noticias/?id=e5a213749a521cf90ee8&mes=2026-11",
        }
        page = render(item, "e5a213749a521cf90ee8")
        self.assertIn('href="' + source_url + '"', page)
        self.assertIn("Ver fuente original", page)
        self.assertIn('rel="nofollow noopener noreferrer"', page)
        self.assertNotIn('href="' + rss_url + '"', page)

    def test_elsol_women_defensive_driving_source_url_is_clickable(self):
        source_url = (
            "https://oem.com.mx/elsoldemexico/metropoli/"
            "ofrecen-taller-gratuito-de-manejo-defensivo-y-preventivo-para-mujeres-en-cdmx-33130686"
        )
        item = {
            "title": "Ofrecen taller gratuito de manejo defensivo y preventivo para mujeres en CDMX",
            "source": "El Sol de México",
            "source_url": source_url,
            "url": "https://news.google.com/rss/articles/example?oc=5",
            "local_url": "/noticias/?id=6538cbdab54691ebcf27&mes=2026-11",
            "date": "2026-11-14",
            "category": "Movilidad",
            "location": "Gustavo A. Madero, Ciudad de México",
            "brief": {
                "lead": "El taller se realizará el 27 de noviembre en Gustavo A. Madero.",
                "context": "Capacitación vial para mujeres.",
                "pending": "El recinto y horario requieren confirmación.",
                "method": "Síntesis basada en el fragmento indexado de El Sol de México.",
            },
        }
        page = render(item, "6538cbdab54691ebcf27")
        self.assertIn('href="' + source_url + '"', page)
        self.assertIn("Ver fuente original", page)

    def test_24_horas_electric_mobility_source_link_and_photo_credit_are_rendered(self):
        source_url = "https://24-horas.mx/cdmx/registro-emplacamiento-vemepe-vep-cdmx-costos-requisitos/"
        photo_url = "https://thumb.wikimedia.org/wikipedia/commons/thumb/5/57/Grin_e-scooter_rider_in_Mexico_City.jpg/1280px-Grin_e-scooter_rider_in_Mexico_City.jpg?utm_campaign=index&utm_content=thumbnail&utm_source=commons.wikimedia.org"
        item = {
            "title": "Placas de motos eléctricas, bicis y scooters en CDMX: ¿cuáles son las reglas y de cuánto es la multa?",
            "source": "24-horas",
            "source_url": source_url,
            "url": "https://news.google.com/rss/articles/example?oc=5",
            "local_url": "/noticias/?id=f321caba525de71a5543&mes=2026-11",
            "date": "2026-11-14",
            "category": "Movilidad",
            "location": "Ciudad de México (sin alcaldía identificada)",
            "brief": {
                "lead": "El periodo de gracia vence el 20 de noviembre de 2026.",
                "context": "Solo VEMEPE requieren placa; VEP reciben DME gratuito.",
                "pending": "Verifica la clasificación en SEMOVI.",
                "method": "Síntesis de 24 Horas contrastada con SEMOVI.",
            },
            "photo": {
                "id": "contexto_grin_escooter_cdmx_2019",
                "kind": "representativa",
                "url": photo_url,
                "category": "Movilidad",
                "topic": "Persona en scooter eléctrico Grin por carril ciclista de CDMX (23/10/2019); foto de archivo, no del trámite de 2026.",
                "author": "Sonia Medina",
                "license": "CC BY 3.0",
                "licenseUrl": "https://creativecommons.org/licenses/by/3.0/",
                "source": "https://commons.wikimedia.org/wiki/File:Grin_e-scooter_rider_in_Mexico_City.jpg",
            },
        }
        page = render(item, "f321caba525de71a5543")
        self.assertIn('href="' + source_url + '"', page)
        self.assertIn("Ver fuente original", page)
        self.assertIn("Sonia Medina", page)
        self.assertIn("CC BY 3.0", page)
        self.assertIn(photo_url.replace("&", "&amp;"), page)

    def test_imer_animal_rights_original_source_url_is_clickable(self):
        source_url = (
            "https://noticias.imer.mx/blog/activistas-y-defensores-de-animales-"
            "marcharon-para-exigir-el-fin-de-la-explotacion-animal-y-promover-el-veganismo-en-cdmx/"
        )
        item = {
            "title": "Defensores de animales exigen el fin de la explotación animal y promueven el veganismo en CDMX",
            "source": "IMER Noticias",
            "source_url": source_url,
            "url": "https://news.google.com/rss/articles/example?oc=5",
            "date": "2026-11-14",
            "local_url": "/noticias/?id=cad284585f539df643d2&mes=2026-11",
            "brief": {
                "lead": "Activistas y organizaciones defensoras de animales marcharon en CDMX.",
                "method": "Síntesis del artículo original de IMER Noticias.",
            },
        }
        page = render(item, "cad284585f539df643d2")
        self.assertIn('href="' + source_url + '"', page)
        self.assertIn("Ver fuente original", page)
        self.assertIn('rel="nofollow noopener noreferrer"', page)
        self.assertNotIn('href="' + item["url"] + '"', page)


    def test_local_photo_keeps_credits(self):
        html = render_photo({"category": "Seguridad", "photo": {
            "url": "/assets/fotos/seguridad.jpg", "kind": "representativa",
            "author": "Autor de prueba", "license": "CC BY 4.0",
            "licenseUrl": "https://creativecommons.org/licenses/by/4.0/"}})
        self.assertIn('src="/assets/fotos/seguridad.jpg"', html)
        self.assertIn("Imagen representativa", html)
        self.assertIn("Autor de prueba", html)
        self.assertIn("CC BY 4.0", html)

    def test_representative_photo_alt_uses_photo_topic_not_article_category(self):
        html = render_photo({"category": "Gobierno", "photo": {
            "url": "https://upload.wikimedia.org/example.jpg",
            "kind": "representativa",
            "topic": "Casa del Centro Histórico de la Ciudad de México (foto de archivo)",
            "author": "Autor de prueba",
            "license": "CC BY-SA 4.0",
            "licenseUrl": "https://creativecommons.org/licenses/by-sa/4.0/",
        }})
        self.assertIn(
            'alt="Casa del Centro Histórico de la Ciudad de México (foto de archivo)"',
            html,
        )
        self.assertNotIn('alt="Imagen representativa de Gobierno"', html)

    def test_sensitive_story_hides_generic_representative_photo(self):
        item = {
            "title": "Caso Vadhir Derbez: Fiscalía CDMX tendría ADN relacionado con denuncia por violación",
            "category": "CDMX",
            "local_url": "/noticias/?id=15c774326c62e64d619e&mes=2026-11",
            "photo": {
                "url": "/assets/fotos/archivo_seguridad_003.jpg",
                "kind": "representativa",
                "author": "Gobierno de la Ciudad de México",
                "license": "CC BY 4.0",
                "licenseUrl": "https://creativecommons.org/licenses/by/4.0",
                "source": "https://commons.wikimedia.org/wiki/File:Adquisici%C3%B3n_patrullas_para_la_Polic%C3%ADa_02.jpg",
            },
        }
        self.assertEqual(render_photo(item), "")
        page = render(item, "15c774326c62e64d619e")
        self.assertIn("Sin fotografía verificada del hecho", page)
        self.assertNotIn('src="/assets/fotos/archivo_seguridad_003.jpg"', page)

    def test_animal_cruelty_story_hides_generic_animal_photo(self):
        item = {
            "title": "Detienen a acusado de maltrato animal en Tlalpan",
            "category": "Seguridad",
            "local_url": "/noticias/?id=50c470b90270a39d9138&mes=2026-11",
            "photo": {
                "url": "https://thumb.wikimedia.org/wikipedia/commons/thumb/4/42/Animales_Bosque_de_Tlalpan_07.JPG/960px-Animales_Bosque_de_Tlalpan_07.JPG",
                "kind": "representativa",
                "author": "Inakiherrasti",
                "license": "CC BY-SA 4.0",
                "licenseUrl": "https://creativecommons.org/licenses/by-sa/4.0",
                "source": "https://commons.wikimedia.org/wiki/File:Animales_Bosque_de_Tlalpan_07.JPG",
            },
        }
        self.assertEqual(render_photo(item), "")
        page = render(item, "50c470b90270a39d9138")
        self.assertIn("Sin fotografía verificada del hecho", page)
        self.assertNotIn("Animales_Bosque_de_Tlalpan_07", page)


    def test_sensitive_story_allows_only_verified_event_photo(self):
        item = {
            "title": "Denuncia por violación: Fiscalía CDMX investiga",
            "photo": {
                "url": "/assets/fotos/archivo_seguridad_003.jpg",
                "kind": "hecho",
                "verified": True,
                "evidence_url": "https://example.org/evidence",
                "author": "Autor verificado",
                "license": "CC BY 4.0",
            },
        }
        self.assertIn('src="/assets/fotos/archivo_seguridad_003.jpg"', render_photo(item))

    def test_borough_photo(self):
        self.assertIn('src="/assets/alcaldias/azcapotzalco.jpg"',
                      render_photo({"photo": {"url": "/assets/alcaldias/azcapotzalco.jpg"}}))

    def test_https_remote_photo(self):
        self.assertIn('src="https://example.org/image.jpg"',
                      render_photo({"photo": {"url": "https://example.org/image.jpg"}}))

    def test_unsafe_local_urls_rejected(self):
        for url in ("//example.org/x.jpg", "/assets/fotos/../secret.txt",
                    "/assets/fotos/x.jpg?redirect=1", "javascript:alert(1)",
                    "/other/x.jpg"):
            with self.subTest(url=url):
                self.assertEqual(render_photo({"photo": {"url": url}}), "")


    def test_dynamic_article_source_allowlist_includes_curated_publishers(self):
        script = (
            Path(__file__).resolve().parents[1] / "assets" / "noticias-locales.js"
        ).read_text(encoding="utf-8")
        self.assertIn("TRUSTED_SOURCE_HOSTS.has(u.hostname)", script)
        for host in (
            "elpais.com",
            "www.elimparcial.com",
            "www.sopitas.com",
            "www.am.com.mx",
            "www.yucatan.com.mx",
            "www.infobae.com",
            "www.somoselmedio.com",
            "elcongresista.mx",
            "ahoranoticias.com.mx",
            "oem.com.mx",
            "sociedad-noticias.com",
            "www.nmas.com.mx",
            "24-horas.mx",
            "capital-cdmx.org",
            "diariobasta.com",
            "es-us.noticias.yahoo.com",
            "noticias.imer.mx",
            "www.billboard.com",
            "www.jornada.com.mx",
            "www.posta.com.mx",
            "www.radioformula.com.mx",
            "www.razon.com.mx",
            "www.sdpnoticias.com",
            "www.tvazteca.com",
        ):
            with self.subTest(host=host):
                self.assertIn("'" + host + "'", script)
        self.assertIn(
            "const VERIFIED_SOURCE_HOSTS = new Set(['comova.mx','mayacomunicacion.com.mx','www.elgrafico.mx']);",
            script,
        )

    def test_current_curated_source_urls_are_clickable_in_static_article_pages(self):
        sources = (
            "https://capital-cdmx.org/colonias-mas-denuncias-cuajimalpa-de-morelos-capital-ayuda-2026/",
            "https://capital-cdmx.org/colonias-mas-denuncias-venustiano-carranza-capital-ayuda-2026/",
            "https://elpais.com/mexico/2026-11-16/el-desfile-de-la-revolucion-en-ciudad-de-mexico-horario-ruta-y-contingentes.html",
            "https://www.tvazteca.com/aztecanoticias/desfile-del-20-de-noviembre-en-cdmx-ruta-horarios-y-alternativas-viales-por-cortes-a-la-circulacion/?outputType=amp",
            "https://www.sopitas.com/noticias/discriminacion-cdmx-copred-edis-2026/",
        )
        for index, source_url in enumerate(sources, start=1):
            with self.subTest(source_url=source_url):
                rss_url = "https://news.google.com/rss/articles/example?oc=5"
                item = {
                    "title": "Noticia local con fuente original",
                    "source": "Medio identificado",
                    "source_url": source_url,
                    "url": rss_url,
                    "date": "2026-11-16",
                    "local_url": f"/noticias/?id={index:020x}&mes=2026-11",
                    "brief": {
                        "lead": "Resumen atribuido al medio.",
                        "method": "Síntesis editorial basada en la publicación original.",
                    },
                }
                page = render(item, f"{index:020x}")
                self.assertIn('href="' + source_url + '"', page)
                self.assertIn("Ver fuente original", page)
                self.assertNotIn('href="' + rss_url + '"', page)

    def test_unlisted_lookalike_source_host_remains_rejected(self):
        source_url = "https://capital-cdmx.org.evil.example/noticia"
        item = {
            "title": "Noticia local con fuente no autorizada",
            "source": "Fuente no verificada",
            "source_url": source_url,
            "url": "https://news.google.com/rss/articles/example?oc=5",
            "date": "2026-11-16",
            "local_url": "/noticias/?id=00000000000000000099&mes=2026-11",
            "brief": {"lead": "Resumen atribuido al titular."},
        }
        page = render(item, "00000000000000000099")
        self.assertNotIn('href="' + source_url + '"', page)
        self.assertNotIn("Ver fuente original", page)



class EditorialPhotoOverrideTests(unittest.TestCase):
    def test_azcapotzalco_budget_article_uses_civic_plaza_not_carnival(self):
        item = {
            "title": "Nancy Núñez pide casi 3 mil millones de pesos para Azcapotzalco en 2027",
            "source": "La Prensa",
            "date": "2026-11-17",
            "local_url": "/noticias/?id=534d17e7c38cfd83b7a1&mes=2026-11",
            "photo": {
                "id": "commons_88470074",
                "kind": "representativa",
                "url": "https://thumb.wikimedia.org/wikipedia/commons/thumb/1/11/Carnaval_de_Azcapotzalco%2C_Ciudad_de_M%C3%A9xico_-_Marzo_2020_II.jpg/960px-Carnaval_de_Azcapotzalco%2C_Ciudad_de_M%C3%A9xico_-_Marzo_2020_II.jpg",
                "author": "Juan Carlos Fonseca Mata",
                "license": "CC BY-SA 4.0",
                "licenseUrl": "https://creativecommons.org/licenses/by-sa/4.0",
                "source": "https://commons.wikimedia.org/wiki/File:Carnaval_de_Azcapotzalco,_Ciudad_de_M%C3%A9xico_-_Marzo_2020_II.jpg",
            },
        }
        rendered = render_photo(item)
        self.assertIn("Azcapotzalco_-_Panor", rendered)
        self.assertIn("ProtoplasmaKid", rendered)
        self.assertIn("CC BY-SA 4.0", rendered)
        self.assertNotIn("Carnaval_de_Azcapotzalco", rendered)

        local_script = (Path(__file__).resolve().parents[1] /
                        "assets/noticias-locales.js").read_text(encoding="utf-8")
        self.assertIn("534d17e7c38cfd83b7a1", local_script)
        self.assertIn("Azcapotzalco_-_Panor", local_script)

        local_index = (Path(__file__).resolve().parents[1] /
                       "noticias/index.html").read_text(encoding="utf-8")
        self.assertIn("noticias-locales.js?v=20261118-azcapotzalco-budget-photo-0332", local_index)

    def test_context_catalog_has_correct_azcapotzalco_and_theatre_credits(self):
        root = Path(__file__).resolve().parents[1]
        catalog = json.loads(
            (root / "assets/fotos/contexto-tematico.json").read_text(encoding="utf-8")
        )
        plaza = next(
            p for p in catalog["photos"]
            if p["id"] == "contexto_azcapotzalco_plaza_civica_2011"
        )
        self.assertEqual(plaza["author"], "ProtoplasmaKid")
        self.assertEqual(plaza["license"], "CC BY-SA 4.0")
        self.assertIn("edificio delegacional", plaza["topic"])
        self.assertIn("no evidencia del presupuesto 2027", plaza["topic"])

        theatre = next(
            p for p in catalog["photos"]
            if p["id"] == "contexto_teatro_metropolitan_2019"
        )
        self.assertIn("no muestra el concierto de Golden Ganga", theatre["topic"])
        self.assertIn("cartelera del 18 de noviembre de 2026", theatre["topic"])


class EditorialArchiveSyncTests(unittest.TestCase):
    def test_archive_photo_override_matches_the_generated_azcapotzalco_article(self):
        azcapotzalco = {
            "local_url": "/noticias/?id=534d17e7c38cfd83b7a1&mes=2026-11",
            "photo": {
                "id": "commons_88470074",
                "url": "https://thumb.wikimedia.org/old-carnival-photo.jpg",
                "author": "Juan Carlos Fonseca Mata",
                "license": "CC BY-SA 4.0",
            },
        }
        unrelated = {
            "local_url": "/noticias/?id=00000000000000000001&mes=2026-11",
            "photo": {"id": "keep-this-photo", "author": "Autor original"},
        }
        records = [azcapotzalco, unrelated]
        changed = apply_editorial_record_overrides(records)
        self.assertEqual(changed, 1)
        self.assertEqual(
            records[0]["photo"]["id"],
            "contexto_azcapotzalco_plaza_civica_2011",
        )
        self.assertIn("Azcapotzalco_-_Panor", records[0]["photo"]["url"])
        self.assertEqual(records[1]["photo"]["id"], "keep-this-photo")
        self.assertEqual(records[1]["photo"]["author"], "Autor original")

    def test_courier_archive_record_has_verified_mobility_summary_and_direct_source(self):
        source_url = "https://sociedad-noticias.com/2026/11/18/motociclistas-repartidores-acuerdan-dialogo-con-autoridades-de-la-cdmx/"
        record = {
            "title": "Motociclistas repartidores acuerdan diálogo con autoridades de la Cdmx",
            "source": "Sociedad Noticias",
            "date": "2026-11-18",
            "local_url": "/noticias/?id=76ea8af5f775cd14991b&mes=2026-11",
            "category": "Seguridad",
            "description": "Resumen anterior basado solo en el titular.",
            "brief": {"lead": "Resumen anterior basado solo en el titular."},
            "photo": {
                "id": "contexto_repartidores_motocicleta_cdmx",
                "url": "https://thumb.wikimedia.org/example.jpg",
                "author": "Palacio Postal",
                "license": "CC BY-SA 4.0",
                "licenseUrl": "https://creativecommons.org/licenses/by-sa/4.0",
                "source": "https://commons.wikimedia.org/wiki/File:Carteros_en_motocicleta_del_Servicio_Postal_Mexicano,_2013.jpg",
                "kind": "representativa",
            },
        }
        records = [record]
        changed = apply_editorial_record_overrides(records)
        self.assertEqual(changed, 1)
        self.assertEqual(record["category"], "Movilidad")
        self.assertEqual(record["source_url"], source_url)
        self.assertIn("Semovi", record["brief"]["lead"])
        self.assertIn("próxima reunión", record["brief"]["pending"])
        self.assertEqual(record["photo"]["author"], "Palacio de Correos de Mexico")
        page = render(record, "76ea8af5f775cd14991b")
        self.assertIn('href="' + source_url + '"', page)
        self.assertNotIn('href="' + record["url"] + '"', page) if record.get("url") else None

    def test_current_context_catalog_and_feed_use_commons_photographer_credit(self):
        root = Path(__file__).resolve().parents[1]
        photo_id = "contexto_repartidores_motocicleta_cdmx"
        context = json.loads(
            (root / "assets/fotos/contexto-tematico.json").read_text(encoding="utf-8")
        )
        photo = next(item for item in context["photos"] if item["id"] == photo_id)
        self.assertEqual(photo["author"], "Palacio de Correos de Mexico")
        self.assertIn("no del hecho actual", photo["topic"])
        self.assertEqual(photo["license"], "CC BY-SA 4.0")
        self.assertEqual(
            photo["source"],
            "https://commons.wikimedia.org/wiki/File:Carteros_en_motocicleta_del_Servicio_Postal_Mexicano,_2013.jpg",
        )
        feed = json.loads((root / "news.json").read_text(encoding="utf-8"))
        articles = [
            item for item in feed["articles"]
            if item.get("photo", {}).get("id") == photo_id
        ]
        self.assertTrue(articles, "El feed debe conservar al menos una noticia que use la foto representativa")
        for article in articles:
            # El feed puede asociar esta foto a noticias distintas de la nota de
            # Sociedad Noticias archivada; no se debe exigirles su source_url ni
            # el resumen de Semovi por compartir únicamente la misma imagen.
            self.assertEqual(article["category"], "Movilidad")
            self.assertEqual(article["photo"]["author"], photo["author"])
            self.assertEqual(article["photo"]["license"], photo["license"])
            self.assertIn("no del hecho actual", article["photo"]["topic"])


if __name__ == "__main__":
    unittest.main()
