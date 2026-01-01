from django.contrib import admin

# Register your models here.
from .models import Movie, StreamingLink, WatchHistory, UserWatchlist, UserFavorite


@admin.register(Movie)
class MovieAdmin(admin.ModelAdmin):
    list_display = ("title", "year")
    search_fields = ("title",)
    list_filter = ("year",)


@admin.register(StreamingLink)
class MovieAdmin(admin.ModelAdmin):
    list_display = ("movie", "quality")
    search_fields = ("movie",)
    list_filter = ("quality",)    


@admin.register(WatchHistory)
class WatchHistoryAdmin(admin.ModelAdmin):
    list_display = ("user", "movie", "progress", "current_time", "season", "episode", "last_watched")
    search_fields = ("user", "movie")
    list_filter = ("progress", "current_time", "season", "episode", "last_watched")

@admin.register(UserWatchlist)
class UserWatchlistAdmin(admin.ModelAdmin):
    list_display = ("user", "movie", "added_at")
    search_fields = ("user", "movie")
    list_filter = ("added_at",) 


@admin.register(UserFavorite)
class UserFavoriteAdmin(admin.ModelAdmin):
    list_display = ("user", "movie", "added_at")
    search_fields = ("user", "movie")
    list_filter = ("added_at",) 


    