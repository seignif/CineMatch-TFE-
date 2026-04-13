import logging
import random

from django.core.cache import cache

logger = logging.getLogger(__name__)

MOOD_LABELS = {
    'rire': 'Envie de rire',
    'reflechir': 'Besoin de réfléchir',
    'emu': "Envie d'être ému",
    'adrenaline': "Besoin d'adrénaline",
}


class MatchingAIService:
    """
    Moteur de génération de messages de compatibilité personnalisés.
    Utilise les données réelles des profils (genres, films, ville, humeur)
    pour produire des messages contextualisés sans dépendance externe.
    Résultats mis en cache 24h dans Redis.
    """

    CACHE_TTL = 86400  # 24h

    def generate_match_content(self, user1, user2, score: int, algorithmic_reasons: list) -> tuple:
        cache_key = f"ai_match_{min(user1.id, user2.id)}_{max(user1.id, user2.id)}"
        cached = cache.get(cache_key)
        if cached:
            return cached['reasons'], cached['message']

        try:
            result = self._generate(user1, user2, score, algorithmic_reasons)
            cache.set(cache_key, result, self.CACHE_TTL)
            return result['reasons'], result['message']
        except Exception as e:
            logger.warning(f"Message generation error for match {user1.id}/{user2.id}: {e}")
            return algorithmic_reasons, self._fallback_message(user1, score)

    # ------------------------------------------------------------------
    # Core generation
    # ------------------------------------------------------------------

    def _generate(self, user1, user2, score: int, algorithmic_reasons: list) -> dict:
        p1 = user1.profile
        p2 = user2.profile

        shared_genres = self._shared_genres(p1, p2)
        shared_films = self._shared_films(p1, p2)
        same_city = self._same_city(user1, user2)
        same_mood = bool(p1.mood and p2.mood and p1.mood == p2.mood)
        mood_label = MOOD_LABELS.get(p1.mood or '', '')

        reasons = self._build_reasons(
            shared_genres, shared_films, same_city, same_mood, mood_label,
            user1, user2, score,
        )
        message = self._build_message(
            user1, user2, score,
            shared_genres, shared_films, same_city, same_mood, mood_label,
        )

        return {'reasons': reasons[:4], 'message': message}

    # ------------------------------------------------------------------
    # Data helpers
    # ------------------------------------------------------------------

    def _shared_genres(self, p1, p2) -> list:
        prefs1 = set((p1.genre_preferences or {}).keys())
        prefs2 = set((p2.genre_preferences or {}).keys())
        return sorted(prefs1 & prefs2)

    def _shared_films(self, p1, p2) -> list:
        films1 = {f.title for f in p1.films_signature.all()}
        films2 = {f.title for f in p2.films_signature.all()}
        return sorted(films1 & films2)

    def _same_city(self, user1, user2):
        c1 = (user1.city or '').strip()
        c2 = (user2.city or '').strip()
        return c1 if c1 and c2 and c1.lower() == c2.lower() else None

    # ------------------------------------------------------------------
    # Reasons builder
    # ------------------------------------------------------------------

    def _build_reasons(self, shared_genres, shared_films, same_city,
                       same_mood, mood_label, user1, user2, score) -> list:
        reasons = []

        if shared_genres:
            reasons.append(f"Genres en commun : {', '.join(shared_genres[:3])}")

        if shared_films:
            reasons.append(f"Films en commun : {', '.join(shared_films[:2])}")

        if same_mood and mood_label:
            reasons.append(f"Même envie du moment : {mood_label}")

        if same_city:
            reasons.append(f"Même ville : {same_city}")

        if not reasons:
            reasons.append("Profils complémentaires")

        return reasons

    # ------------------------------------------------------------------
    # Message builder
    # ------------------------------------------------------------------

    def _build_message(self, user1, user2, score,
                       shared_genres, shared_films, same_city, same_mood, mood_label) -> str:
        n1 = user1.first_name
        n2 = user2.first_name
        g = shared_genres[0] if shared_genres else None
        f = shared_films[0] if shared_films else None

        if score >= 80:
            candidates = [
                f"Excellente nouvelle, {n1} ! {n2} et toi avez un profil cinéphile très proche — c'est rare, il faut en profiter !",
            ]
            if g and same_city:
                candidates += [
                    f"{n1}, tu as trouvé un vrai alter ego : même passion pour {g}, même ville. Une sortie ciné s'impose !",
                    f"Incroyable compatibilité, {n1} ! Avec {n2}, vous partagez {g} et êtes tous les deux à {same_city}. Lancez-vous !",
                ]
            elif g and f:
                candidates += [
                    f"{n1}, {n2} a les mêmes coups de cœur que toi : {g} et même le film '{f}'. Cette connexion est exceptionnelle !",
                    f"Wow, {n1} ! Mêmes genres, mêmes films — {n2} semble être exactement la personne qu'il te faut.",
                ]
            elif g:
                candidates += [
                    f"{n1}, votre amour commun pour {g} n'est que la surface. Vos profils s'accordent à un niveau remarquable !",
                    f"Cette compatibilité parle d'elle-même, {n1}. {n2} partage ta passion pour {g} — ne laisse pas passer ça.",
                ]
            elif same_city:
                candidates += [
                    f"{n1}, {n2} est à {same_city} et vos profils s'accordent parfaitement. C'est l'occasion idéale !",
                ]

        elif score >= 60:
            candidates = [
                f"Belle rencontre en perspective, {n1} ! {n2} et toi avez de vraies affinités cinéphiles.",
            ]
            if g:
                candidates += [
                    f"{n1}, vous partagez tous les deux un faible pour {g}. Un bon point de départ pour une vraie conversation !",
                    f"Bonne compatibilité, {n1} ! {n2} aime aussi {g} — voilà déjà un sujet de conversation tout trouvé.",
                ]
            if same_mood and mood_label:
                candidates += [
                    f"{n1}, vous avez la même envie ce soir : {mood_label.lower()}. C'est peut-être le bon moment pour proposer une sortie à {n2} !",
                ]
            if same_city:
                candidates += [
                    f"{n1}, {n2} est dans ta ville. Bonne compatibilité globale — pourquoi ne pas vous retrouver autour d'un film ?",
                ]
            if f:
                candidates += [
                    f"Vous avez tous les deux '{f}' dans vos favoris, {n1}. Voilà un excellent point de départ !",
                ]

        else:
            candidates = [
                f"Chaque rencontre est unique, {n1}. {n2} pourrait t'apporter un regard différent sur le cinéma.",
                f"{n1}, les meilleures surprises arrivent parfois là où on s'y attend le moins. {n2} attend peut-être ta curiosité !",
                f"Différents mais complémentaires, {n1} — c'est souvent là que naissent les échanges les plus intéressants.",
            ]
            if g:
                candidates += [
                    f"{n1}, vous avez en commun un goût pour {g}. Parfois les meilleures rencontres partent de peu !",
                ]

        return random.choice(candidates)

    # ------------------------------------------------------------------
    # Fallback (si exception inattendue)
    # ------------------------------------------------------------------

    def _fallback_message(self, user, score: int) -> str:
        if score >= 80:
            return f"Excellente compatibilité ! Vous semblez avoir beaucoup en commun, {user.first_name}."
        if score >= 60:
            return f"Bonne compatibilité, {user.first_name} ! Ca vaut le coup de se rencontrer."
        return f"Pourquoi ne pas tenter l'experience, {user.first_name} ?"
