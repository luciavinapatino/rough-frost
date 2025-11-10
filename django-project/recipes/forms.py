"""
Forms for recipe creation and management.

This module provides form classes for creating and editing recipes,
including handling of tags (comma-separated) and steps (newline-separated).
"""
from django import forms
from django.contrib.auth.models import User

from .models import Recipe, Tag


class RecipeForm(forms.ModelForm):
    """
    Form for creating and editing recipes.
    
    This form extends Django's ModelForm for the Recipe model and adds two additional
    custom fields for user convenience:
    - tags_csv: Allows users to input tags as comma-separated values instead of 
      selecting from a multi-select dropdown
    - steps_text: Allows users to input cooking steps as newline-separated text 
      instead of creating individual Step objects
    
    The form handles parsing of comma-separated tags and newline-separated steps,
    which are then converted to actual database objects by the view.
    """
    
    tags_csv = forms.CharField(
        required=False,
        label='Tags (comma-separated)',
        widget=forms.TextInput(attrs={'placeholder': 'vegan, dessert, quick-meal'}),
        help_text='Enter tags separated by commas. Tags will be created if they don\'t exist.'
    )
    
    steps_text = forms.CharField(
        required=False,
        label='Steps (one per line)',
        widget=forms.Textarea(attrs={'rows': 6, 'placeholder': '1. Preheat oven\n2. Mix ingredients\n3. Bake'}),
        help_text='Enter each cooking step on a new line. Steps will be numbered automatically.'
    )

    class Meta:
        model = Recipe
        fields = ['title', 'description', 'image_url']
        help_texts = {
            'title': 'The name of your recipe',
            'description': 'A brief description of what this recipe is',
            'image_url': 'Optional: URL to an image of the finished dish',
        }

    def clean_tags_csv(self):
        """
        Validate and parse comma-separated tag input.
        
        Strips whitespace from each tag and filters out empty strings.
        Converts the comma-separated string into a list of individual tag names.
        
        Returns:
            list: Cleaned list of tag name strings
        """
        data = self.cleaned_data.get('tags_csv', '')
        # Normalize: split by comma, strip whitespace, filter empty strings
        tag_names = [t.strip() for t in data.split(',') if t.strip()]
        return tag_names
    
    def clean_title(self):
        """
        Validate recipe title field.
        
        Ensures the title is not empty after stripping whitespace.
        
        Returns:
            str: Cleaned title
            
        Raises:
            ValidationError: If title is empty or only whitespace
        """
        title = self.cleaned_data.get('title', '').strip()
        if not title:
            raise forms.ValidationError('Recipe title cannot be empty.')
        return title
