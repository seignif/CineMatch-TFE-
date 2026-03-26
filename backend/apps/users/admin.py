from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from apps.users.models import ProfileFilmSignature, User, UserProfile


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = ['email', 'username', 'first_name', 'last_name', 'city', 'is_active', 'date_joined']
    list_filter = ['is_active', 'is_staff', 'city']
    search_fields = ['email', 'username', 'first_name', 'last_name']
    ordering = ['-date_joined']
    fieldsets = UserAdmin.fieldsets + (
        ('Infos supplementaires', {'fields': ('date_of_birth', 'city')}),
    )


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'mood', 'city_display', 'rgpd_consent']
    list_filter = ['mood', 'rgpd_consent']
    search_fields = ['user__email', 'user__first_name', 'user__last_name']

    def city_display(self, obj):
        return obj.user.city
    city_display.short_description = 'Ville'


@admin.register(ProfileFilmSignature)
class ProfileFilmSignatureAdmin(admin.ModelAdmin):
    list_display = ['profile', 'film', 'order', 'added_at']
    list_filter = ['added_at']
    search_fields = ['profile__user__email', 'film__title']
    ordering = ['profile', 'order']
