"""Regresiones de votos útiles en Mi comunidad.

Estas pruebas verifican la estructura de la integración. Las comprobaciones
de permisos efectivos requieren publicar las reglas y probar Firestore.
"""
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def read(path):
    return (ROOT / path).read_text(encoding="utf-8")


class CommunityVotingTests(unittest.TestCase):
    def test_votes_are_atomic_and_one_per_account(self):
        rules = read("firebase/firestore.rules")
        for expected in (
            "match /community/main/votes/{commentId}/users/{voterId}",
            "match /community/main/voteTotals/{commentId}",
            "voterId == request.auth.uid",
            "allow list: if false",
            "getAfter(voteTotalPath(commentId)).data.count",
            "existsAfter(myVotePath(commentId))",
            "!existsAfter(myVotePath(commentId))",
            "allow delete: if false",
            "validVoteCount()",
            "validVotedComment(commentId)",
        ):
            self.assertIn(expected, rules)
        self.assertIn("request.resource.data.count >= 0", rules)
        self.assertIn("request.resource.data.createdAt == request.time", rules)

    def test_forum_uses_transaction_and_does_not_fake_votes(self):
        script = read("assets/comments.js")
        for expected in (
            "fs.runTransaction(db,async tx=>",
            "fs.getDoc(refs.total)",
            "tx.delete(personal)",
            "tx.set(personal,{createdAt:fs.serverTimestamp()})",
            "tx.set(total,{count})",
            "function usefulVoteButton(topic)",
            "function updateBestAnswers()",
            "function showVotingUnavailable()",
            "voteObserver?.disconnect()",
        ):
            self.assertIn(expected, script)
        self.assertNotIn("setCustomUserClaims", script)

    def test_styles_and_disclosure_are_present(self):
        forum = read("comunidad/index.html")
        self.assertIn("assets/forum-votes.css", forum)
        self.assertIn("id=\"forum-voting-note\"", forum)
        self.assertRegex(forum, r"comments\\.js\\?v=[a-zA-Z0-9_-]+")
        self.assertIn("las respuestas más votadas", forum.lower())
        css = read("assets/forum-votes.css")
        self.assertIn(".forum-best-answer", css)
        privacy = read("privacidad.html")
        self.assertIn("Votos útiles de Mi comunidad", privacy)
        self.assertIn("no se borran automáticamente", privacy)

    def test_reports_and_moderation_rules_preserved(self):
        rules = read("firebase/firestore.rules")
        self.assertIn("match /community/main/reports/{reportId}", rules)
        self.assertIn("allow read, delete: if moderator()", rules)
        self.assertIn("allow create: if validComment()", rules)
        self.assertIn("match /communityBans/{uid}", rules)


if __name__ == "__main__":
    unittest.main()
