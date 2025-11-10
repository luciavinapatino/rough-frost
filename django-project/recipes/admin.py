from django.contrib import admin
from .models import Recipe, Step, Tag, Favorite


@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    """
    Admin interface for Recipe model.
    Makes it easy to view and manage recipes in the Django admin panel.
    """
    list_display = ['title', 'author', 'created_at']
    list_filter = ['created_at', 'tags']
    search_fields = ['title', 'description']
    filter_horizontal = ['tags']  # Better UI for selecting tags


@admin.register(Step)
class StepAdmin(admin.ModelAdmin):
    """
    Admin interface for Step model.
    Shows recipe steps in a clear, organized way.
    """
    list_display = ['recipe', 'step_number', 'instruction_text']
    list_filter = ['recipe']
    ordering = ['recipe', 'step_number']


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    """
    Admin interface for Tag model.
    Simple interface for managing recipe tags.
    """
    list_display = ['name']
    search_fields = ['name']


@admin.register(Favorite)
class FavoriteAdmin(admin.ModelAdmin):
    """
    Admin interface for Favorite model.
    View which users have favorited which recipes.
    """
    list_display = ['user', 'recipe', 'created_at']
    list_filter = ['created_at']
    search_fields = ['user__username', 'recipe__title']
