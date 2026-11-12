#!/usr/bin/env python3
"""Validate public SEO documents without changing the site."""
from html.parser import HTMLParser
from urllib.error import HTTPError
from urllib.request import Request, urlopen
from urllib.parse import urlparse
import json
import xml.etree.ElementTree as ET

BASE = "https://cdmx-al-memento.pages.dev"
class Links(HTMLParser):
    def __init__(self):
        super().__init__()
        self.hrefs = []
    def handle_starttag(self, tag, attrs):
        if tag == "a":
            href = dict(attrs).get("href", "")
            if href.startswith("/articulos/"):
                self.hrefs.append(href)

def fetch(path):
    req = Request(BASE + path, headers={"User-Agent": "CDMX-SEO-HealthCheck/1.0"})
    with urlopen(req, timeout=25) as response:
        data = response.read()
        if response.status != 200:
            raise ValueError(f"{path}: HTTP {response.status}")
        return data


def check_community():
    html = fetch("/comunidad/").decode("utf-8")
    required = {
        'id="cdmx-comments"': "contenedor de comentarios",
        'id="forum-search"': "buscador del foro",
        'id="forum-question-title"': "editor de preguntas",
        "comments-config.js": "configuración pública de Firebase",
        "comments.js": "cliente de comentarios",
    }
    missing = [label for marker, label in required.items() if marker not in html]
    if missing:
        raise ValueError("/comunidad/: faltan elementos: " + ", ".join(missing))
    print("OK /comunidad/: foro, comentarios y scripts de acceso presentes")


def check_engagement():
    path = (
        "/api/engagement?article="
        "%2Fnoticias%2F%3Fid%3Db37ba45fa2fa424b73bd%26mes%3D2026-11"
    )
    req = Request(BASE + path, headers={"User-Agent": "CDMX-SEO-HealthCheck/1.0"})
    try:
        with urlopen(req, timeout=25) as response:
            payload = json.loads(response.read().decode("utf-8"))
            if response.status != 200:
                raise ValueError(f"/api/engagement: HTTP {response.status}")
            if not all(key in payload for key in ("visitors", "likes", "liked")):
                raise ValueError("/api/engagement: faltan contadores en la respuesta")
            print("OK /api/engagement: visitantes y Me gusta responden")
    except HTTPError as exc:
        if exc.code == 503:
            print(
                "::warning:: /api/engagement devolvió HTTP 503; LIKES_DB o sus tablas "
                "no están disponibles y los contadores reales no pudieron verificarse."
            )
        else:
            raise

def main():
    for path in ("/", "/archivo/"):
        parser = Links()
        parser.feed(fetch(path).decode("utf-8"))
        if not parser.hrefs:
            raise ValueError(f"{path}: no static article links found")
        print(f"OK {path}: {len(parser.hrefs)} article links")
    for path in ("/sitemap.xml", "/sitemap-articulos.xml"):
        root = ET.fromstring(fetch(path))
        if not root.tag.endswith("urlset"):
            raise ValueError(f"{path}: XML root is not urlset")
        locs = [x.text for x in root.iter() if x.tag.endswith("loc")]
        if not locs or not all(u and urlparse(u).netloc == urlparse(BASE).netloc for u in locs):
            raise ValueError(f"{path}: missing or invalid URLs")
        print(f"OK {path}: valid XML with {len(locs)} URLs")
    check_community()
    check_engagement()
    print("Public SEO content checks passed")

if __name__ == "__main__":
    main()
