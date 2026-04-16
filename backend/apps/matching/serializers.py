from rest_framework import serializers
from apps.users.models import User, UserProfile
from .models import Swipe, Match, PlannedOuting, Review


class PublicProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserProfile
        fields = ['bio', 'profile_picture', 'mood', 'genre_preferences']


class CandidateSerializer(serializers.ModelSerializer):
    profile = PublicProfileSerializer(read_only=True)
    score = serializers.IntegerField(read_only=True)
    reasons = serializers.ListField(child=serializers.CharField(), read_only=True)

    class Meta:
        model = User
        fields = ['id', 'first_name', 'city', 'date_of_birth', 'profile', 'score', 'reasons']


class MatchSerializer(serializers.ModelSerializer):
    other_user = serializers.SerializerMethodField()

    class Meta:
        model = Match
        fields = [
            'id', 'other_user', 'score_compatibilite',
            'raisons_compatibilite', 'ai_generated_reasons',
            'ai_match_message', 'status', 'created_at',
        ]

    def get_other_user(self, obj):
        request_user = self.context['request'].user
        other = obj.user2 if obj.user1 == request_user else obj.user1
        return {
            'id': other.id,
            'first_name': other.first_name,
            'city': other.city,
            'profile': PublicProfileSerializer(other.profile).data,
        }


class SwipeSerializer(serializers.Serializer):
    to_user_id = serializers.IntegerField()
    action = serializers.ChoiceField(choices=['like', 'pass', 'superlike'])


class PlannedOutingSeanceSerializer(serializers.Serializer):
    """Séance simplifiée pour les sorties — lecture seule."""
    id = serializers.IntegerField()
    film_title = serializers.SerializerMethodField()
    film_poster = serializers.SerializerMethodField()
    cinema_name = serializers.SerializerMethodField()
    cinema_kinepolis_id = serializers.SerializerMethodField()
    showtime = serializers.DateTimeField()
    language = serializers.CharField()
    hall = serializers.IntegerField(allow_null=True)
    booking_url = serializers.URLField()
    is_sold_out = serializers.BooleanField()
    raw_attributes = serializers.CharField()

    def get_film_title(self, obj):
        return obj.film.title if obj.film else ''

    def get_film_poster(self, obj):
        return obj.film.poster_url if obj.film else ''

    def get_cinema_name(self, obj):
        return obj.cinema.name if obj.cinema else ''

    def get_cinema_kinepolis_id(self, obj):
        return obj.cinema.kinepolis_id if obj.cinema else ''


class PlannedOutingSerializer(serializers.ModelSerializer):
    seance = PlannedOutingSeanceSerializer(read_only=True)
    seance_id = serializers.IntegerField(write_only=True, required=False, allow_null=True)
    proposer_info = serializers.SerializerMethodField()
    partner_info = serializers.SerializerMethodField()
    is_upcoming = serializers.SerializerMethodField()
    user_is_proposer = serializers.SerializerMethodField()

    class Meta:
        model = PlannedOuting
        fields = [
            'id', 'match', 'status',
            'seance', 'seance_id',
            'proposer_info', 'partner_info',
            'meeting_place', 'meeting_time',
            'proposer_booked', 'partner_booked',
            'proposal_message',
            'is_upcoming', 'user_is_proposer',
            'created_at', 'updated_at',
        ]
        read_only_fields = [
            'id', 'status', 'proposer_booked', 'partner_booked',
            'created_at', 'updated_at',
        ]

    def _user_info(self, user):
        pic = None
        if hasattr(user, 'profile') and user.profile.profile_picture:
            request = self.context.get('request')
            pic = request.build_absolute_uri(user.profile.profile_picture.url) if request else user.profile.profile_picture.url
        return {'id': user.id, 'first_name': user.first_name, 'profile_picture': pic}

    def get_proposer_info(self, obj):
        return self._user_info(obj.proposer)

    def get_partner_info(self, obj):
        return self._user_info(obj.get_partner())

    def get_is_upcoming(self, obj):
        return obj.is_upcoming()

    def get_user_is_proposer(self, obj):
        request = self.context.get('request')
        return bool(request and obj.proposer == request.user)


class ReviewSerializer(serializers.ModelSerializer):
    class Meta:
        model = Review
        fields = ['id', 'outing', 'rating', 'would_go_again', 'comment', 'created_at']
        read_only_fields = ['id', 'created_at']

    def validate_rating(self, value):
        if value not in range(1, 6):
            raise serializers.ValidationError('La note doit être entre 1 et 5.')
        return value
