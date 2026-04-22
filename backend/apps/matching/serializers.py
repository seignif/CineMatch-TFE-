from rest_framework import serializers
from apps.users.models import User, UserProfile
from .models import Swipe, Match, PlannedOuting, Review, Group, GroupMember, GroupMessage, FilmVote


class PublicProfileSerializer(serializers.ModelSerializer):
    films_signature = serializers.SerializerMethodField()

    class Meta:
        model = UserProfile
        fields = ['bio', 'profile_picture', 'mood', 'genre_preferences', 'films_signature']

    def get_films_signature(self, obj):
        return [
            {'id': f.id, 'title': f.title, 'poster_url': f.poster_url}
            for f in obj.films_signature.all()
        ]


class CandidateSerializer(serializers.ModelSerializer):
    profile = PublicProfileSerializer(read_only=True)
    score = serializers.IntegerField(read_only=True)
    reasons = serializers.ListField(child=serializers.CharField(), read_only=True)
    superliked_me = serializers.BooleanField(read_only=True)

    class Meta:
        model = User
        fields = ['id', 'first_name', 'city', 'date_of_birth', 'profile', 'score', 'reasons', 'superliked_me']


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
        read_only_fields = ['id', 'outing', 'created_at']

    def validate_rating(self, value):
        if value not in range(1, 6):
            raise serializers.ValidationError('La note doit être entre 1 et 5.')
        return value


# ---------------------------------------------------------------------------
# Groupes (US-041 / US-042 / US-043)
# ---------------------------------------------------------------------------

class GroupMemberSerializer(serializers.ModelSerializer):
    user_info = serializers.SerializerMethodField()

    class Meta:
        model = GroupMember
        fields = ['id', 'user_info', 'role', 'status', 'joined_at']

    def get_user_info(self, obj):
        u = obj.user
        profile = getattr(u, 'profile', None)
        pic = None
        if profile and profile.profile_picture:
            request = self.context.get('request')
            pic = request.build_absolute_uri(profile.profile_picture.url) if request else profile.profile_picture.url
        return {
            'id': u.id,
            'first_name': u.first_name,
            'city': u.city,
            'profile_picture': pic,
        }


class GroupMessageSerializer(serializers.ModelSerializer):
    sender_name = serializers.CharField(source='sender.first_name', read_only=True)
    sender_id = serializers.IntegerField(source='sender.id', read_only=True)

    class Meta:
        model = GroupMessage
        fields = ['id', 'sender_id', 'sender_name', 'content', 'is_system', 'created_at']


class FilmVoteSerializer(serializers.ModelSerializer):
    film_title = serializers.CharField(source='film.title', read_only=True)
    film_poster = serializers.CharField(source='film.poster_url', read_only=True)
    voter_name = serializers.CharField(source='voter.first_name', read_only=True)

    class Meta:
        model = FilmVote
        fields = ['id', 'film', 'film_title', 'film_poster', 'voter_name', 'vote']


class GroupSerializer(serializers.ModelSerializer):
    members_info = GroupMemberSerializer(source='groupmember_set', many=True, read_only=True)
    active_member_count = serializers.SerializerMethodField()
    last_message = serializers.SerializerMethodField()
    votes_summary = serializers.SerializerMethodField()
    is_creator = serializers.SerializerMethodField()
    chosen_film_info = serializers.SerializerMethodField()
    my_invitation_status = serializers.SerializerMethodField()
    my_votes = serializers.SerializerMethodField()

    class Meta:
        model = Group
        fields = [
            'id', 'name', 'status', 'creator',
            'members_info', 'active_member_count',
            'last_message', 'votes_summary',
            'chosen_film_info', 'is_creator',
            'my_invitation_status', 'my_votes',
            'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'creator', 'status', 'created_at', 'updated_at']

    def get_active_member_count(self, obj):
        return obj.groupmember_set.filter(status='accepted').count()

    def get_last_message(self, obj):
        msg = obj.messages.order_by('-created_at').first()
        if not msg:
            return None
        return {
            'content': msg.content,
            'sender_name': msg.sender.first_name,
            'created_at': msg.created_at.isoformat(),
            'is_system': msg.is_system,
        }

    def get_votes_summary(self, obj):
        from collections import defaultdict
        votes = FilmVote.objects.filter(group=obj).select_related('film')
        summary = defaultdict(lambda: {'up': 0, 'down': 0, 'film': None})
        for vote in votes:
            summary[vote.film_id]['film'] = {
                'id': vote.film.id,
                'title': vote.film.title,
                'poster_url': vote.film.poster_url,
            }
            summary[vote.film_id][vote.vote] += 1
        return list(summary.values())

    def get_is_creator(self, obj):
        request = self.context.get('request')
        return bool(request and obj.creator == request.user)

    def get_chosen_film_info(self, obj):
        if not obj.chosen_film:
            return None
        return {
            'id': obj.chosen_film.id,
            'title': obj.chosen_film.title,
            'poster_url': obj.chosen_film.poster_url,
        }

    def get_my_invitation_status(self, obj):
        request = self.context.get('request')
        if not request:
            return None
        try:
            member = GroupMember.objects.get(group=obj, user=request.user)
            return member.status
        except GroupMember.DoesNotExist:
            return None

    def get_my_votes(self, obj):
        request = self.context.get('request')
        if not request:
            return {}
        votes = FilmVote.objects.filter(group=obj, voter=request.user)
        return {str(v.film_id): v.vote for v in votes}
