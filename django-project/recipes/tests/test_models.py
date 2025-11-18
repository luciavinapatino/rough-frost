from django.test import TestCase
from django.urls import reverse
from django.contrib.auth.models import User

from .models import Recipe, Tag, Step


class RecipeFlowTests(TestCase):
	"""Integration-style tests for creating, searching, and viewing recipes."""

	def setUp(self):
		self.user = User.objects.create_user(username='tester', password='pass')
		# Log in the test client so create view assigns the authenticated user
		logged_in = self.client.login(username='tester', password='pass')
		assert logged_in

	def test_create_recipe_creates_tags_and_steps_and_redirects(self):
		data = {
			'title': 'Test Pie',
			'description': 'A delightful test pie.',
			'image_url': 'http://example.com/pie.jpg',
			'tags_csv': 'dessert, test',
			'steps_text': 'Preheat oven\nMix ingredients',
		}

		response = self.client.post(reverse('create_recipe'), data)
		# Should redirect to home on success
		self.assertEqual(response.status_code, 302)

		recipe = Recipe.objects.get(title='Test Pie')
		self.assertEqual(recipe.author, self.user)
		self.assertEqual(recipe.description, 'A delightful test pie.')

		tag_names = sorted(list(recipe.tags.values_list('name', flat=True)))
		self.assertListEqual(tag_names, ['dessert', 'test'])

		steps = list(recipe.steps.order_by('step_number').values_list('instruction_text', flat=True))
		self.assertListEqual(steps, ['Preheat oven', 'Mix ingredients'])

	def test_search_returns_recipe_and_detail_shows_all_fields(self):
		# Create a recipe directly
		recipe = Recipe.objects.create(title='Chocolate Cake', description='Rich chocolate cake', author=self.user)
		tag = Tag.objects.create(name='dessert')
		recipe.tags.add(tag)
		Step.objects.create(recipe=recipe, step_number=1, instruction_text='Bake at 350F')

		# Search by title
		response = self.client.get(reverse('home') + '?q=Chocolate')
		self.assertEqual(response.status_code, 200)
		self.assertContains(response, 'Chocolate Cake')

		# Visit detail page
		detail_url = reverse('recipe_detail', args=[recipe.pk])
		response = self.client.get(detail_url)
		self.assertEqual(response.status_code, 200)
		self.assertContains(response, 'Rich chocolate cake')
		self.assertContains(response, 'Bake at 350F')
		self.assertContains(response, 'dessert')


