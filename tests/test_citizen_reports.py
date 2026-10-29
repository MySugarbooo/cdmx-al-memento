"""Etapa 9: revisión de interfaz y aislamiento de datos privados.

Pruebas de regresión estáticas; NO prueban la publicación de reglas activas,
que solo se puede verificar tras publicarlas en Firebase y usar cuentas reales.
"""
from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parents[1]


def file(name):
    return (ROOT / name).read_text(encoding="utf-8")


class CitizenReportTests(unittest.TestCase):
    def test_public_page_has_form_and_submission_notice(self):
        html = file("reportes-ciudadanos/index.html")
        for expected in [
            'id="citizen-public-list"', 'id="citizen-public-status"',
            'id="citizen-login"', 'id="citizen-logout"',
            'id="citizen-form" hidden', 'id="citizen-my-list"',
            'id="citizen-moderator" class="citizen-panel citizen-moderator" hidden',
            'id="citizen-mod-list"', 'id="citizen-send-status"',
            'id="citizen-consent"', 'id="citizen-description"',
            'id="citizen-colonia"', 'id="citizen-borough"',
            '/assets/reportes-ciudadanos.css?v=1',
            '/assets/reportes-ciudadanos.js?v=1',
            '/assets/comments-config.js?v=1',
            'https://atencionciudadana.cdmx.gob.mx/',
        ]:
            with self.subTest(expected=expected):
                self.assertIn(expected, html)
        self.assertIn('no genera un folio SUAC', html)
        self.assertIn('No compartas domicilios particulares', html)
        self.assertIn('Emergencias: 911', html)
        self.assertIn('content="index,follow"', html)

    def test_auth_and_pending_are_required(self):
        client = file("assets/reportes-ciudadanos.js")
        for text in [
            'getIdTokenResult(person,true)',
            'token.claims.moderator===true',
            'new firebase.authMod.GoogleAuthProvider()',
            'fs.serverTimestamp()', "status:'pending'",
            "fs.collection(firebase.db,'citizenReports')",
            "fs.where('uid','==',person.uid)",
            "fs.collection(firebase.db,'citizenReportsPublic')",
            "moderator=false",
            "submitBusy=true;submitBtn.disabled=true",
            "if(!ready||!person||submitBusy)return",
            "const batch=fs.writeBatch(firebase.db)",
            "batch.update(privateRef,{status:next",
            "batch.set(publicRef,{",
            "batch.update(publicRef,{status:'closed'",
            "batch.delete(publicRef)",
            'No se pudo guardar el reporte',
        ]:
            with self.subTest(text=text):
                self.assertIn(text, client)
        self.assertNotIn('innerHTML', client)
        self.assertNotIn('eval(', client)
        self.assertNotIn('setCustomUserClaims', client)
        self.assertNotIn('getUserByEmail', client)
        self.assertNotIn('photoURL:', client)
        public_projection = client.split('batch.set(publicRef,{', 1)[1].split('});', 1)[0]
        for excluded in ['uid:', 'email:', 'name:', 'phone:', 'photoURL:']:
            self.assertNotIn(excluded, public_projection)

    def test_rules_private_and_public_separated(self):
        rules = file("firebase/firestore.rules")
        for expected in [
            "match /citizenReports/{reportId}",
            "match /citizenReportsPublic/{reportId}",
            "allow create: if validCitizenSubmission(reportId)",
            "allow update: if validCitizenModeration(reportId)",
            "getAfter(citizenPublicPath(reportId)).data",
            "matchingCitizenPublic(",
            "next.diff(previous).affectedKeys().hasOnly([",
            "allow create: if moderator()",
            "allow update: if moderator()",
            "allow delete: if moderator()",
            "citizenBorough(data.borough)",
            "citizenCategory(data.category)",
            "data.status == 'pending'",
            "data.moderatedBy == ''",
            "data.createdAt == request.time",
            "data.updatedAt == request.time",
        ]:
            with self.subTest(text=expected):
                self.assertIn(expected, rules)
        public_rules = rules.split("match /citizenReportsPublic/{reportId}", 1)[1].split(
            "match /communityBans/{uid}", 1
        )[0]
        self.assertNotIn("allow write: if true", public_rules)
        self.assertNotIn("allow create: if signedIn()", public_rules)
        self.assertIn("allow read: if true", public_rules)
        self.assertIn("getAfter(citizenPrivatePath(reportId)).data.status", public_rules)
        private_rules = rules.split("match /citizenReports/{reportId}", 1)[1].split(
            "match /citizenReportsPublic/{reportId}", 1
        )[0]
        self.assertIn("resource.data.uid == request.auth.uid", private_rules)
        self.assertIn("if moderator()", private_rules)

    def test_existing_community_rules_untouched(self):
        rules = file("firebase/firestore.rules")
        for existing in [
            "match /community/main/comments/{commentId}",
            "match /community/main/votes/{commentId}/users/{voterId}",
            "match /community/main/voteTotals/{commentId}",
            "match /community/main/reports/{reportId}",
            "match /community/main/moderationActions/{actionId}",
            "request.auth.token.get('moderator', false) == true",
        ]:
            self.assertIn(existing, rules)

    def test_navigation_privacy_and_documentation(self):
        for path in [
            "index.html", "comunidad/index.html", "servicios/index.html",
            "moderacion/index.html",
        ]:
            self.assertIn('href="/reportes-ciudadanos/', file(path))
        self.assertIn('"reportes-ciudadanos/"', file("update_news.py"))
        self.assertIn(
            "https://cdmx-al-memento.pages.dev/reportes-ciudadanos/</loc>",
            file("sitemap.xml"),
        )
        self.assertIn(
            "/reportes-ciudadanos/\n  Cache-Control: no-cache, must-revalidate",
            file("_headers"),
        )
        privacy = file("privacidad.html")
        self.assertIn("Reportes ciudadanos por colonia", privacy)
        self.assertIn("sin el UID, nombre, correo ni foto del autor", privacy)
        self.assertIn("no genera folios gubernamentales", privacy)
        docs = file("firebase/README.md")
        self.assertIn("Etapa 9: reportes ciudadanos por colonia", docs)
        self.assertIn("publicar las reglas completas", docs)
        self.assertIn("Firebase App Check", docs)

    def test_ci_checks_scripts(self):
        workflow = file(".github/workflows/news.yml")
        self.assertIn("'tests/test_citizen_reports.py'", workflow)
        self.assertIn("node --check assets/reportes-ciudadanos.js", workflow)
        self.assertIn("node tests/test_citizen_reports.mjs", workflow)


if __name__ == "__main__":
    unittest.main()
