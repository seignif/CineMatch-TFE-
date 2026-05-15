"""US-039 : Système de badges automatique thème cinéma vintage."""

BADGE_DEFINITIONS = {
    'clap_debut': {
        'id': 'clap_debut',
        'name': 'Clap de Début',
        'description': 'Ton premier match CineMatch !',
        'svg_id': 'badge_clap',
        'color_primary': '#E63946',
        'color_secondary': '#FFD700',
        'tier': 'bronze',
    },
    'montee_marches': {
        'id': 'montee_marches',
        'name': 'Montée des Marches',
        'description': '5 matchs réalisés — le tapis rouge t\'attend !',
        'svg_id': 'badge_star',
        'color_primary': '#FFD700',
        'color_secondary': '#E63946',
        'tier': 'silver',
    },
    'role_principal': {
        'id': 'role_principal',
        'name': 'Rôle Principal',
        'description': 'Profil 100% complété — tu es la star !',
        'svg_id': 'badge_masks',
        'color_primary': '#9B59B6',
        'color_secondary': '#FFD700',
        'tier': 'silver',
    },
    'palme_dor': {
        'id': 'palme_dor',
        'name': 'Palme d\'Or',
        'description': 'Note moyenne ≥ 4.5 avec au moins 3 avis',
        'svg_id': 'badge_trophy',
        'color_primary': '#FFD700',
        'color_secondary': '#0A0A0F',
        'tier': 'gold',
    },
    'premiere_seance': {
        'id': 'premiere_seance',
        'name': 'Première Séance',
        'description': 'Ta première sortie ciné organisée !',
        'svg_id': 'badge_popcorn',
        'color_primary': '#E63946',
        'color_secondary': '#FFF8E7',
        'tier': 'bronze',
    },
    'abonne_salle': {
        'id': 'abonne_salle',
        'name': 'Abonné de la Salle',
        'description': '5 sorties ciné réalisées',
        'svg_id': 'badge_reel',
        'color_primary': '#2ECC71',
        'color_secondary': '#FFD700',
        'tier': 'silver',
    },
    'critique_officiel': {
        'id': 'critique_officiel',
        'name': 'Critique Officiel',
        'description': '5 avis laissés après vos sorties',
        'svg_id': 'badge_camera',
        'color_primary': '#3498DB',
        'color_secondary': '#FFD700',
        'tier': 'silver',
    },
}


class BadgeService:

    @staticmethod
    def check_and_award_badges(user) -> list:
        """Vérifie et attribue les badges mérités. Retourne les nouveaux badges."""
        profile = user.profile
        current_badges = set(profile.badges or [])
        new_badges = []

        from django.db.models import Q
        from apps.matching.models import Match, PlannedOuting, Review

        match_count = Match.objects.filter(
            Q(user1=user) | Q(user2=user), status='active'
        ).count()

        outing_count = PlannedOuting.objects.filter(
            Q(proposer=user) | Q(match__user1=user) | Q(match__user2=user),
            status__in=['confirmed', 'completed']
        ).distinct().count()

        reviews = list(Review.objects.filter(reviewed=user))
        review_count = len(reviews)
        avg_rating = (
            sum(r.rating for r in reviews) / review_count
            if review_count > 0 else 0
        )
        reviews_given = Review.objects.filter(reviewer=user).count()

        checks = {
            'clap_debut': match_count >= 1,
            'montee_marches': match_count >= 5,
            'role_principal': BadgeService._is_profile_complete(profile),
            'palme_dor': review_count >= 3 and avg_rating >= 4.5,
            'premiere_seance': outing_count >= 1,
            'abonne_salle': outing_count >= 5,
            'critique_officiel': reviews_given >= 5,
        }

        for badge_id, earned in checks.items():
            if earned and badge_id not in current_badges:
                current_badges.add(badge_id)
                new_badges.append(BADGE_DEFINITIONS[badge_id])

        if new_badges:
            profile.badges = list(current_badges)
            profile.save(update_fields=['badges'])

        return new_badges

    @staticmethod
    def _is_profile_complete(profile) -> bool:
        return bool(
            profile.bio and
            profile.mood and
            profile.genre_preferences and
            profile.films_signature.exists()
        )

    @staticmethod
    def get_reputation_score(user) -> dict:
        from apps.matching.models import Review
        reviews = list(Review.objects.filter(reviewed=user))
        count = len(reviews)

        if count == 0:
            return {'score': None, 'count': 0, 'label': 'Nouveau', 'would_go_again_pct': None}

        avg = sum(r.rating for r in reviews) / count
        would_go_again_pct = int(
            sum(1 for r in reviews if r.would_go_again) / count * 100
        )

        if count < 3:
            label = 'Nouveau'
        elif avg >= 4.5:
            label = 'Excellent'
        elif avg >= 4.0:
            label = 'Très bien'
        elif avg >= 3.0:
            label = 'Bien'
        else:
            label = 'Moyen'

        return {
            'score': round(avg, 1) if count >= 3 else None,
            'count': count,
            'label': label,
            'would_go_again_pct': would_go_again_pct if count >= 3 else None,
        }

    @staticmethod
    def get_all_badges_info(user) -> list:
        earned = set(user.profile.badges or [])
        return [
            {**badge_def, 'earned': badge_id in earned}
            for badge_id, badge_def in BADGE_DEFINITIONS.items()
        ]
