from django.contrib import admin
from .models import Challenge

@admin.register(Challenge)
class ChallengeAdmin(admin.ModelAdmin):
    list_display = ("name", "description", "challenge_type", "members")
    search_fields = ("name", "description", "challenge_type")