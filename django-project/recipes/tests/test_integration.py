"""
Integration tests that test multiple components working together.
"""
from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from recipes.models import Recipe, Ingredient, Step, Tag, Favorite


class AuthenticationIntegrationTests(TestCase):
    """Integration tests for authentication flow."""
    
    def setUp(self):
        """Set up test data."""
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
    
    def test_complete_registration_to_recipe_creation_flow(self):
        """Test complete flow: register -> login -> create recipe."""
        # Step 1: Register new user
        register_url = reverse('register')
        response = self.client.post(register_url, {
            'username': 'newuser',
            'password1': 'complexpass123',
            'password2': 'complexpass123'
        })
        self.assertEqual(response.status_code, 302)  # Redirect after registration
        
        # Step 2: User should be automatically logged in
        home_url = reverse('home')
        response = self.client.get(home_url)
        self.assertContains(response, 'newuser')
        
        # Step 3: Create a recipe
        create_url = reverse('create_recipe')
        response = self.client.post(create_url, {
            'title': 'My First Recipe',
            'description': 'A recipe I created',
            'ingredient_name': ['Flour'],
            'ingredient_amount': ['2 cups'],
            'instruction': ['Mix and bake']
        })
        self.assertEqual(response.status_code, 302)
        
        # Step 4: Verify recipe was created
        recipe = Recipe.objects.get(title='My First Recipe')
        self.assertEqual(recipe.author.username, 'newuser')
    
    def test_login_to_view_recipes_flow(self):
        """Test complete flow: login -> view my recipes -> view recipe detail."""
        # Step 1: Create a recipe as testuser
        self.client.login(username='testuser', password='testpass123')
        create_url = reverse('create_recipe')
        response = self.client.post(create_url, {
            'title': 'Test Recipe',
            'description': 'Test',
            'ingredient_name': ['Flour'],
            'ingredient_amount': ['2 cups'],
            'instruction': ['Mix']
        })
        recipe_id = Recipe.objects.get(title='Test Recipe').id
        
        # Step 2: Logout
        logout_url = reverse('logout')
        self.client.post(logout_url)
        
        # Step 3: Login again
        login_url = reverse('login')
        response = self.client.post(login_url, {
            'username': 'testuser',
            'password': 'testpass123'
        })
        self.assertEqual(response.status_code, 302)
        
        # Step 4: View my recipes
        my_recipes_url = reverse('my_recipes')
        response = self.client.get(my_recipes_url)
        self.assertContains(response, 'Test Recipe')
        
        # Step 5: View recipe detail
        detail_url = reverse('recipe_detail', args=[recipe_id])
        response = self.client.get(detail_url)
        self.assertContains(response, 'Test Recipe')
        self.assertContains(response, 'Flour')


