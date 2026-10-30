#!/usr/bin/env python3
"""Validate public SEO documents without changing the site."""
from html.parser import HTMLParser
from urllib.request import Request, urlopen
from urllib.parse import urlparse
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
    print("Public SEO content checks passed")

if __name__ == "__main__":
    main()
