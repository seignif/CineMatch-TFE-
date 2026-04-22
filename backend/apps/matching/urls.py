from django.urls import path
from .views import (
    CandidatesView, SwipeView, MatchListView, MatchDetailView,
    OutingListCreateView, OutingDetailView, OutingConfirmView,
    OutingCancelView, OutingMarkBookedView, UpcomingOutingsView,
    OutingCompleteView, ReviewCreateView,
    GroupListCreateView, GroupInvitationsView, GroupRespondInvitationView,
    GroupDetailView, GroupLeaveView, GroupInviteMembersView, GroupMessagesView,
    FilmVoteView, GroupChooseFilmView,
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

    # Avis + statut terminé (US-038)
    path('outings/<int:pk>/complete/', OutingCompleteView.as_view(), name='outing-complete'),
    path('outings/<int:pk>/review/', ReviewCreateView.as_view(), name='outing-review'),

    # Groupes (US-041 / US-042 / US-043)
    path('groups/', GroupListCreateView.as_view(), name='groups'),
    path('groups/invitations/', GroupInvitationsView.as_view(), name='group-invitations'),
    path('groups/<int:pk>/', GroupDetailView.as_view(), name='group-detail'),
    path('groups/<int:pk>/respond/', GroupRespondInvitationView.as_view(), name='group-respond'),
    path('groups/<int:pk>/leave/', GroupLeaveView.as_view(), name='group-leave'),
    path('groups/<int:pk>/invite/', GroupInviteMembersView.as_view(), name='group-invite'),
    path('groups/<int:pk>/messages/', GroupMessagesView.as_view(), name='group-messages'),
    path('groups/<int:pk>/vote/', FilmVoteView.as_view(), name='group-vote'),
    path('groups/<int:pk>/choose-film/', GroupChooseFilmView.as_view(), name='group-choose-film'),
]
