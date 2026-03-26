from django.test import TestCase

from apps.matching.algorithm import MatchingAlgorithm
from apps.matching.models import Match, Swipe
from apps.users.models import User


def make_user(email, username, genre_prefs=None, mood=""):
    user = User.objects.create_user(
        username=username,
        email=email,
        password="testpass123",
        first_name="Test",
        last_name="User",
    )
    user.profile.genre_preferences = genre_prefs or {}
    user.profile.mood = mood
    user.profile.save()
    return user


# ---------------------------------------------------------------------------
# MatchingAlgorithm — pure logic (no DB)
# ---------------------------------------------------------------------------

class TestGenreSimilarity(TestCase):
    def setUp(self):
        self.algo = MatchingAlgorithm()

    def test_identical_preferences(self):
        score = self.algo.calculate_genre_similarity(
            {"action": 8, "drama": 5},
            {"action": 8, "drama": 5},
        )
        self.assertAlmostEqual(score, 100.0, places=1)

    def test_similar_preferences(self):
        score = self.algo.calculate_genre_similarity(
            {"action": 8},
            {"action": 7},
        )
        self.assertGreater(score, 90.0)

    def test_orthogonal_preferences(self):
        score = self.algo.calculate_genre_similarity(
            {"action": 8},
            {"drama": 5},
        )
        self.assertEqual(score, 0.0)

    def test_empty_first(self):
        score = self.algo.calculate_genre_similarity({}, {"action": 8})
        self.assertEqual(score, 0.0)

    def test_empty_both(self):
        score = self.algo.calculate_genre_similarity({}, {})
        self.assertEqual(score, 0.0)

    def test_zero_norm(self):
        score = self.algo.calculate_genre_similarity(
            {"action": 0},
            {"action": 0},
        )
        self.assertEqual(score, 0.0)


class TestFilmSimilarity(TestCase):
    def setUp(self):
        self.algo = MatchingAlgorithm()

    def test_empty_lists(self):
        self.assertEqual(self.algo.calculate_film_similarity([], []), 0.0)

    def test_empty_first(self):
        self.assertEqual(self.algo.calculate_film_similarity([], []), 0.0)


class TestAvailabilityOverlap(TestCase):
    def test_always_50(self):
        algo = MatchingAlgorithm()
        self.assertEqual(algo.calculate_availability_overlap(None, None), 50.0)


# ---------------------------------------------------------------------------
# MatchingAlgorithm — with DB
# ---------------------------------------------------------------------------

class TestCompatibility(TestCase):
    def setUp(self):
        self.algo = MatchingAlgorithm()
        self.user1 = make_user(
            "alice@test.com", "alice",
            genre_prefs={"action": 8, "drama": 5},
            mood="rire",
        )
        self.user2 = make_user(
            "bob@test.com", "bob",
            genre_prefs={"action": 7, "comedy": 3},
            mood="rire",
        )

    def test_compatibility_returns_tuple(self):
        score, reasons = self.algo.calculate_compatibility(self.user1, self.user2)
        self.assertIsInstance(score, int)
        self.assertIsInstance(reasons, list)
        self.assertGreaterEqual(len(reasons), 1)

    def test_score_in_range(self):
        score, _ = self.algo.calculate_compatibility(self.user1, self.user2)
        self.assertGreaterEqual(score, 0)
        self.assertLessEqual(score, 100)

    def test_same_mood_increases_score(self):
        score_same, _ = self.algo.calculate_compatibility(self.user1, self.user2)
        self.user2.profile.mood = "adrénaline"
        self.user2.profile.save()
        score_diff, _ = self.algo.calculate_compatibility(self.user1, self.user2)
        self.assertGreater(score_same, score_diff)

    def test_no_common_genres_low_score(self):
        self.user1.profile.genre_preferences = {"horror": 9}
        self.user1.profile.save()
        self.user2.profile.genre_preferences = {"comedy": 9}
        self.user2.profile.save()
        score, _ = self.algo.calculate_compatibility(self.user1, self.user2)
        self.assertLess(score, 50)


class TestGenerateCompatibilityReasons(TestCase):
    def setUp(self):
        self.algo = MatchingAlgorithm()
        self.user1 = make_user(
            "carol@test.com", "carol",
            genre_prefs={"action": 9, "drama": 7},
            mood="rire",
        )
        self.user2 = make_user(
            "david@test.com", "david",
            genre_prefs={"action": 8, "thriller": 6},
            mood="rire",
        )

    def test_fallback_reason(self):
        reasons = self.algo.generate_compatibility_reasons(
            self.user1, self.user2, genre_score=20, film_score=0, mood_score=0
        )
        self.assertIn("Profils complémentaires", reasons)

    def test_same_mood_reason(self):
        reasons = self.algo.generate_compatibility_reasons(
            self.user1, self.user2, genre_score=20, film_score=0, mood_score=100
        )
        self.assertTrue(any("rire" in r for r in reasons))

    def test_high_genre_score_reason(self):
        reasons = self.algo.generate_compatibility_reasons(
            self.user1, self.user2, genre_score=80, film_score=0, mood_score=0
        )
        self.assertTrue(any("action" in r.lower() for r in reasons))


# ---------------------------------------------------------------------------
# Matching models
# ---------------------------------------------------------------------------

class TestMatchModel(TestCase):
    def setUp(self):
        self.user1 = make_user("u1@test.com", "u1")
        self.user2 = make_user("u2@test.com", "u2")

    def test_create_match(self):
        match = Match.objects.create(
            user1=self.user1,
            user2=self.user2,
            score_compatibilite=75,
        )
        self.assertEqual(match.score_compatibilite, 75)
        self.assertEqual(match.status, "active")

    def test_match_str(self):
        match = Match.objects.create(
            user1=self.user1,
            user2=self.user2,
            score_compatibilite=80,
        )
        s = str(match)
        self.assertIn("80%", s)


class TestSwipeModel(TestCase):
    def setUp(self):
        self.user1 = make_user("sw1@test.com", "sw1")
        self.user2 = make_user("sw2@test.com", "sw2")

    def test_create_swipe(self):
        swipe = Swipe.objects.create(
            from_user=self.user1,
            to_user=self.user2,
            action="like",
        )
        self.assertEqual(swipe.action, "like")
