from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAdminUser
from rest_framework.response import Response


def health_check(request):
    return JsonResponse({"status": "ok", "version": "1.0.0"})


@api_view(['POST'])
@permission_classes([IsAdminUser])
def admin_sync_kinepolis(request):
    from apps.films.tasks import sync_kinepolis_all
    task = sync_kinepolis_all.delay()
    return Response({"status": "started", "task_id": task.id})


urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/health/', health_check, name='health-check'),
    path('api/admin/sync-kinepolis/', admin_sync_kinepolis, name='admin-sync-kinepolis'),
    path('api/', include('api.urls')),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
