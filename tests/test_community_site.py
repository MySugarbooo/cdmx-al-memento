"""Regresiones que cubren seguridad, privacidad y descubrimiento público del foro."""
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
def read(path):
    return (ROOT/path).read_text(encoding="utf-8")

class CommunitySiteTests(unittest.TestCase):
    def test_privacy_policy_discloses_firebase_accounts_and_public_profile(self):
        policy=read("privacidad.html")
        self.assertNotIn("no ofrece cuentas de usuario ni formularios propios",policy)
        for text in ("Firebase Authentication", "Cloud Firestore", "fotografía de perfil", "reportes no son públicos", "eliminar sus propias publicaciones"):
            self.assertIn(text.lower(),policy.lower())

    def test_sitemap_lists_forum_and_sixteen_borough_pages(self):
        sitemap=read("sitemap.xml")
        self.assertIn("https://cdmx-al-memento.pages.dev/comunidad/</loc>",sitemap)
        boroughs=sorted(p.name for p in (ROOT/"alcaldias").iterdir() if p.is_dir() and (p/"index.html").is_file())
        self.assertEqual(len(boroughs),16)
        for slug in boroughs:
            self.assertIn("https://cdmx-al-memento.pages.dev/alcaldias/"+slug+"/</loc>",sitemap)
        update=read("update_news.py")
        self.assertIn('"comunidad/"',update)
        self.assertIn('"alcaldias/" + p.name + "/"',update)

    def test_cache_headers_cover_dynamic_public_page_html(self):
        headers=read("_headers")
        for path in ("/comunidad/", "/alcaldias/", "/alcaldias/*", "/noticias/", "/archivo/"):
            self.assertIn(path+"\n  Cache-Control: no-cache, must-revalidate",headers)

    def test_moderation_requires_admin_claim_and_never_public_mail(self):
        rules=read("firebase/firestore.rules")
        client=read("assets/comments.js")
        admin=read("firebase/asignar-moderador.mjs")
        self.assertIn("request.auth.token.get('moderator', false) == true",rules)
        self.assertIn("allow read, delete: if moderator()",rules)
        self.assertIn("result.claims.moderator===true",client)
        self.assertIn("admin.setCustomUserClaims",admin.replace("auth.setCustomUserClaims","admin.setCustomUserClaims"))
        self.assertIn("user.providerData.some(provider=>provider.providerId==='google.com')",admin)
        self.assertIn("if(!apply)",admin)
        self.assertNotIn("setCustomUserClaims",client)
        self.assertNotIn("SERVICE_ACCOUNT_PRIVATE_KEY",client)

if __name__ == "__main__":
    unittest.main()
