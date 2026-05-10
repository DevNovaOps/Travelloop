from django.contrib import admin
from .models import (
    User, Trip, ItinerarySection, Activity,
    PackingCategory, PackingItem, TripNote,
    CommunityPost, PostComment, Destination,
    Notification, AuditLog,
)


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ['first_name', 'last_name', 'email', 'role', 'is_active', 'created_at']
    list_filter = ['role', 'is_active']
    search_fields = ['first_name', 'last_name', 'email']


@admin.register(Trip)
class TripAdmin(admin.ModelAdmin):
    list_display = ['name', 'destination', 'mood', 'status', 'created_by', 'start_date', 'end_date']
    list_filter = ['status', 'mood']
    search_fields = ['name', 'destination']


@admin.register(ItinerarySection)
class ItinerarySectionAdmin(admin.ModelAdmin):
    list_display = ['title', 'trip', 'start_date', 'end_date', 'budget']


@admin.register(Activity)
class ActivityAdmin(admin.ModelAdmin):
    list_display = ['name', 'section', 'day_number', 'expense', 'icon']
    list_filter = ['icon', 'day_number']


@admin.register(PackingCategory)
class PackingCategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'trip', 'icon']


@admin.register(PackingItem)
class PackingItemAdmin(admin.ModelAdmin):
    list_display = ['text', 'category', 'is_packed']
    list_filter = ['is_packed']


@admin.register(TripNote)
class TripNoteAdmin(admin.ModelAdmin):
    list_display = ['title', 'trip', 'day_label', 'stop', 'created_at']
    search_fields = ['title', 'body']


@admin.register(CommunityPost)
class CommunityPostAdmin(admin.ModelAdmin):
    list_display = ['author', 'trip_name', 'likes', 'comments_count', 'created_at']


@admin.register(PostComment)
class PostCommentAdmin(admin.ModelAdmin):
    list_display = ['author', 'post', 'created_at']


@admin.register(Destination)
class DestinationAdmin(admin.ModelAdmin):
    list_display = ['name', 'category', 'rating']
    list_filter = ['category']
    search_fields = ['name']


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ['title', 'user', 'is_read', 'created_at']
    list_filter = ['is_read']


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ['action', 'user', 'ip_address', 'created_at']
    readonly_fields = ['user', 'action', 'details', 'ip_address', 'created_at']
