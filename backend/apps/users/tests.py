from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken

from apps.users.models import ProfileFilmSignature, User, UserProfile


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def make_user(email, username, password="testpass123"):
    return User.objects.create_user(
        username=username,
        email=email,
        password=password,
        first_name="Test",
        last_name="User",
    )


def auth_client(user):
    client = APIClient()
    refresh = RefreshToken.for_user(user)
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {refresh.access_token}")
    return client


# ---------------------------------------------------------------------------
# User model
# ---------------------------------------------------------------------------

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


# ---------------------------------------------------------------------------
# UserProfile model
# ---------------------------------------------------------------------------

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

    def test_mood_choices_no_accents(self):
        for key in ("rire", "reflechir", "emu", "adrenaline"):
            self.profile.mood = key
            self.profile.save()
            self.profile.refresh_from_db()
            self.assertEqual(self.profile.mood, key)


# ---------------------------------------------------------------------------
# Register endpoint  US-004
# ---------------------------------------------------------------------------

class TestRegisterView(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.url = "/api/auth/register/"
        self.valid_payload = {
            "email": "new@example.com",
            "username": "newuser",
            "password": "StrongPass1!",
            "password2": "StrongPass1!",
            "first_name": "New",
            "last_name": "User",
        }

    def test_register_success(self):
        response = self.client.post(self.url, self.valid_payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn("tokens", response.data)
        self.assertIn("access", response.data["tokens"])
        self.assertIn("refresh", response.data["tokens"])

    def test_register_creates_user(self):
        self.client.post(self.url, self.valid_payload, format="json")
        self.assertTrue(User.objects.filter(email="new@example.com").exists())

    def test_register_creates_profile(self):
        self.client.post(self.url, self.valid_payload, format="json")
        user = User.objects.get(email="new@example.com")
        self.assertTrue(hasattr(user, "profile"))

    def test_register_passwords_mismatch(self):
        payload = {**self.valid_payload, "password2": "WrongPass1!"}
        response = self.client.post(self.url, payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_register_duplicate_email(self):
        self.client.post(self.url, self.valid_payload, format="json")
        response = self.client.post(self.url, self.valid_payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_register_missing_fields(self):
        response = self.client.post(self.url, {"email": "x@x.com"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_register_weak_password(self):
        payload = {**self.valid_payload, "password": "123", "password2": "123"}
        response = self.client.post(self.url, payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


# ---------------------------------------------------------------------------
# Login endpoint  US-005
# ---------------------------------------------------------------------------

class TestLoginView(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.url = "/api/auth/login/"
        self.user = make_user("login@example.com", "loginuser", password="MyPass123!")

    def test_login_success(self):
        response = self.client.post(
            self.url,
            {"email": "login@example.com", "password": "MyPass123!"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("access", response.data)
        self.assertIn("refresh", response.data)

    def test_login_wrong_password(self):
        response = self.client.post(
            self.url,
            {"email": "login@example.com", "password": "wrong"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_login_unknown_email(self):
        response = self.client.post(
            self.url,
            {"email": "nobody@example.com", "password": "MyPass123!"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


# ---------------------------------------------------------------------------
# Logout endpoint  US-006
# ---------------------------------------------------------------------------

class TestLogoutView(TestCase):
    def setUp(self):
        self.user = make_user("logout@example.com", "logoutuser")
        self.url = "/api/auth/logout/"

    def test_logout_success(self):
        client = auth_client(self.user)
        refresh = str(RefreshToken.for_user(self.user))
        response = client.post(self.url, {"refresh": refresh}, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_logout_invalid_token(self):
        client = auth_client(self.user)
        response = client.post(self.url, {"refresh": "badtoken"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_logout_unauthenticated(self):
        client = APIClient()
        response = client.post(self.url, {"refresh": "x"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


# ---------------------------------------------------------------------------
# Me endpoint  US-005 / US-008
# ---------------------------------------------------------------------------

class TestMeView(TestCase):
    def setUp(self):
        self.user = make_user("me@example.com", "meuser")
        self.client = auth_client(self.user)
        self.url = "/api/users/me/"

    def test_get_me(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["email"], "me@example.com")
        self.assertIn("profile", response.data)

    def test_patch_me(self):
        response = self.client.patch(self.url, {"first_name": "Updated"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["first_name"], "Updated")

    def test_me_unauthenticated(self):
        response = APIClient().get(self.url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


# ---------------------------------------------------------------------------
# Update profile endpoint  US-008
# ---------------------------------------------------------------------------

class TestUpdateProfileView(TestCase):
    def setUp(self):
        self.user = make_user("profile@example.com", "profileuser")
        self.client = auth_client(self.user)
        self.url = "/api/users/me/profile/"

    def test_patch_bio(self):
        response = self.client.patch(
            self.url, {"bio": "Cinéphile passionné"}, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.user.profile.refresh_from_db()
        self.assertEqual(self.user.profile.bio, "Cinéphile passionné")

    def test_patch_mood(self):
        response = self.client.patch(self.url, {"mood": "rire"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.user.profile.refresh_from_db()
        self.assertEqual(self.user.profile.mood, "rire")

    def test_patch_genre_preferences(self):
        payload = {"genre_preferences": {"action": 9, "drama": 6}}
        response = self.client.patch(self.url, payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.user.profile.refresh_from_db()
        self.assertEqual(self.user.profile.genre_preferences["action"], 9)

    def test_films_signature_too_many(self):
        response = self.client.patch(
            self.url,
            {"films_signature_ids": [1, 2, 3, 4, 5, 6]},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_unauthenticated(self):
        response = APIClient().patch(self.url, {"bio": "x"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


# ---------------------------------------------------------------------------
# Change password endpoint  US-007
# ---------------------------------------------------------------------------

class TestChangePasswordView(TestCase):
    def setUp(self):
        self.user = make_user("pw@example.com", "pwuser", password="OldPass1!")
        self.client = auth_client(self.user)
        self.url = "/api/auth/change-password/"

    def test_change_password_success(self):
        response = self.client.post(
            self.url,
            {"old_password": "OldPass1!", "new_password": "NewPass2@"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password("NewPass2@"))

    def test_wrong_old_password(self):
        response = self.client.post(
            self.url,
            {"old_password": "WrongOld!", "new_password": "NewPass2@"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_weak_new_password(self):
        response = self.client.post(
            self.url,
            {"old_password": "OldPass1!", "new_password": "123"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_unauthenticated(self):
        response = APIClient().post(self.url, {}, format="json")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
