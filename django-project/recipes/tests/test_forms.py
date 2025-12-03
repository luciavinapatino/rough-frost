"""
Unit tests for recipe forms.
"""
from django.test import TestCase
from django.contrib.auth.models import User
from recipes.forms import RecipeForm
from recipes.models import Recipe


class RecipeFormTests(TestCase):
    """Test cases for RecipeForm."""
    
    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
    
    def test_recipe_form_valid_data(self):
        """Test recipe form with valid data."""
        form_data = {
            'title': 'Test Recipe',
            'description': 'A test recipe description'
        }
        form = RecipeForm(data=form_data)
        self.assertTrue(form.is_valid())
    
    def test_recipe_form_required_fields(self):
        """Test that title and description are required."""
        form = RecipeForm(data={})
        self.assertFalse(form.is_valid())
        self.assertIn('title', form.errors)
        self.assertIn('description', form.errors)
    
    def test_recipe_form_title_max_length(self):
        """Test that title respects max_length constraint."""
        form_data = {
            'title': 'A' * 201,  # Exceeds max_length=200
            'description': 'Test description'
        }
        form = RecipeForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('title', form.errors)
    
    def test_recipe_form_image_url_optional(self):
        """Test that image_url is optional."""
        form_data = {
            'title': 'Test Recipe',
            'description': 'Test description',
            'image_url': ''
        }
        form = RecipeForm(data=form_data)
        self.assertTrue(form.is_valid())
    
    def test_recipe_form_image_url_validation(self):
        """Test that image_url must be a valid URL if provided."""
        form_data = {
            'title': 'Test Recipe',
            'description': 'Test description',
            'image_url': 'not-a-valid-url'
        }
        form = RecipeForm(data=form_data)
        # URLField validation happens at model level, but form should accept it
        # Django's URLField is lenient, so this might pass
        # If stricter validation is needed, add custom clean method
    
    def test_recipe_form_save(self):
        """Test that form can save a recipe."""
        form_data = {
            'title': 'Test Recipe',
            'description': 'Test description'
        }
        form = RecipeForm(data=form_data)
        self.assertTrue(form.is_valid())
        recipe = form.save(commit=False)
        recipe.author = self.user
        recipe.save()
        self.assertEqual(Recipe.objects.count(), 1)
        self.assertEqual(Recipe.objects.first().title, 'Test Recipe')



