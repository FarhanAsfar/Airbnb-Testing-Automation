from django.contrib import admin
from automation.models import TestResult, Listing


@admin.register(TestResult)
class TestResultAdmin(admin.ModelAdmin):
    list_display = ('testCase', 'passed', 'url', 'comment','created_at')
    list_filter = ('passed',)
    search_fields = ('testCase', 'comment')
    readonly_fields = ('testCase', 'url', 'passed', 'comment', 'created_at')
    ordering = ('-created_at',)

@admin.register(Listing)
class ListingAdmin(admin.ModelAdmin):
    list_display = ('title', 'price', 'search_url', 'img_url','location','checkin', 'checkout', 'guests','created_at')
    list_filter = ('location',)
    search_fields = ('title', 'location')
    readonly_fields = ('price', 'search_url', 'img_url', 'title', 'created_at')
    ordering = ('-created_at',)