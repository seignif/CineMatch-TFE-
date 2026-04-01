from django.contrib import admin
from .models import Swipe, Match, PlannedOuting, Review


@admin.register(Swipe)
class SwipeAdmin(admin.ModelAdmin):
    list_display = ['from_user', 'to_user', 'action', 'created_at']
    list_filter = ['action']
    search_fields = ['from_user__email', 'to_user__email']
    raw_id_fields = ['from_user', 'to_user']


@admin.register(Match)
class MatchAdmin(admin.ModelAdmin):
    list_display = ['user1', 'user2', 'score_compatibilite', 'status', 'created_at']
    list_filter = ['status']
    search_fields = ['user1__email', 'user2__email']
    raw_id_fields = ['user1', 'user2']
    readonly_fields = ['score_compatibilite', 'raisons_compatibilite', 'ai_generated_reasons', 'ai_match_message', 'created_at']


@admin.register(PlannedOuting)
class PlannedOutingAdmin(admin.ModelAdmin):
    list_display = ['match', 'proposer', 'seance', 'status', 'created_at']
    list_filter = ['status']
    raw_id_fields = ['match', 'proposer', 'seance']


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ['outing', 'reviewer', 'rating', 'created_at']
    list_filter = ['rating']
    raw_id_fields = ['outing', 'reviewer']
