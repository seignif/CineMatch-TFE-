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
