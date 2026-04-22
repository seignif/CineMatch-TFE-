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


# ---------------------------------------------------------------------------
# BadgeService (US-039 / US-040)
# ---------------------------------------------------------------------------

from apps.users.badge_service import BadgeService, BADGE_DEFINITIONS
from apps.matching.models import Match, PlannedOuting, Review


def _make_badge_user(email, username):
    return User.objects.create_user(
        username=username, email=email, password="pass",
        first_name="Badge", last_name="User",
    )


class TestBadgeDefinitions(TestCase):
    def test_seven_badges_defined(self):
        self.assertEqual(len(BADGE_DEFINITIONS), 7)

    def test_badge_has_required_fields(self):
        for badge_id, badge in BADGE_DEFINITIONS.items():
            self.assertIn('id', badge)
            self.assertIn('name', badge)
            self.assertIn('tier', badge)
            self.assertIn('svg_id', badge)


class TestGetAllBadgesInfo(TestCase):
    def setUp(self):
        self.user = _make_badge_user("badges1@test.com", "badgeuser1")

    def test_returns_seven_badges(self):
        badges = BadgeService.get_all_badges_info(self.user)
        self.assertEqual(len(badges), 7)

    def test_all_not_earned_by_default(self):
        badges = BadgeService.get_all_badges_info(self.user)
        for badge in badges:
            self.assertFalse(badge['earned'])

    def test_earned_badge_shown(self):
        self.user.profile.badges = ['clap_debut']
        self.user.profile.save()
        badges = BadgeService.get_all_badges_info(self.user)
        earned = {b['id']: b['earned'] for b in badges}
        self.assertTrue(earned['clap_debut'])
        self.assertFalse(earned['montee_marches'])


class TestIsProfileComplete(TestCase):
    def setUp(self):
        self.user = _make_badge_user("badges2@test.com", "badgeuser2")

    def test_incomplete_profile(self):
        self.assertFalse(BadgeService._is_profile_complete(self.user.profile))

    def test_complete_profile_without_films(self):
        self.user.profile.bio = "Bio"
        self.user.profile.mood = "rire"
        self.user.profile.genre_preferences = {"Action": 8}
        self.user.profile.save()
        self.assertFalse(BadgeService._is_profile_complete(self.user.profile))


class TestGetReputationScore(TestCase):
    def setUp(self):
        self.user = _make_badge_user("rep1@test.com", "repuser1")
        self.reviewer = _make_badge_user("rep2@test.com", "repuser2")

    def test_no_reviews(self):
        result = BadgeService.get_reputation_score(self.user)
        self.assertEqual(result['score'], None)
        self.assertEqual(result['count'], 0)
        self.assertEqual(result['label'], 'Nouveau')

    def test_fewer_than_three_reviews(self):
        match = Match.objects.create(
            user1=self.reviewer, user2=self.user,
            score_compatibilite=80,
        )
        outing = PlannedOuting.objects.create(
            match=match, proposer=self.reviewer, status='completed',
        )
        Review.objects.create(
            outing=outing, reviewer=self.reviewer, reviewed=self.user,
            rating=5, would_go_again=True,
        )
        result = BadgeService.get_reputation_score(self.user)
        self.assertEqual(result['count'], 1)
        self.assertIsNone(result['score'])  # masqué si < 3 avis

    def test_three_reviews_show_score(self):
        match = Match.objects.create(
            user1=self.reviewer, user2=self.user,
            score_compatibilite=80,
        )
        outing = PlannedOuting.objects.create(
            match=match, proposer=self.reviewer, status='completed',
        )
        for i in range(3):
            r = _make_badge_user(f"rev{i}@test.com", f"revuser{i}")
            Review.objects.create(
                outing=outing, reviewer=r, reviewed=self.user,
                rating=5, would_go_again=True,
            )
        result = BadgeService.get_reputation_score(self.user)
        self.assertEqual(result['count'], 3)
        self.assertIsNotNone(result['score'])
        self.assertEqual(result['label'], 'Excellent')


class TestCheckAndAwardBadges(TestCase):
    def setUp(self):
        self.user = _make_badge_user("award1@test.com", "awarduser1")
        self.other = _make_badge_user("award2@test.com", "awarduser2")

    def test_no_badges_without_match(self):
        new_badges = BadgeService.check_and_award_badges(self.user)
        self.assertEqual(new_badges, [])

    def test_clap_debut_awarded_on_match(self):
        Match.objects.create(
            user1=self.user, user2=self.other,
            score_compatibilite=75,
        )
        new_badges = BadgeService.check_and_award_badges(self.user)
        badge_ids = [b['id'] for b in new_badges]
        self.assertIn('clap_debut', badge_ids)

    def test_badge_not_awarded_twice(self):
        Match.objects.create(
            user1=self.user, user2=self.other,
            score_compatibilite=75,
        )
        BadgeService.check_and_award_badges(self.user)
        new_badges = BadgeService.check_and_award_badges(self.user)
        badge_ids = [b['id'] for b in new_badges]
        self.assertNotIn('clap_debut', badge_ids)
