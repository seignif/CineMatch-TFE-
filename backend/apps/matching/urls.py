from django.urls import path
from .views import (
    CandidatesView, SwipeView, MatchListView, MatchDetailView,
    OutingListCreateView, OutingDetailView, OutingConfirmView,
    OutingCancelView, OutingMarkBookedView, UpcomingOutingsView,
)

urlpatterns = [
    # Matching
    path('candidates/', CandidatesView.as_view(), name='matching-candidates'),
    path('swipe/', SwipeView.as_view(), name='matching-swipe'),
    path('matches/', MatchListView.as_view(), name='matching-matches'),
    path('matches/<int:pk>/', MatchDetailView.as_view(), name='matching-match-detail'),

    # Sorties planifiées (US-029 à US-033)
    path('outings/', OutingListCreateView.as_view(), name='outings'),
    path('outings/upcoming/', UpcomingOutingsView.as_view(), name='outings-upcoming'),
    path('outings/<int:pk>/', OutingDetailView.as_view(), name='outing-detail'),
    path('outings/<int:pk>/confirm/', OutingConfirmView.as_view(), name='outing-confirm'),
    path('outings/<int:pk>/cancel/', OutingCancelView.as_view(), name='outing-cancel'),
    path('outings/<int:pk>/booked/', OutingMarkBookedView.as_view(), name='outing-booked'),
]
