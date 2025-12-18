from django.contrib import admin

# Register your models here.
from .models import Movie, StreamingLink


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