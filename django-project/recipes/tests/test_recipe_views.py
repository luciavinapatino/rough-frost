"""
Unit tests for recipe-related views (create, detail, list).
"""
from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from django.core.files.uploadedfile import SimpleUploadedFile
from recipes.models import Recipe, Ingredient, Step


class RecipeCreationTests(TestCase):
    """Test cases for recipe creation view."""
    
    def setUp(self):
        """Set up test data."""
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.create_url = reverse('create_recipe')
    
    def test_create_recipe_requires_login(self):
        """Test that unauthenticated users are redirected to login."""
        response = self.client.get(self.create_url)
        self.assertEqual(response.status_code, 302)
        self.assertIn('/login', response.url)
    
    def test_create_recipe_page_loads(self):
        """Test that recipe creation page loads for authenticated users."""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(self.create_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'recipes/create_recipe.html')
        self.assertIn('recipe_form', response.context)
    
    def test_create_recipe_with_valid_data(self):
        """Test creating a recipe with valid data."""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.post(self.create_url, {
            'title': 'Test Recipe',
            'description': 'A test recipe',
            'ingredient_name': ['Flour', 'Sugar'],
            'ingredient_amount': ['2 cups', '1 cup'],
            'instruction': ['Mix ingredients', 'Bake at 350°F']
        })
        # Should redirect to recipe detail page
        self.assertEqual(response.status_code, 302)
        self.assertIn('/recipes/', response.url)
        
        # Verify recipe was created
        recipe = Recipe.objects.get(title='Test Recipe')
        self.assertEqual(recipe.author, self.user)
        self.assertEqual(recipe.description, 'A test recipe')
        
        # Verify ingredients were created
        ingredients = recipe.ingredients.all()
        self.assertEqual(ingredients.count(), 2)
        self.assertEqual(ingredients[0].name, 'Flour')
        self.assertEqual(ingredients[0].amount, '2 cups')
        
        # Verify steps were created
        steps = recipe.steps.all()
        self.assertEqual(steps.count(), 2)
        self.assertEqual(steps[0].step_number, 1)
        self.assertEqual(steps[0].instruction_text, 'Mix ingredients')
        self.assertEqual(steps[1].step_number, 2)
    
    def test_create_recipe_with_image_url(self):
        """Test creating a recipe with image URL."""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.post(self.create_url, {
            'title': 'Test Recipe',
            'description': 'A test recipe',
            'image_url': 'https://example.com/image.jpg',
            'ingredient_name': ['Flour'],
            'ingredient_amount': ['2 cups'],
            'instruction': ['Mix ingredients']
        })
        self.assertEqual(response.status_code, 302)
        recipe = Recipe.objects.get(title='Test Recipe')
        self.assertEqual(recipe.image_url, 'https://example.com/image.jpg')
    
    def test_create_recipe_ignores_empty_ingredients(self):
        """Test that empty ingredient fields are ignored."""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.post(self.create_url, {
            'title': 'Test Recipe',
            'description': 'A test recipe',
            'ingredient_name': ['Flour', '', 'Sugar'],
            'ingredient_amount': ['2 cups', '', '1 cup'],
            'instruction': ['Mix ingredients']
        })
        self.assertEqual(response.status_code, 302)
        recipe = Recipe.objects.get(title='Test Recipe')
        # Should only have 2 ingredients (empty one ignored)
        self.assertEqual(recipe.ingredients.count(), 2)
    
    def test_create_recipe_ignores_empty_instructions(self):
        """Test that empty instruction fields are ignored."""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.post(self.create_url, {
            'title': 'Test Recipe',
            'description': 'A test recipe',
            'ingredient_name': ['Flour'],
            'ingredient_amount': ['2 cups'],
            'instruction': ['Mix ingredients', '', 'Bake']
        })
        self.assertEqual(response.status_code, 302)
        recipe = Recipe.objects.get(title='Test Recipe')
        # Should only have 2 steps (empty one ignored)
        self.assertEqual(recipe.steps.count(), 2)


class RecipeDetailTests(TestCase):
    """Test cases for recipe detail view."""
    
    def setUp(self):
        """Set up test data."""
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.recipe = Recipe.objects.create(
            title='Test Recipe',
            description='A test recipe',
            author=self.user
        )
        Ingredient.objects.create(
            recipe=self.recipe,
            name='Flour',
            amount='2 cups'
        )
        Step.objects.create(
            recipe=self.recipe,
            step_number=1,
            instruction_text='Mix ingredients'
        )
    
    def test_recipe_detail_page_loads(self):
        """Test that recipe detail page loads."""
        url = reverse('recipe_detail', args=[self.recipe.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'recipes/recipe_detail.html')
        self.assertEqual(response.context['recipe'], self.recipe)
    
    def test_recipe_detail_shows_ingredients(self):
        """Test that recipe detail shows ingredients."""
        url = reverse('recipe_detail', args=[self.recipe.id])
        response = self.client.get(url)
        self.assertIn('ingredients', response.context)
        ingredients = response.context['ingredients']
        self.assertEqual(ingredients.count(), 1)
        self.assertEqual(ingredients[0].name, 'Flour')
    
    def test_recipe_detail_shows_steps(self):
        """Test that recipe detail shows steps."""
        url = reverse('recipe_detail', args=[self.recipe.id])
        response = self.client.get(url)
        self.assertIn('steps', response.context)
        steps = response.context['steps']
        self.assertEqual(steps.count(), 1)
        self.assertEqual(steps[0].instruction_text, 'Mix ingredients')
    
    def test_recipe_detail_404_for_nonexistent(self):
        """Test that nonexistent recipe returns 404."""
        url = reverse('recipe_detail', args=[99999])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)


class MyRecipesTests(TestCase):
    """Test cases for my recipes view."""
    
    def setUp(self):
        """Set up test data."""
        self.client = Client()
        self.user1 = User.objects.create_user(
            username='user1',
            password='testpass123'
        )
        self.user2 = User.objects.create_user(
            username='user2',
            password='testpass123'
        )
        # Create recipes for both users
        self.recipe1 = Recipe.objects.create(
            title='User1 Recipe',
            description='Recipe by user1',
            author=self.user1
        )
        self.recipe2 = Recipe.objects.create(
            title='User2 Recipe',
            description='Recipe by user2',
            author=self.user2
        )
    
    def test_my_recipes_requires_login(self):
        """Test that unauthenticated users are redirected to login."""
        url = reverse('my_recipes')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)
        self.assertIn('/login', response.url)
    
    def test_my_recipes_shows_only_user_recipes(self):
        """Test that my recipes only shows recipes by logged-in user."""
        self.client.login(username='user1', password='testpass123')
        url = reverse('my_recipes')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'recipes/my_recipes.html')
        recipes = response.context['recipes']
        self.assertEqual(recipes.count(), 1)
        self.assertEqual(recipes[0], self.recipe1)
        self.assertNotIn(self.recipe2, recipes)
    
    def test_my_recipes_empty_for_user_with_no_recipes(self):
        """Test that my recipes shows empty state for users with no recipes."""
        user3 = User.objects.create_user(
            username='user3',
            password='testpass123'
        )
        self.client.login(username='user3', password='testpass123')
        url = reverse('my_recipes')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        recipes = response.context['recipes']
        self.assertEqual(recipes.count(), 0)



