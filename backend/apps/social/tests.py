from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken

from apps.users.models import User
from apps.social.models import Post, PostComment, PostLike, Report


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def make_user(email, username, password="testpass123"):
    return User.objects.create_user(
        username=username, email=email, password=password,
        first_name="Test", last_name="User",
    )


def auth_client(user):
    client = APIClient()
    refresh = RefreshToken.for_user(user)
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {refresh.access_token}")
    return client


# ---------------------------------------------------------------------------
# Post model — is_hidden
# ---------------------------------------------------------------------------

class TestPostModel(TestCase):
    def setUp(self):
        self.user = make_user("postmodel@example.com", "postmodeluser")

    def test_post_not_hidden_by_default(self):
        post = Post.objects.create(author=self.user, content="Bonjour")
        self.assertFalse(post.is_hidden)

    def test_post_str(self):
        post = Post.objects.create(author=self.user, content="Test contenu")
        self.assertIn("Test", str(post))

    def test_hidden_post_excluded_from_feed(self):
        Post.objects.create(author=self.user, content="Visible")
        Post.objects.create(author=self.user, content="Caché", is_hidden=True)
        visible = Post.objects.filter(is_hidden=False)
        self.assertEqual(visible.count(), 1)
        self.assertEqual(visible.first().content, "Visible")


# ---------------------------------------------------------------------------
# Report model
# ---------------------------------------------------------------------------

class TestReportModel(TestCase):
    def setUp(self):
        self.reporter = make_user("reporter@example.com", "reporteruser")
        self.reported = make_user("reported@example.com", "reporteduser")
        self.post = Post.objects.create(author=self.reported, content="Contenu signalé")

    def test_report_creation(self):
        report = Report.objects.create(
            reporter=self.reporter,
            type="post",
            reason="spam",
            post=self.post,
            reported_user=self.reported,
        )
        self.assertEqual(report.status, "pending")
        self.assertEqual(report.type, "post")

    def test_report_str(self):
        report = Report.objects.create(
            reporter=self.reporter, type="post", reason="spam",
        )
        self.assertIn("post", str(report))


# ---------------------------------------------------------------------------
# ReportCreateView — POST /api/social/reports/  (US-075/076)
# ---------------------------------------------------------------------------

class TestReportCreateView(TestCase):
    def setUp(self):
        self.reporter = make_user("rptview@example.com", "rptviewuser")
        self.other = make_user("rptother@example.com", "rptotheruser")
        self.client = auth_client(self.reporter)
        self.url = "/api/social/reports/"
        self.post = Post.objects.create(author=self.other, content="Mauvais contenu")

    def test_requires_auth(self):
        response = APIClient().post(self.url, {"type": "post", "reason": "spam", "post": self.post.id}, format="json")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_report_post_success(self):
        response = self.client.post(self.url, {
            "type": "post", "reason": "spam",
            "post": self.post.id, "reported_user": self.other.id,
        }, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Report.objects.count(), 1)

    def test_cannot_report_self(self):
        own_post = Post.objects.create(author=self.reporter, content="Mon post")
        response = self.client.post(self.url, {
            "type": "post", "reason": "spam",
            "post": own_post.id, "reported_user": self.reporter.id,
        }, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_duplicate_report_ignored(self):
        payload = {"type": "post", "reason": "spam", "post": self.post.id, "reported_user": self.other.id}
        self.client.post(self.url, payload, format="json")
        response = self.client.post(self.url, payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(Report.objects.count(), 1)

    def test_report_message(self):
        response = self.client.post(self.url, {
            "type": "message", "reason": "harassment",
            "message_id": 42, "message_content": "Texte irrespectueux",
            "reported_user": self.other.id,
        }, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_report_group_message(self):
        response = self.client.post(self.url, {
            "type": "group_message", "reason": "harassment",
            "message_id": 99, "message_content": "Texte groupe",
            "reported_user": self.other.id,
        }, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)


# ---------------------------------------------------------------------------
# Auto-hide — post masqué après 3 signalements
# ---------------------------------------------------------------------------

class TestPostAutoHide(TestCase):
    def setUp(self):
        self.author = make_user("autoauthor@example.com", "autoauthoruser")
        self.post = Post.objects.create(author=self.author, content="Post à masquer")
        self.url = "/api/social/reports/"

    def _make_reporter(self, n):
        u = make_user(f"autoreporter{n}@example.com", f"autoreporteruser{n}")
        return auth_client(u)

    def test_post_auto_hidden_at_three_reports(self):
        for i in range(3):
            client = self._make_reporter(i)
            client.post(self.url, {
                "type": "post", "reason": "spam",
                "post": self.post.id, "reported_user": self.author.id,
            }, format="json")
        self.post.refresh_from_db()
        self.assertTrue(self.post.is_hidden)

    def test_post_not_hidden_at_two_reports(self):
        for i in range(2):
            client = self._make_reporter(i)
            client.post(self.url, {
                "type": "post", "reason": "spam",
                "post": self.post.id, "reported_user": self.author.id,
            }, format="json")
        self.post.refresh_from_db()
        self.assertFalse(self.post.is_hidden)

    def test_hidden_post_excluded_from_api_feed(self):
        self.post.is_hidden = True
        self.post.save()
        reporter = make_user("feedcheck@example.com", "feedcheckuser")
        client = auth_client(reporter)
        response = client.get("/api/social/posts/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = response.data.get("results") if isinstance(response.data, dict) else response.data
        ids = [p["id"] for p in results]
        self.assertNotIn(self.post.id, ids)
