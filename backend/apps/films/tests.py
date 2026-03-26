import datetime

from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient

from apps.films.models import Cinema, Film, Genre, Seance
from apps.films.serializers import (
    CinemaSerializer,
    FilmDetailSerializer,
    FilmSerializer,
    GenreSerializer,
)
from apps.films.services.matching_service import fuzzy_match_title, normalize_title


# ---------------------------------------------------------------------------
# matching_service
# ---------------------------------------------------------------------------

class TestNormalizeTitle(TestCase):
    def test_removes_french_articles(self):
        self.assertEqual(normalize_title("Le Film"), "film")
        self.assertEqual(normalize_title("Les Films"), "films")
        self.assertEqual(normalize_title("La Nuit"), "nuit")

    def test_removes_english_articles(self):
        self.assertEqual(normalize_title("The Matrix"), "matrix")
        self.assertEqual(normalize_title("A Beautiful Mind"), "beautiful mind")

    def test_removes_accents(self):
        result = normalize_title("Étoile")
        self.assertEqual(result, "etoile")

    def test_lowercase(self):
        self.assertEqual(normalize_title("AVATAR"), "avatar")

    def test_removes_punctuation(self):
        result = normalize_title("Spider-Man: No Way Home")
        self.assertNotIn("-", result)
        self.assertNotIn(":", result)

    def test_empty_string(self):
        self.assertEqual(normalize_title(""), "")


class TestFuzzyMatchTitle(TestCase):
    def test_identical_titles(self):
        matched, ratio = fuzzy_match_title("Avatar", "Avatar")
        self.assertTrue(matched)
        self.assertEqual(ratio, 1.0)

    def test_similar_titles(self):
        matched, ratio = fuzzy_match_title(
            "Avatar The Way of Water", "Avatar: The Way of Water"
        )
        self.assertTrue(matched)
        self.assertGreater(ratio, 0.75)

    def test_different_titles(self):
        matched, ratio = fuzzy_match_title("Avatar", "Titanic")
        self.assertFalse(matched)

    def test_empty_first(self):
        matched, ratio = fuzzy_match_title("", "Avatar")
        self.assertFalse(matched)
        self.assertEqual(ratio, 0.0)

    def test_empty_both(self):
        matched, ratio = fuzzy_match_title("", "")
        self.assertFalse(matched)
        self.assertEqual(ratio, 0.0)

    def test_custom_threshold(self):
        matched, ratio = fuzzy_match_title("Avatar", "Avatarr", threshold=0.90)
        self.assertTrue(matched)

    def test_threshold_not_met(self):
        matched, _ = fuzzy_match_title("Avatar", "Titanic", threshold=0.50)
        self.assertFalse(matched)


# ---------------------------------------------------------------------------
# Genre model
# ---------------------------------------------------------------------------

class TestGenreModel(TestCase):
    def test_str(self):
        genre = Genre(name="Action")
        self.assertEqual(str(genre), "Action")

    def test_create_with_tmdb_id(self):
        genre = Genre.objects.create(name="Comedy", tmdb_id=35)
        self.assertEqual(genre.tmdb_id, 35)

    def test_create_without_tmdb_id(self):
        genre = Genre.objects.create(name="Drama")
        self.assertIsNone(genre.tmdb_id)

    def test_unique_name(self):
        Genre.objects.create(name="Horror")
        with self.assertRaises(Exception):
            Genre.objects.create(name="Horror")


# ---------------------------------------------------------------------------
# Cinema model
# ---------------------------------------------------------------------------

class TestCinemaModel(TestCase):
    def test_str(self):
        cinema = Cinema(name="Kinepolis Braine")
        self.assertEqual(str(cinema), "Kinepolis Braine")

    def test_create(self):
        cinema = Cinema.objects.create(
            kinepolis_id="KBRAI",
            name="Kinepolis Braine",
            country="BE",
            language="FR",
        )
        self.assertEqual(cinema.kinepolis_id, "KBRAI")
        self.assertTrue(cinema.is_active)

    def test_defaults(self):
        cinema = Cinema.objects.create(kinepolis_id="TEST", name="Test")
        self.assertEqual(cinema.country, "BE")
        self.assertEqual(cinema.language, "FR")
        self.assertIsNone(cinema.latitude)


# ---------------------------------------------------------------------------
# Film model
# ---------------------------------------------------------------------------

class TestFilmModel(TestCase):
    def setUp(self):
        self.genre = Genre.objects.create(name="Action")
        self.film = Film.objects.create(
            kinepolis_id="HO00011897",
            title="One Battle After Another",
            duration=161,
        )
        self.film.genres.add(self.genre)

    def test_str(self):
        self.assertEqual(str(self.film), "One Battle After Another")

    def test_genres(self):
        self.assertEqual(self.film.genres.count(), 1)

    def test_is_future_default(self):
        self.assertFalse(self.film.is_future)

    def test_tmdb_id_nullable(self):
        self.assertIsNone(self.film.tmdb_id)


# ---------------------------------------------------------------------------
# Seance model
# ---------------------------------------------------------------------------

