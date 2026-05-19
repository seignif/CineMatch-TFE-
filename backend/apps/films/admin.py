from django.contrib import admin
from .models import Film, Genre, Cinema, Seance, WatchedFilm


@admin.register(Seance)
class SeanceAdmin(admin.ModelAdmin):
    list_display = ('film', 'cinema', 'showtime', 'language', 'is_sold_out', 'created_at_display')
    list_filter = ('cinema', 'language', 'is_sold_out')
    search_fields = ('film__title', 'cinema__name')
    ordering = ('-showtime',)
    date_hierarchy = 'showtime'

    def created_at_display(self, obj):
        return obj.showtime
    created_at_display.short_description = 'Showtime'


@admin.register(Film)
class FilmAdmin(admin.ModelAdmin):
    list_display = ('title', 'is_future', 'tmdb_rating', 'release_date')
    list_filter = ('is_future', 'genres')
    search_fields = ('title', 'kinepolis_id')
    ordering = ('title',)


admin.site.register(Genre)
admin.site.register(Cinema)
admin.site.register(WatchedFilm)
