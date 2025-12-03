"""
Unit tests for Recipe, Ingredient, Step, and Tag models.
"""
from django.test import TestCase
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from recipes.models import Recipe, Ingredient, Step, Tag, Favorite


class RecipeModelTests(TestCase):
    """Test cases for the Recipe model."""
    
    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123',
            email='test@example.com'
        )
    
    def test_recipe_creation(self):
        """Test creating a recipe with required fields."""
        recipe = Recipe.objects.create(
            title='Test Recipe',
            description='A test recipe description',
            author=self.user
        )
        self.assertEqual(recipe.title, 'Test Recipe')
        self.assertEqual(recipe.description, 'A test recipe description')
        self.assertEqual(recipe.author, self.user)
        self.assertIsNotNone(recipe.created_at)
    
    def test_recipe_str_representation(self):
        """Test recipe string representation."""
        recipe = Recipe.objects.create(
            title='Chocolate Cake',
            description='Delicious cake',
            author=self.user
        )
        self.assertEqual(str(recipe), 'Chocolate Cake')
    
    def test_recipe_ordering(self):
        """Test that recipes are ordered by created_at descending."""
        recipe1 = Recipe.objects.create(
            title='First Recipe',
            description='First',
            author=self.user
        )
        recipe2 = Recipe.objects.create(
            title='Second Recipe',
            description='Second',
            author=self.user
        )
        recipes = Recipe.objects.all()
        self.assertEqual(recipes[0], recipe2)  # Newest first
        self.assertEqual(recipes[1], recipe1)
    
    def test_recipe_cascade_delete(self):
        """Test that deleting a user deletes their recipes."""
        recipe = Recipe.objects.create(
            title='Test Recipe',
            description='Test',
            author=self.user
        )
        recipe_id = recipe.id
        self.user.delete()
        self.assertFalse(Recipe.objects.filter(id=recipe_id).exists())


class IngredientModelTests(TestCase):
    """Test cases for the Ingredient model."""
    
    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.recipe = Recipe.objects.create(
            title='Test Recipe',
            description='Test',
            author=self.user
        )
    
    def test_ingredient_creation(self):
        """Test creating an ingredient."""
        ingredient = Ingredient.objects.create(
            recipe=self.recipe,
            name='Flour',
            amount='2 cups'
        )
        self.assertEqual(ingredient.name, 'Flour')
        self.assertEqual(ingredient.amount, '2 cups')
        self.assertEqual(ingredient.recipe, self.recipe)
    
    def test_ingredient_str_with_amount(self):
        """Test ingredient string representation with amount."""
        ingredient = Ingredient.objects.create(
            recipe=self.recipe,
            name='Sugar',
            amount='1 cup'
        )
        self.assertEqual(str(ingredient), '1 cup Sugar')
    
    def test_ingredient_str_without_amount(self):
        """Test ingredient string representation without amount."""
        ingredient = Ingredient.objects.create(
            recipe=self.recipe,
            name='Salt'
        )
        self.assertEqual(str(ingredient), 'Salt')
    
    def test_ingredient_cascade_delete(self):
        """Test that deleting a recipe deletes its ingredients."""
        ingredient = Ingredient.objects.create(
            recipe=self.recipe,
            name='Flour',
            amount='2 cups'
        )
        ingredient_id = ingredient.id
        self.recipe.delete()
        self.assertFalse(Ingredient.objects.filter(id=ingredient_id).exists())


