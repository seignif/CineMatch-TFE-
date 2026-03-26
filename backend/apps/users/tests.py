from django.test import TestCase

from apps.users.models import ProfileFilmSignature, User, UserProfile


class TestUserModel(TestCase):
    def test_create_user(self):
        user = User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="securepass123",
            first_name="Test",
            last_name="User",
        )
        self.assertEqual(user.email, "test@example.com")
        self.assertTrue(user.check_password("securepass123"))

    def test_str(self):
        user = User.objects.create_user(
            username="strtest",
            email="strtest@example.com",
            password="pass",
            first_name="A",
            last_name="B",
        )
        self.assertEqual(str(user), "strtest@example.com")

    def test_profile_auto_created_by_signal(self):
        user = User.objects.create_user(
            username="siguser",
            email="signal@example.com",
            password="pass",
            first_name="S",
            last_name="G",
        )
        self.assertTrue(hasattr(user, "profile"))
        self.assertIsInstance(user.profile, UserProfile)

    def test_email_is_unique(self):
        User.objects.create_user(
            username="u1", email="dup@example.com", password="pass",
            first_name="A", last_name="B",
        )
        with self.assertRaises(Exception):
            User.objects.create_user(
                username="u2", email="dup@example.com", password="pass",
                first_name="C", last_name="D",
            )


class TestUserProfile(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="profuser",
            email="prof@example.com",
            password="pass",
            first_name="P",
            last_name="R",
        )
        self.profile = self.user.profile

    def test_str(self):
        self.assertEqual(str(self.profile), "Profil de prof@example.com")

    def test_defaults(self):
        self.assertEqual(self.profile.genre_preferences, {})
        self.assertEqual(self.profile.badges, [])
        self.assertEqual(self.profile.stats, {})
        self.assertFalse(self.profile.rgpd_consent)
        self.assertEqual(self.profile.mood, "")

    def test_update_genre_preferences(self):
        self.profile.genre_preferences = {"action": 8, "drama": 5}
        self.profile.save()
        self.profile.refresh_from_db()
        self.assertEqual(self.profile.genre_preferences["action"], 8)

    def test_update_mood(self):
        self.profile.mood = "rire"
        self.profile.save()
        self.profile.refresh_from_db()
        self.assertEqual(self.profile.mood, "rire")
