from django.contrib import admin
from .models import App, AppTier, AppFeature, AppScreenshot, KBArticle

class AppTierInline(admin.TabularInline):
    model = AppTier
    extra = 1

class AppFeatureInline(admin.TabularInline):
    model = AppFeature
    extra = 3

class AppScreenshotInline(admin.TabularInline):
    model = AppScreenshot
    extra = 2

@admin.register(App)
class AppAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'is_active')
    prepopulated_fields = {'slug': ('name',)} # Automatically generates slug from name
    inlines = [AppTierInline, AppFeatureInline, AppScreenshotInline]

@admin.register(KBArticle)
class KBAdmin(admin.ModelAdmin):
    list_display = ('title', 'app', 'category')
    list_filter = ('app', 'category')