class StepModelTests(TestCase):
    """Test cases for the Step model."""
    
    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.recipe = Recipe.objects.create(
            title='Test Recipe',
            description='Test',
            author=self.user
        )
    
    def test_step_creation(self):
        """Test creating a step."""
        step = Step.objects.create(
            recipe=self.recipe,
            step_number=1,
            instruction_text='Preheat oven to 350°F'
        )
        self.assertEqual(step.step_number, 1)
        self.assertEqual(step.instruction_text, 'Preheat oven to 350°F')
        self.assertEqual(step.recipe, self.recipe)
    
    def test_step_str_representation(self):
        """Test step string representation."""
        step = Step.objects.create(
            recipe=self.recipe,
            step_number=2,
            instruction_text='Mix ingredients'
        )
        self.assertEqual(str(step), 'Test Recipe - Step 2')
    
    def test_step_ordering(self):
        """Test that steps are ordered by step_number."""
        step2 = Step.objects.create(
            recipe=self.recipe,
            step_number=2,
            instruction_text='Second step'
        )
        step1 = Step.objects.create(
            recipe=self.recipe,
            step_number=1,
            instruction_text='First step'
        )
        steps = Step.objects.all()
        self.assertEqual(steps[0], step1)
        self.assertEqual(steps[1], step2)
    
    def test_step_unique_together(self):
        """Test that step_number must be unique per recipe."""
        Step.objects.create(
            recipe=self.recipe,
            step_number=1,
            instruction_text='First step'
        )
        # Creating another step with same number should work (different recipe)
        recipe2 = Recipe.objects.create(
            title='Another Recipe',
            description='Test',
            author=self.user
        )
        step2 = Step.objects.create(
            recipe=recipe2,
            step_number=1,
            instruction_text='First step'
        )
        self.assertEqual(step2.step_number, 1)
    
    def test_step_cascade_delete(self):
        """Test that deleting a recipe deletes its steps."""
        step = Step.objects.create(
            recipe=self.recipe,
            step_number=1,
            instruction_text='Test step'
        )
        step_id = step.id
        self.recipe.delete()
        self.assertFalse(Step.objects.filter(id=step_id).exists())


class TagModelTests(TestCase):
    """Test cases for the Tag model."""
    
    def test_tag_creation(self):
        """Test creating a tag."""
        tag = Tag.objects.create(name='vegan')
        self.assertEqual(tag.name, 'vegan')
    
    def test_tag_str_representation(self):
        """Test tag string representation."""
        tag = Tag.objects.create(name='dessert')
        self.assertEqual(str(tag), 'dessert')
    
    def test_tag_unique_name(self):
        """Test that tag names must be unique."""
        Tag.objects.create(name='vegan')
        with self.assertRaises(Exception):  # IntegrityError
            Tag.objects.create(name='vegan')
    
    def test_tag_ordering(self):
        """Test that tags are ordered alphabetically."""
        Tag.objects.create(name='zebra')
        Tag.objects.create(name='apple')
        tags = Tag.objects.all()
        self.assertEqual(tags[0].name, 'apple')
        self.assertEqual(tags[1].name, 'zebra')


class FavoriteModelTests(TestCase):
    """Test cases for the Favorite model."""
    
    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.recipe = Recipe.objects.create(
            title='Test Recipe',
            description='Test',
            author=self.user
        )
    
    def test_favorite_creation(self):
        """Test creating a favorite."""
        favorite = Favorite.objects.create(
            user=self.user,
            recipe=self.recipe,
            notes='I love this recipe!'
        )
        self.assertEqual(favorite.user, self.user)
        self.assertEqual(favorite.recipe, self.recipe)
        self.assertEqual(favorite.notes, 'I love this recipe!')
    
    def test_favorite_str_representation(self):
        """Test favorite string representation."""
        favorite = Favorite.objects.create(
            user=self.user,
            recipe=self.recipe
        )
        self.assertEqual(str(favorite), 'testuser favorited Test Recipe')
    
    def test_favorite_unique_together(self):
        """Test that a user can only favorite a recipe once."""
        Favorite.objects.create(
            user=self.user,
            recipe=self.recipe
        )
        with self.assertRaises(Exception):  # IntegrityError
            Favorite.objects.create(
                user=self.user,
                recipe=self.recipe
            )
    
    def test_favorite_cascade_delete_user(self):
        """Test that deleting a user deletes their favorites."""
        favorite = Favorite.objects.create(
            user=self.user,
            recipe=self.recipe
        )
        favorite_id = favorite.id
        self.user.delete()
        self.assertFalse(Favorite.objects.filter(id=favorite_id).exists())
    
    def test_favorite_cascade_delete_recipe(self):
        """Test that deleting a recipe deletes its favorites."""
        favorite = Favorite.objects.create(
            user=self.user,
            recipe=self.recipe
        )
        favorite_id = favorite.id
        self.recipe.delete()
        self.assertFalse(Favorite.objects.filter(id=favorite_id).exists())



