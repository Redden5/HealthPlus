from django.contrib import admin

# Register your models here.
from .models import JournalEntry


@admin.register(JournalEntry)
class JournalEntryAdmin(admin.ModelAdmin):
    list_display = ('patient', 'mood_score', 'created_at')
    search_fields = ('patient__user__username', 'patient__first_name', 'patient__last_name', 'text')
    list_filter = ('created_at', 'mood_score')