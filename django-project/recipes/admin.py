"""
Django admin configuration for recipe models.

Registers Recipe, Step, Tag, and Favorite models with custom admin classes
to provide an intuitive interface for managing recipes and related data.
"""
from django.contrib import admin
from .models import Recipe, Step, Tag, Favorite, ABTestImpression, ABTestClick


@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    """
    Admin interface for Recipe model.
    
    Features:
        - Display: title, author, creation date
        - Filtering: by creation date and tags
        - Search: by title and description
        - Many-to-many: improved tag selection UI via filter_horizontal
    """
    list_display = ['title', 'author', 'created_at']
    list_filter = ['created_at', 'tags']
    search_fields = ['title', 'description']
    filter_horizontal = ['tags']  # Better UX for many-to-many tag selection
admin.site.register(ABTestImpression)
admin.site.register(ABTestClick)


@admin.register(Step)
class StepAdmin(admin.ModelAdmin):
    """
    Admin interface for Step model.
    
    Features:
        - Display: recipe, step number, instruction text
        - Filtering: by recipe
        - Ordering: by recipe and step number
    """
    list_display = ['recipe', 'step_number', 'instruction_text']
    list_filter = ['recipe']
    ordering = ['recipe', 'step_number']


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    """
    Admin interface for Tag model.
    
    Features:
        - Display: tag name
        - Search: by tag name
        - Ordering: alphabetical (default)
    """
    list_display = ['name']
    search_fields = ['name']


@admin.register(Favorite)
class FavoriteAdmin(admin.ModelAdmin):
    """
    Admin interface for Favorite model.
    
    Features:
        - Display: user, recipe, creation date
        - Filtering: by creation date
        - Search: by username and recipe title
    """
    list_display = ['user', 'recipe', 'created_at']
    list_filter = ['created_at']
    search_fields = ['user__username', 'recipe__title']
