"""
Unit tests for recipe-related views (create, detail, edit).
"""
from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from recipes.models import Recipe, Tag, Step


class RecipeCreationTests(TestCase):
    """Test cases for recipe creation."""

    def setUp(self):
        """Set up test data."""
        self.client = Client()
        self.user = User.objects.create_user(username='testuser', password='testpass123')
        self.create_url = reverse('create_recipe')
        # Create a cuisine tag for testing
        self.italian_tag = Tag.objects.create(name='Italian', category='cuisine')

    def test_create_recipe_page_loads(self):
        """Test that recipe creation page loads."""
        response = self.client.get(self.create_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'create_recipe.html')
        self.assertIn('form', response.context)

    def test_create_recipe_with_valid_data(self):
        """Test creating a recipe with valid data."""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.post(self.create_url, {
            'title': 'Spaghetti Carbonara',
            'description': 'Classic Italian pasta',
            'recipe_author': 'Jamie Oliver',
            'ingredients': 'Pasta\nEggs\nCheese',
            'steps_text': 'Boil pasta\nMix eggs and cheese\nCombine',
            'prep_time': 10,
            'cook_time': 20,
            'cuisine_type': self.italian_tag.id,
            'tags_csv': 'quick, easy',
        })

        # Should redirect on success
        self.assertEqual(response.status_code, 302)

        # Verify recipe was created
        recipe = Recipe.objects.get(title='Spaghetti Carbonara')
        self.assertEqual(recipe.author, self.user)
        self.assertEqual(recipe.prep_time, 10)
        self.assertEqual(recipe.cook_time, 20)
        self.assertEqual(recipe.recipe_author, 'Jamie Oliver')

        # Verify steps were created (3 steps)
        self.assertEqual(recipe.steps.count(), 3)
        self.assertEqual(recipe.steps.first().instruction_text, 'Boil pasta')

        # Verify tags were created
        self.assertTrue(recipe.tags.filter(name='Italian').exists())
        self.assertTrue(recipe.tags.filter(name='quick').exists())

    def test_create_recipe_with_minimal_fields(self):
        """Test creating a recipe with only required fields."""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.post(self.create_url, {
            'title': 'Simple Recipe',
            'description': 'A simple test recipe',
        })

        self.assertEqual(response.status_code, 302)
        recipe = Recipe.objects.get(title='Simple Recipe')
        self.assertEqual(recipe.author, self.user)
        self.assertEqual(recipe.steps.count(), 0)  # No steps provided

    def test_create_recipe_empty_title_fails(self):
        """Test that empty title fails validation."""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.post(self.create_url, {
            'title': '',
            'description': 'Test description',
        })

        # Should not redirect, stays on form page
        self.assertEqual(response.status_code, 200)
        self.assertFormError(response, 'form', 'title', 'Recipe title cannot be empty.')

    def test_create_recipe_assigns_author(self):
        """Test that logged-in user becomes the recipe author."""
        self.client.login(username='testuser', password='testpass123')
        self.client.post(self.create_url, {
            'title': 'Test Recipe',
            'description': 'Test description',
        })

        recipe = Recipe.objects.get(title='Test Recipe')
        self.assertEqual(recipe.author, self.user)

    def test_create_recipe_unauthenticated_uses_first_user(self):
        """Test that unauthenticated user gets first user as author."""
        # Don't log in
        response = self.client.post(self.create_url, {
            'title': 'Anon Recipe',
            'description': 'Made by anonymous',
        })

        recipe = Recipe.objects.get(title='Anon Recipe')
        self.assertEqual(recipe.author, User.objects.first())

    def test_create_recipe_with_tags_csv(self):
        """Test creating recipe with comma-separated tags."""
        self.client.login(username='testuser', password='testpass123')
        self.client.post(self.create_url, {
            'title': 'Tagged Recipe',
            'description': 'Recipe with tags',
            'tags_csv': 'vegan, gluten-free, quick',
        })

        recipe = Recipe.objects.get(title='Tagged Recipe')
        self.assertTrue(recipe.tags.filter(name='vegan').exists())
        self.assertTrue(recipe.tags.filter(name='gluten-free').exists())
        self.assertTrue(recipe.tags.filter(name='quick').exists())

    def test_create_recipe_with_steps_text(self):
        """Test creating recipe with newline-separated steps."""
        self.client.login(username='testuser', password='testpass123')
        self.client.post(self.create_url, {
            'title': 'Recipe with Steps',
            'description': 'Recipe with instructions',
            'steps_text': 'First step\nSecond step\nThird step',
        })

        recipe = Recipe.objects.get(title='Recipe with Steps')
        steps = recipe.steps.all().order_by('step_number')
        self.assertEqual(steps.count(), 3)
        self.assertEqual(steps[0].step_number, 1)
        self.assertEqual(steps[0].instruction_text, 'First step')
        self.assertEqual(steps[1].step_number, 2)
        self.assertEqual(steps[2].step_number, 3)


