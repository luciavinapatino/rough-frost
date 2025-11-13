"""
Database models for the recipes application.

This module defines the core data models:
    - Recipe: Main recipe entity with title, description, author, and image
    - Tag: Labels for categorizing recipes (vegan, dessert, gluten-free, etc.)
    - Step: Numbered cooking instructions for recipes
    - Favorite: User favorites with personal notes about recipes

Relationships:
    - Recipe has one author (ForeignKey to User)
    - Recipe can have many tags (ManyToMany)
    - Recipe can have many steps (ForeignKey from Step)
    - Recipe can be favorited by many users (ForeignKey from Favorite)
"""
from django.db import models
from django.contrib.auth.models import User


class Recipe(models.Model):
    """
    Recipe model - stores core recipe information.
    
    Each recipe has a title, description, author, and optional image.
    Recipes can have multiple steps (instructions) and multiple tags (categories).
    """
    title = models.CharField(
        max_length=200,
        help_text="The name of the recipe (e.g., 'Chocolate Chip Cookies')"
    )
    description = models.TextField(
        help_text="A brief description of the recipe"
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        help_text="The user who created this recipe"
    )
    image_url = models.URLField(
        blank=True,
        null=True,
        help_text="URL to an image of the finished recipe (optional)"
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        help_text="When this recipe was first created"
    )
    tags = models.ManyToManyField(
        'Tag',
        blank=True,
        help_text="Tags that categorize this recipe (e.g., vegan, dessert, gluten-free)"
    )
    ingredients = models.TextField(
        blank=True,
        help_text="Recipe ingredients, one per line"
    )

    class Meta:
        ordering = ['-created_at']  # Newest recipes first
    
    def __str__(self):
        return self.title


class Tag(models.Model):
    """
    Tag model - labels for categorizing recipes.
    
    Examples: "vegan", "dessert", "gluten-free", "quick-meal"
    A recipe can have many tags, and a tag can apply to many recipes.
    """
    name = models.CharField(
        max_length=50,
        unique=True,
        help_text="The tag name (e.g., 'vegan', 'dessert', 'gluten-free')"
    )
    
    class Meta:
        ordering = ['name']  # Alphabetical order
    
    def __str__(self):
        return self.name


class Step(models.Model):
    """
    Step model - numbered cooking instructions for recipes.
    
    Each recipe can have multiple steps. Steps are ordered by step_number.
    Example: Step 1 might be "Preheat oven to 350°F", Step 2 might be "Mix ingredients", etc.
    """
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='steps',
        help_text="The recipe this step belongs to"
    )
    step_number = models.PositiveIntegerField(
        help_text="The order of this step (1, 2, 3, etc.)"
    )
    instruction_text = models.TextField(
        help_text="The instruction for this step"
    )
    
    class Meta:
        ordering = ['step_number']  # Steps in order
        unique_together = ['recipe', 'step_number']  # Can't have duplicate step numbers for same recipe
    
    def __str__(self):
        return f"{self.recipe.title} - Step {self.step_number}"


class Favorite(models.Model):
    """
    Favorite model - links users to recipes they've saved as favorites.
    
    This creates a many-to-many relationship between Users and Recipes.
    Users can save recipes to their favorites list and add personal notes.
    """
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='favorites',
        help_text="The user who favorited this recipe"
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='favorited_by',
        help_text="The recipe that was favorited"
    )
    notes = models.TextField(
        blank=True,
        help_text="Personal notes about this recipe (e.g., 'I prefer to replace cilantro with parsley')"
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        help_text="When this recipe was added to favorites"
    )
    
    class Meta:
        unique_together = ['user', 'recipe']  # A user can only favorite a recipe once
        ordering = ['-created_at']  # Most recently favorited first
    
    def __str__(self):
        return f"{self.user.username} favorited {self.recipe.title}"
