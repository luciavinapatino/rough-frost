"""
End-to-end tests that test complete user journeys.
"""
from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from recipes.models import Recipe, Ingredient, Step


class CompleteUserJourneyTests(TestCase):
    """End-to-end tests for complete user journeys."""
    
    def setUp(self):
        """Set up test client."""
        self.client = Client()
    
    def test_new_user_journey(self):
        """
        Test complete journey: Register -> Login -> Create Recipe -> View Recipe -> Logout
        """
        # Step 1: User visits homepage (unauthenticated)
        home_url = reverse('home')
        response = self.client.get(home_url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Log in')
        self.assertContains(response, 'Create account')
        
        # Step 2: User clicks "Create account"
        register_url = reverse('register')
        response = self.client.get(register_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'registration/register.html')
        
        # Step 3: User registers
        response = self.client.post(register_url, {
            'username': 'newuser',
            'password1': 'complexpass123!',
            'password2': 'complexpass123!'
        })
        self.assertEqual(response.status_code, 302)  # Redirect after registration
        
        # Step 4: User is automatically logged in and sees homepage
        response = self.client.get(home_url)
        self.assertContains(response, 'Welcome')
        self.assertContains(response, 'newuser')
        self.assertContains(response, 'Create Recipe')
        self.assertContains(response, 'My Recipes')
        
        # Step 5: User clicks "Create Recipe"
        create_url = reverse('create_recipe')
        response = self.client.get(create_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'recipes/create_recipe.html')
        
        # Step 6: User creates a recipe
        response = self.client.post(create_url, {
            'title': 'My First Recipe',
            'description': 'This is my first recipe in the app',
            'image_url': 'https://example.com/recipe.jpg',
            'ingredient_name': ['Flour', 'Sugar', 'Eggs'],
            'ingredient_amount': ['2 cups', '1 cup', '3'],
            'instruction': [
                'Preheat oven to 350°F',
                'Mix dry ingredients in a bowl',
                'Add wet ingredients and mix well',
                'Pour into pan and bake for 25 minutes'
            ]
        })
        self.assertEqual(response.status_code, 302)  # Redirect to recipe detail
        
        # Step 7: User views the created recipe
        recipe = Recipe.objects.get(title='My First Recipe')
        detail_url = reverse('recipe_detail', args=[recipe.id])
        response = self.client.get(detail_url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'My First Recipe')
        self.assertContains(response, 'This is my first recipe in the app')
        self.assertContains(response, 'Flour')
        self.assertContains(response, '2 cups')
        self.assertContains(response, 'Sugar')
        self.assertContains(response, 'Preheat oven to 350°F')
        self.assertContains(response, 'Mix dry ingredients')
        
        # Step 8: User views "My Recipes"
        my_recipes_url = reverse('my_recipes')
        response = self.client.get(my_recipes_url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'My First Recipe')
        recipes = response.context['recipes']
        self.assertEqual(recipes.count(), 1)
        
        # Step 9: User logs out
        logout_url = reverse('logout')
        response = self.client.post(logout_url)
        self.assertEqual(response.status_code, 302)  # Redirect to home
        
        # Step 10: User is logged out and sees login/register buttons
        response = self.client.get(home_url)
        self.assertContains(response, 'Log in')
        self.assertContains(response, 'Create account')
        self.assertNotContains(response, 'Welcome')
    
    def test_returning_user_journey(self):
        """
        Test complete journey: Login -> View Recipes -> Create Another Recipe -> View All Recipes
        """
        # Setup: Create a user with existing recipes
        user = User.objects.create_user(
            username='returninguser',
            password='testpass123'
        )
        recipe1 = Recipe.objects.create(
            title='Existing Recipe 1',
            description='First recipe',
            author=user
        )
        recipe2 = Recipe.objects.create(
            title='Existing Recipe 2',
            description='Second recipe',
            author=user
        )
        
        # Step 1: User visits homepage
        home_url = reverse('home')
        response = self.client.get(home_url)
        self.assertContains(response, 'Log in')
        
        # Step 2: User clicks "Log in"
        login_url = reverse('login')
        response = self.client.get(login_url)
        self.assertEqual(response.status_code, 200)
        
        # Step 3: User logs in
        response = self.client.post(login_url, {
            'username': 'returninguser',
            'password': 'testpass123'
        })
        self.assertEqual(response.status_code, 302)  # Redirect to home
        
        # Step 4: User sees welcome message
        response = self.client.get(home_url)
        self.assertContains(response, 'Welcome')
        self.assertContains(response, 'returninguser')
        
        # Step 5: User views "My Recipes"
        my_recipes_url = reverse('my_recipes')
        response = self.client.get(my_recipes_url)
        self.assertEqual(response.status_code, 200)
        recipes = response.context['recipes']
        self.assertEqual(recipes.count(), 2)
        recipe_titles = [r.title for r in recipes]
        self.assertIn('Existing Recipe 1', recipe_titles)
        self.assertIn('Existing Recipe 2', recipe_titles)
        
        # Step 6: User views a recipe detail
        detail_url = reverse('recipe_detail', args=[recipe1.id])
        response = self.client.get(detail_url)
        self.assertContains(response, 'Existing Recipe 1')
        
        # Step 7: User creates another recipe
        create_url = reverse('create_recipe')
        response = self.client.post(create_url, {
            'title': 'New Recipe',
            'description': 'A new recipe',
            'ingredient_name': ['Flour'],
            'ingredient_amount': ['2 cups'],
            'instruction': ['Mix']
        })
        self.assertEqual(response.status_code, 302)
        
        # Step 8: User views "My Recipes" again and sees all 3 recipes
        response = self.client.get(my_recipes_url)
        recipes = response.context['recipes']
        self.assertEqual(recipes.count(), 3)
    
    def test_recipe_creation_with_multiple_ingredients_and_steps(self):
        """
        Test creating a complex recipe with many ingredients and steps.
        """
        user = User.objects.create_user(
            username='chef',
            password='testpass123'
        )
        self.client.login(username='chef', password='testpass123')
        
        create_url = reverse('create_recipe')
        
        # Create a complex recipe
        ingredients = [
            ('Flour', '2 cups'),
            ('Sugar', '1 cup'),
            ('Butter', '1/2 cup'),
            ('Eggs', '2'),
            ('Vanilla', '1 tsp'),
            ('Baking Powder', '1 tsp'),
            ('Salt', '1/2 tsp'),
        ]
        
        instructions = [
            'Preheat oven to 350°F',
            'Grease and flour a 9x13 inch pan',
            'In a large bowl, cream together butter and sugar',
            'Beat in eggs one at a time',
            'Stir in vanilla',
            'Combine flour, baking powder, and salt',
            'Gradually blend into the creamed mixture',
            'Spread batter evenly into the prepared pan',
            'Bake for 30 to 35 minutes',
            'Cool in pan on wire rack'
        ]
        
        response = self.client.post(create_url, {
            'title': 'Complex Chocolate Cake',
            'description': 'A detailed recipe with many steps',
            'ingredient_name': [ing[0] for ing in ingredients],
            'ingredient_amount': [ing[1] for ing in ingredients],
            'instruction': instructions
        })
        
        self.assertEqual(response.status_code, 302)
        
        # Verify recipe was created with all components
        recipe = Recipe.objects.get(title='Complex Chocolate Cake')
        self.assertEqual(recipe.ingredients.count(), 7)
        self.assertEqual(recipe.steps.count(), 10)
        
        # Verify ingredients
        ingredient_names = [ing.name for ing in recipe.ingredients.all()]
        self.assertIn('Flour', ingredient_names)
        self.assertIn('Vanilla', ingredient_names)
        
        # Verify steps are numbered correctly
        steps = recipe.steps.all()
        self.assertEqual(steps[0].step_number, 1)
        self.assertEqual(steps[0].instruction_text, 'Preheat oven to 350°F')
        self.assertEqual(steps[9].step_number, 10)
        self.assertEqual(steps[9].instruction_text, 'Cool in pan on wire rack')
    
    def test_error_handling_journey(self):
        """
        Test user journey with error handling: Invalid login -> Retry -> Success
        """
        user = User.objects.create_user(
            username='testuser',
            password='correctpass123'
        )
        
        login_url = reverse('login')
        
        # Step 1: User tries to login with wrong password
        response = self.client.post(login_url, {
            'username': 'testuser',
            'password': 'wrongpassword'
        })
        self.assertEqual(response.status_code, 200)  # Stays on login page
        self.assertContains(response, 'Invalid username or password')
        
        # Step 2: User tries with wrong username
        response = self.client.post(login_url, {
            'username': 'wronguser',
            'password': 'correctpass123'
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Invalid username or password')
        
        # Step 3: User successfully logs in
        response = self.client.post(login_url, {
            'username': 'testuser',
            'password': 'correctpass123'
        })
        self.assertEqual(response.status_code, 302)  # Redirects to home
        
        # Step 4: User is now logged in
        home_url = reverse('home')
        response = self.client.get(home_url)
        self.assertContains(response, 'Welcome')
        self.assertContains(response, 'testuser')



