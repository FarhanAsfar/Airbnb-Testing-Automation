from django.contrib import admin
from automation.models import TestResult


@admin.register(TestResult)
class TestResultAdmin(admin.ModelAdmin):
    list_display = ('testCase', 'passed', 'url', 'comment','created_at')
    list_filter = ('passed',)
    search_fields = ('testCase', 'comment')
    readonly_fields = ('testCase', 'url', 'passed', 'comment', 'created_at')
    ordering = ('-created_at',)
