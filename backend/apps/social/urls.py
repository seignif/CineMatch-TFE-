from django.urls import path
from apps.social import views

urlpatterns = [
    path('posts/', views.PostListCreateView.as_view(), name='posts'),
    path('posts/<int:pk>/', views.PostDetailView.as_view(), name='post-detail'),
    path('posts/<int:pk>/like/', views.PostLikeView.as_view(), name='post-like'),
    path('posts/<int:pk>/comments/', views.PostCommentListCreateView.as_view(), name='post-comments'),
    path('comments/<int:pk>/', views.PostCommentDeleteView.as_view(), name='comment-delete'),
    path('notifications/', views.NotificationListView.as_view(), name='notifications'),
    path('notifications/unread-count/', views.UnreadNotificationCountView.as_view(), name='notif-unread'),
    path('notifications/read/', views.NotificationMarkReadView.as_view(), name='notif-read-all'),
    path('notifications/<int:pk>/read/', views.NotificationMarkReadView.as_view(), name='notif-read-one'),
]