class RecipeCRUDIntegrationTests(TestCase):
    """Integration tests for recipe CRUD operations."""
    
    def setUp(self):
        """Set up test data."""
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.client.login(username='testuser', password='testpass123')
    
    def test_create_recipe_with_all_components(self):
        """Test creating a recipe with ingredients, steps, and tags."""
        create_url = reverse('create_recipe')
        
        # Create tags first
        tag1 = Tag.objects.create(name='dessert', category='cuisine')
        tag2 = Tag.objects.create(name='vegan', category='dietary')
        
        response = self.client.post(create_url, {
            'title': 'Vegan Chocolate Cake',
            'description': 'A delicious vegan cake',
            'image_url': 'https://example.com/cake.jpg',
            'ingredient_name': ['Flour', 'Sugar', 'Cocoa'],
            'ingredient_amount': ['2 cups', '1 cup', '1/2 cup'],
            'instruction': [
                'Preheat oven to 350°F',
                'Mix dry ingredients',
                'Add wet ingredients',
                'Bake for 30 minutes'
            ]
        })
        
        self.assertEqual(response.status_code, 302)
        
        # Verify recipe
        recipe = Recipe.objects.get(title='Vegan Chocolate Cake')
        self.assertEqual(recipe.description, 'A delicious vegan cake')
        self.assertEqual(recipe.image_url, 'https://example.com/cake.jpg')
        
        # Verify ingredients
        ingredients = recipe.ingredients.all()
        self.assertEqual(ingredients.count(), 3)
        ingredient_names = [ing.name for ing in ingredients]
        self.assertIn('Flour', ingredient_names)
        self.assertIn('Sugar', ingredient_names)
        self.assertIn('Cocoa', ingredient_names)
        
        # Verify steps
        steps = recipe.steps.all()
        self.assertEqual(steps.count(), 4)
        self.assertEqual(steps[0].step_number, 1)
        self.assertEqual(steps[0].instruction_text, 'Preheat oven to 350°F')
        self.assertEqual(steps[3].step_number, 4)
    
    def test_recipe_display_integration(self):
        """Test that recipe displays correctly with all components."""
        # Create recipe with all components
        recipe = Recipe.objects.create(
            title='Complete Recipe',
            description='A complete recipe',
            author=self.user,
            image_url='https://example.com/image.jpg'
        )
        Ingredient.objects.create(recipe=recipe, name='Flour', amount='2 cups')
        Ingredient.objects.create(recipe=recipe, name='Sugar', amount='1 cup')
        Step.objects.create(recipe=recipe, step_number=1, instruction_text='Step 1')
        Step.objects.create(recipe=recipe, step_number=2, instruction_text='Step 2')
        
        # View recipe detail
        detail_url = reverse('recipe_detail', args=[recipe.id])
        response = self.client.get(detail_url)
        
        # Verify all components are displayed
        self.assertContains(response, 'Complete Recipe')
        self.assertContains(response, 'A complete recipe')
        self.assertContains(response, 'Flour')
        self.assertContains(response, '2 cups')
        self.assertContains(response, 'Sugar')
        self.assertContains(response, 'Step 1')
        self.assertContains(response, 'Step 2')


class UserRecipeRelationshipTests(TestCase):
    """Integration tests for user-recipe relationships."""
    
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
    
    def test_user_sees_only_own_recipes(self):
        """Test that users only see their own recipes in my_recipes."""
        # User1 creates a recipe
        self.client.login(username='user1', password='testpass123')
        create_url = reverse('create_recipe')
        self.client.post(create_url, {
            'title': 'User1 Recipe',
            'description': 'Recipe by user1',
            'ingredient_name': ['Flour'],
            'ingredient_amount': ['2 cups'],
            'instruction': ['Mix']
        })
        
        # User2 creates a recipe
        self.client.login(username='user2', password='testpass123')
        self.client.post(create_url, {
            'title': 'User2 Recipe',
            'description': 'Recipe by user2',
            'ingredient_name': ['Sugar'],
            'ingredient_amount': ['1 cup'],
            'instruction': ['Mix']
        })
        
        # User1 views my_recipes
        self.client.login(username='user1', password='testpass123')
        my_recipes_url = reverse('my_recipes')
        response = self.client.get(my_recipes_url)
        recipes = response.context['recipes']
        self.assertEqual(recipes.count(), 1)
        self.assertEqual(recipes[0].title, 'User1 Recipe')
        self.assertEqual(recipes[0].author, self.user1)
    
    def test_recipe_favorites_integration(self):
        """Test that users can favorite recipes."""
        # Create a recipe
        recipe = Recipe.objects.create(
            title='Favorite Recipe',
            description='A recipe to favorite',
            author=self.user1
        )
        
        # User2 favorites the recipe
        favorite = Favorite.objects.create(
            user=self.user2,
            recipe=recipe,
            notes='I love this recipe!'
        )
        
        # Verify favorite was created
        self.assertEqual(favorite.user, self.user2)
        self.assertEqual(favorite.recipe, recipe)
        self.assertEqual(favorite.notes, 'I love this recipe!')
        
        # Verify recipe has favorite
        self.assertEqual(recipe.favorited_by.count(), 1)
        self.assertEqual(recipe.favorited_by.first().user, self.user2)
        
        # Verify user has favorite
        self.assertEqual(self.user2.favorites.count(), 1)
        self.assertEqual(self.user2.favorites.first().recipe, recipe)



