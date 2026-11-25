from django.contrib import admin

from .models import Resource


@admin.register(Resource)
class ResourceAdmin(admin.ModelAdmin):
    list_display = ("name", "category", "status", "owner", "created_at")
    list_filter = ("status", "category")
    search_fields = ("name", "description", "owner__username")
    readonly_fields = ("created_at", "updated_at")
