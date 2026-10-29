"""Regresiones de la etapa 5: moderación avanzada y auditoría privada.

Son pruebas estáticas. Para validar permisos efectivos hay que publicar
firestore.rules y probar con una cuenta moderadora y otra sin permisos.
"""
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def read(path):
    return (ROOT / path).read_text(encoding="utf-8")


class AdvancedModerationTests(unittest.TestCase):
    def test_existing_panel_keeps_auth_and_adds_filters(self):
        page = read("moderacion/index.html")
        for item in (
            'id="identity-name"', 'id="identity-photo"',
            'id="identity-role"', 'id="login"', 'id="logout"',
            'id="private"', 'id="reports"', 'id="reports-reason"',
            'id="reports-search"', 'id="reports-sort"',
            'id="history"', 'id="history-status"',
            'id="history-action"', 'id="history-search"',
            'id="audit-state"', 'id="stat-pending"',
            'id="stat-unique"', 'id="stat-repeated"',
            'moderacion-avanzada.css', 'moderacion-avanzada.js',
        ):
            self.assertIn(item, page)
        self.assertIn('content="noindex,nofollow"', page)
        self.assertIn('id="private" hidden', page)

    def test_role_is_enforced_in_frontend(self):
        script = read("assets/moderacion-avanzada.js")
        for required in (
            "getIdTokenResult(viewer,true)",
            "token.claims.moderator===true",
            "privateArea.hidden=false",
            "auth.currentUser===viewer",
            "Acceso denegado:",
            "actorUid:viewer.uid",
            "getRedirectResult(auth)",
        ):
            self.assertIn(required, script)
        self.assertNotIn("setCustomUserClaims", script)
        self.assertNotIn("serviceAccount", script)

    def test_audit_writes_are_atomic_and_explicit(self):
        script = read("assets/moderacion-avanzada.js")
        for required in (
            "runTransaction(db,async tx=>",
            "tx.get(report.ref)",
            "tx.get(postRef)",
            "tx.set(auditRef,",
            "tx.delete(postRef)",
            "tx.delete(report.ref)",
            "createdAt:serverTimestamp()",
            "reportSort.value==='most'",
            "No hay reportes que coincidan",
            "histAction.value",
            "historyRefresh.addEventListener",
            "historial; esta decisión no quedará registrada",
        ):
            self.assertIn(required, script)
        self.assertNotIn("innerHTML", script)

    def test_firestorm_rules_keep_private_immutable_history(self):
        rules = read("firebase/firestore.rules")
        for required in (
            "match /community/main/moderationActions/{actionId}",
            "allow read: if moderator();",
            "allow create: if validModerationAction(actionId);",
            "allow update, delete: if false;",
            "data.actorUid == request.auth.uid",
            "data.createdAt == request.time",
            "!existsAfter(moderationReportPath(data.reportId))",
            "!existsAfter(moderationCommentPath(data.commentId))",
            "get(moderationReportPath(data.reportId)).data.reason == data.reason",
            "match /community/main/reports/{reportId}",
            "allow read, delete: if moderator()",
            "match /community/main/votes/{commentId}/users/{voterId}",
        ):
            self.assertIn(required, rules)

    def test_disclosure_and_documentation(self):
        privacy = read("privacidad.html")
        docs = read("firebase/README.md")
        self.assertIn("Historial interno de moderación", privacy)
        self.assertIn("moderationActions", docs)
        self.assertIn("solo las decisiones hechas desde este panel", docs)
        self.assertIn("Firestore Database", docs)


if __name__ == "__main__":
    unittest.main()
