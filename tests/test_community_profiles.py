"""Regresiones de perfiles públicos de Mi comunidad.

No requieren credenciales, ni modifican reglas de Firebase.
La comprobación de lectura real requiere abrir el perfil publicado.
"""
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def read(path):
    return (ROOT / path).read_text(encoding="utf-8")


class PublicProfilesTests(unittest.TestCase):
    def test_profile_page_has_public_accessible_elements(self):
        page = read("perfiles/index.html")
        for expected in (
            'id="profile-name"', 'id="profile-avatar"',
            'id="profile-list"', 'id="profile-filter"',
            'id="profile-more"', 'id="profile-question-count"',
            'id="profile-reply-count"', 'id="profile-total-count"',
            'id="profile-status"', 'name="robots"',
            '/assets/community-profiles.js', '/assets/community-profiles.css',
        ):
            self.assertIn(expected, page)
        self.assertIn('content="noindex,follow"', page)

    def test_profiles_only_query_public_forum_messages(self):
        script = read("assets/community-profiles.js")
        for expected in (
            "fs.collection(db,'community','main','comments')",
            "fs.where('uid','==',targetUid)",
            "fs.limit(PAGE_SIZE)", "fs.startAfter(cursor)",
            "fs.getDocs(", "new URLSearchParams(location.search)",
            "questionPrefix=", "replyExpression=",
            "textContent=content", "referrerPolicy='no-referrer'",
            "authApi.onAuthStateChanged", "profile-list",
        ):
            self.assertIn(expected, script)
        self.assertNotIn("innerHTML", script)
        self.assertNotIn("setDoc(", script)
        self.assertNotIn("addDoc(", script)
        self.assertNotIn("reports", script)
        self.assertNotIn("getUsers", script)

    def test_forum_links_author_and_session_account(self):
        script = read("assets/comments.js")
        page = read("comunidad/index.html")
        self.assertIn("inner.href='/perfiles/?uid='+encodeURIComponent(uid)", script)
        self.assertIn("myProfile.href=person?'/perfiles/?uid='+encodeURIComponent(person.uid)", script)
        self.assertIn("id=\"community-my-profile\"", page)
        self.assertIn("comments.js?v=11-perfiles", page)
        self.assertIn("/assets/community-profiles.css", page)

    def test_no_security_rule_change_necessary(self):
        rules = read("firebase/firestore.rules")
        self.assertIn("match /community/main/comments/{commentId}", rules)
        self.assertIn("allow read: if true;", rules)
        self.assertIn("allow read, delete: if moderator()", rules)
        self.assertIn("match /community/main/votes/{commentId}/users/{voterId}", rules)

    def test_privacy_discloses_public_profile_and_uid(self):
        privacy = read("privacidad.html")
        self.assertIn("Perfiles públicos de Mi comunidad", privacy)
        self.assertIn("UID", privacy)
        self.assertIn("no muestra en el perfil su correo", privacy)


if __name__ == "__main__":
    unittest.main()