class RecipeEditTests(TestCase):
    """Test cases for recipe editing."""

    def setUp(self):
        """Set up test data."""
        self.client = Client()
        self.user1 = User.objects.create_user(username='user1', password='pass123')
        self.user2 = User.objects.create_user(username='user2', password='pass123')

        # Create a recipe owned by user1
        self.recipe = Recipe.objects.create(
            title='Original Title',
            description='Original description',
            author=self.user1,
            ingredients='Ingredient 1\nIngredient 2',
            prep_time=15,
            cook_time=30,
        )
        Step.objects.create(recipe=self.recipe, step_number=1, instruction_text='Step 1')
        Step.objects.create(recipe=self.recipe, step_number=2, instruction_text='Step 2')

        self.italian_tag = Tag.objects.create(name='Italian', category='cuisine')
        self.recipe.tags.add(self.italian_tag)

        self.edit_url = reverse('edit_recipe', args=[self.recipe.pk])

    def test_edit_recipe_by_author_succeeds(self):
        """Test that recipe author can edit their recipe."""
        self.client.login(username='user1', password='pass123')
        response = self.client.post(self.edit_url, {
            'title': 'Updated Title',
            'description': 'Updated description',
            'prep_time': 20,
            'cook_time': 40,
            'steps_text': 'New Step 1\nNew Step 2\nNew Step 3',
        })

        # Should redirect on success
        self.assertEqual(response.status_code, 302)

        # Verify recipe was updated
        self.recipe.refresh_from_db()
        self.assertEqual(self.recipe.title, 'Updated Title')
        self.assertEqual(self.recipe.prep_time, 20)

        # Verify steps were updated (now 3 steps)
        self.assertEqual(self.recipe.steps.count(), 3)
        self.assertEqual(self.recipe.steps.first().instruction_text, 'New Step 1')

    def test_edit_recipe_by_non_author_forbidden(self):
        """Test that non-author cannot edit recipe."""
        self.client.login(username='user2', password='pass123')
        response = self.client.post(self.edit_url, {
            'title': 'Hacked Title',
            'description': 'Should not work',
        })

        # Should return 403 Forbidden
        self.assertEqual(response.status_code, 403)

        # Verify recipe was NOT updated
        self.recipe.refresh_from_db()
        self.assertEqual(self.recipe.title, 'Original Title')

    def test_edit_recipe_unauthenticated_forbidden(self):
        """Test that unauthenticated users cannot edit."""
        # Don't log in - AnonymousUser won't match recipe.author
        response = self.client.post(self.edit_url, {
            'title': 'Hacked Title',
            'description': 'Should not work',
        })

        # Should return 403 Forbidden
        self.assertEqual(response.status_code, 403)

        # Verify recipe was NOT updated
        self.recipe.refresh_from_db()
        self.assertEqual(self.recipe.title, 'Original Title')

    def test_edit_recipe_preserves_author(self):
        """Test that editing does not change the original author."""
        self.client.login(username='user1', password='pass123')
        self.client.post(self.edit_url, {
            'title': 'Updated Title',
            'description': 'Updated description',
        })

        self.recipe.refresh_from_db()
        self.assertEqual(self.recipe.author, self.user1)

    def test_edit_recipe_nonexistent_returns_404(self):
        """Test that editing non-existent recipe returns 404."""
        self.client.login(username='user1', password='pass123')
        url = reverse('edit_recipe', args=[99999])
        response = self.client.get(url)

        self.assertEqual(response.status_code, 404)

    def test_edit_recipe_get_prepopulates_form(self):
        """Test that GET request prepopulates form with existing data."""
        self.client.login(username='user1', password='pass123')
        response = self.client.get(self.edit_url)

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'edit_recipe.html')

        # Verify form has initial data
        form = response.context['form']
        self.assertEqual(form.initial['steps_text'], 'Step 1\nStep 2')
        self.assertEqual(form.initial['cuisine_type'], self.italian_tag)

    def test_edit_recipe_updates_tags(self):
        """Test that editing updates tags correctly."""
        self.client.login(username='user1', password='pass123')
        mexican_tag = Tag.objects.create(name='Mexican', category='cuisine')

        self.client.post(self.edit_url, {
            'title': 'Original Title',
            'description': 'Original description',
            'cuisine_type': mexican_tag.id,
            'tags_csv': 'spicy, vegetarian',
        })

        self.recipe.refresh_from_db()

        # Old tag should be removed, new tags added
        self.assertFalse(self.recipe.tags.filter(name='Italian').exists())
        self.assertTrue(self.recipe.tags.filter(name='Mexican').exists())
        self.assertTrue(self.recipe.tags.filter(name='spicy').exists())

    def test_edit_recipe_clears_steps_when_empty(self):
        """Test that providing empty steps_text removes all steps."""
        self.client.login(username='user1', password='pass123')
        self.client.post(self.edit_url, {
            'title': 'Original Title',
            'description': 'Original description',
            'steps_text': '',  # Empty steps
        })

        self.recipe.refresh_from_db()
        self.assertEqual(self.recipe.steps.count(), 0)

    def test_edit_recipe_updates_all_fields(self):
        """Test that all recipe fields can be updated."""
        self.client.login(username='user1', password='pass123')
        self.client.post(self.edit_url, {
            'title': 'New Title',
            'description': 'New description',
            'recipe_author': 'Gordon Ramsay',
            'source_url': 'https://example.com/recipe',
            'image_url': 'https://example.com/image.jpg',
            'ingredients': 'New ingredient 1\nNew ingredient 2',
            'prep_time': 25,
            'cook_time': 45,
        })

        self.recipe.refresh_from_db()
        self.assertEqual(self.recipe.title, 'New Title')
        self.assertEqual(self.recipe.description, 'New description')
        self.assertEqual(self.recipe.recipe_author, 'Gordon Ramsay')
        self.assertEqual(self.recipe.source_url, 'https://example.com/recipe')
        self.assertEqual(self.recipe.image_url, 'https://example.com/image.jpg')
        self.assertEqual(self.recipe.prep_time, 25)
        self.assertEqual(self.recipe.cook_time, 45)


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
        Step.objects.create(
            recipe=self.recipe,
            step_number=1,
            instruction_text='Mix ingredients'
        )

    def test_recipe_detail_page_loads(self):
        """Test that recipe detail page loads."""
        url = reverse('recipe_detail', args=[self.recipe.pk])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'recipe_detail.html')
        self.assertEqual(response.context['recipe'], self.recipe)

    def test_recipe_detail_shows_steps(self):
        """Test that recipe detail shows steps."""
        url = reverse('recipe_detail', args=[self.recipe.pk])
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

    def test_recipe_detail_shows_edit_button_for_author(self):
        """Test that edit button is shown to recipe author."""
        self.client.login(username='testuser', password='testpass123')
        url = reverse('recipe_detail', args=[self.recipe.pk])
        response = self.client.get(url)
        self.assertContains(response, 'edit_recipe')

    def test_recipe_detail_hides_edit_button_for_non_author(self):
        """Test that edit button is hidden from non-authors."""
        other_user = User.objects.create_user(username='other', password='pass123')
        self.client.login(username='other', password='pass123')
        url = reverse('recipe_detail', args=[self.recipe.pk])
        response = self.client.get(url)
        # Edit button should not appear for non-authors
        self.assertNotContains(response, 'href="{}"'.format(reverse('edit_recipe', args=[self.recipe.pk])))