class TestSeanceModel(TestCase):
    def setUp(self):
        self.film = Film.objects.create(kinepolis_id="HO001", title="Test Film")
        self.cinema = Cinema.objects.create(kinepolis_id="KBRAI", name="Kinepolis Braine")
        self.seance = Seance.objects.create(
            kinepolis_session_id="KBRAI-123",
            film=self.film,
            cinema=self.cinema,
            showtime=timezone.now() + datetime.timedelta(days=1),
            booking_url="https://kinepolis.be/fr/direct-vista-redirect/123/0/KBRAI/0",
        )

    def test_str(self):
        s = str(self.seance)
        self.assertIn("Test Film", s)
        self.assertIn("Kinepolis Braine", s)

    def test_booking_url(self):
        self.assertTrue(self.seance.booking_url.startswith("https://kinepolis.be"))

    def test_defaults(self):
        self.assertFalse(self.seance.is_sold_out)
        self.assertFalse(self.seance.has_cosy_seating)


# ---------------------------------------------------------------------------
# Serializers
# ---------------------------------------------------------------------------

class TestGenreSerializer(TestCase):
    def test_fields(self):
        genre = Genre.objects.create(name="Thriller", tmdb_id=53)
        data = GenreSerializer(genre).data
        self.assertEqual(data["name"], "Thriller")
        self.assertEqual(data["tmdb_id"], 53)


class TestCinemaSerializer(TestCase):
    def test_fields(self):
        cinema = Cinema.objects.create(kinepolis_id="SL", name="Kinepolis Leuven")
        data = CinemaSerializer(cinema).data
        self.assertEqual(data["kinepolis_id"], "SL")
        self.assertEqual(data["name"], "Kinepolis Leuven")


class TestFilmSerializer(TestCase):
    def setUp(self):
        self.genre = Genre.objects.create(name="Drama")
        self.film = Film.objects.create(
            kinepolis_id="HO002",
            title="Test Film",
            duration=120,
        )
        self.film.genres.add(self.genre)

    def test_list_serializer(self):
        data = FilmSerializer(self.film).data
        self.assertEqual(data["title"], "Test Film")
        self.assertEqual(data["kinepolis_id"], "HO002")
        self.assertEqual(len(data["genres"]), 1)

    def test_detail_serializer(self):
        data = FilmDetailSerializer(self.film).data
        self.assertIn("synopsis", data)
        self.assertIn("seances", data)
        self.assertIn("backdrop_url", data)


# ---------------------------------------------------------------------------
# Views (API endpoints)
# ---------------------------------------------------------------------------

class TestFilmsAPI(TestCase):
    def setUp(self):
        self.client = APIClient()
        genre = Genre.objects.create(name="Action")
        self.film = Film.objects.create(
            kinepolis_id="HO003",
            title="API Test Film",
            duration=90,
            is_future=False,
        )
        self.film.genres.add(genre)
        self.future_film = Film.objects.create(
            kinepolis_id="HO004",
            title="Future Film",
            is_future=True,
        )
        self.cinema = Cinema.objects.create(kinepolis_id="TCINEMA", name="Test Cinema")

    def test_list_films(self):
        response = self.client.get("/api/films/films/")
        self.assertEqual(response.status_code, 200)
        self.assertGreaterEqual(response.data["count"], 2)

    def test_retrieve_film(self):
        response = self.client.get(f"/api/films/films/{self.film.pk}/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["title"], "API Test Film")

    def test_list_cinemas(self):
        response = self.client.get("/api/films/cinemas/")
        self.assertEqual(response.status_code, 200)
        self.assertGreaterEqual(response.data["count"], 1)

    def test_retrieve_cinema(self):
        response = self.client.get(f"/api/films/cinemas/{self.cinema.pk}/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["kinepolis_id"], "TCINEMA")

    def test_filter_is_future_false(self):
        response = self.client.get("/api/films/films/?is_future=false")
        self.assertEqual(response.status_code, 200)
        for film in response.data["results"]:
            self.assertFalse(film["is_future"])

    def test_filter_is_future_true(self):
        response = self.client.get("/api/films/films/?is_future=true")
        self.assertEqual(response.status_code, 200)
        for film in response.data["results"]:
            self.assertTrue(film["is_future"])

    def test_search_films(self):
        response = self.client.get("/api/films/films/?search=API+Test")
        self.assertEqual(response.status_code, 200)
        self.assertGreaterEqual(response.data["count"], 1)

    def test_search_no_result(self):
        response = self.client.get("/api/films/films/?search=xyznotexist")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["count"], 0)

    def test_film_seances_empty(self):
        response = self.client.get(f"/api/films/films/{self.film.pk}/seances/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 0)

    def test_cinema_seances_empty(self):
        response = self.client.get(f"/api/films/cinemas/{self.cinema.pk}/seances/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 0)

    def test_film_seances_with_data(self):
        seance = Seance.objects.create(
            kinepolis_session_id="TCINEMA-999",
            film=self.film,
            cinema=self.cinema,
            showtime=timezone.now() + datetime.timedelta(hours=2),
            booking_url="https://kinepolis.be/fr/direct-vista-redirect/999/0/TCINEMA/0",
        )
        response = self.client.get(f"/api/films/films/{self.film.pk}/seances/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["kinepolis_session_id"], "TCINEMA-999")
        self.assertEqual(
            response.data[0]["booking_url"],
            "https://kinepolis.be/fr/direct-vista-redirect/999/0/TCINEMA/0",
        )
