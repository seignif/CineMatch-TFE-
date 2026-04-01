from rest_framework import serializers
from apps.users.models import User, UserProfile
from .models import Swipe, Match


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
