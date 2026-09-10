from django.contrib import admin
from .models import Skill, PracticeLog, UserStreak

@admin.register(Skill)
class SkillAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'user', 'created_at')
    search_fields = ('name', 'category')
    list_filter = ('category', 'created_at')
    ordering = ('-created_at',)

@admin.register(PracticeLog)
class PracticeLogAdmin(admin.ModelAdmin):
    list_display = ('skill', 'date', 'quality', 'post_practice_retention')
    list_filter = ('quality', 'date')
    search_fields = ('skill__name',)

admin.site.site_header = "PSRT Admin Panel"
admin.site.site_title = "PSRT Admin"
admin.site.index_title = "Welcome to PSRT Dashboard"

@admin.register(UserStreak)
class UserStreakAdmin(admin.ModelAdmin):
    list_display = ['user', 'current_streak', 'longest_streak', 'last_activity_date', 'active_streak']
    list_filter = ['user']
    search_fields = ['user__username']
    readonly_fields = ['current_streak', 'longest_streak', 'last_activity_date']