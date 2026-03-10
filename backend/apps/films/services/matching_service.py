import re
from difflib import SequenceMatcher
from unidecode import unidecode


def normalize_title(title: str) -> str:
    """Normalise un titre pour le fuzzy matching."""
    title = title.lower()
    title = unidecode(title)  # Supprime les accents
    title = re.sub(r'[^\w\s]', '', title)  # Supprime la ponctuation
    # Supprime les articles français et anglais
    for article in ['le', 'la', 'les', 'un', 'une', 'des', 'the', 'a', 'an']:
        title = re.sub(rf'\b{article}\b', '', title)
    return title.strip()


def fuzzy_match_title(title1: str, title2: str, threshold: float = 0.75) -> tuple[bool, float]:
    """
    Compare deux titres de films avec tolérance aux variations orthographiques.

    Returns:
        (matched: bool, ratio: float) - matched=True si ratio >= threshold
    """
    norm1 = normalize_title(title1)
    norm2 = normalize_title(title2)

    if not norm1 or not norm2:
        return False, 0.0

    ratio = SequenceMatcher(None, norm1, norm2).ratio()
    return ratio >= threshold, ratio


def match_movieglu_to_tmdb(movieglu_film_data: dict):
    """
    Trouve le film TMDb correspondant à un film retourné par MovieGlu.

    movieglu_film_data contient au moins :
        - film_name  : str
        - film_id    : int  (ID MovieGlu, pas TMDb)

    Stratégie :
        1. Match exact sur titre normalisé
        2. Match fuzzy (seuil 0.75) sur titre FR ou titre original
        3. Retourne None si aucun match → loggé pour correction admin

    Returns:
        Film instance ou None
    """
    from apps.films.models import Film

    movieglu_title = movieglu_film_data.get('film_name', '')
    if not movieglu_title:
        return None

    best_film = None
    best_ratio = 0.0

    for film in Film.objects.filter(is_now_playing=True).only('id', 'titre', 'titre_original'):
        for title in [film.titre, film.titre_original]:
            if not title:
                continue
            matched, ratio = fuzzy_match_title(title, movieglu_title)
            if matched and ratio > best_ratio:
                best_ratio = ratio
                best_film = film

    return best_film
