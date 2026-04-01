from django.urls import path
from .views import CandidatesView, SwipeView, MatchListView, MatchDetailView

urlpatterns = [
    path('candidates/', CandidatesView.as_view(), name='matching-candidates'),
    path('swipe/', SwipeView.as_view(), name='matching-swipe'),
    path('matches/', MatchListView.as_view(), name='matching-matches'),
    path('matches/<int:pk>/', MatchDetailView.as_view(), name='matching-match-detail'),
]
