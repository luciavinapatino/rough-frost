"""
URL routing configuration for the recipes app.

This module defines the URL patterns for the recipes application.
All routes are relative to the base URL specified in the main project urls.py.

Routes:
    '' (root):             Home page with recipe listing and search (home)
    'create/':             Recipe creation form (create_recipe)
    'recipe/<int:pk>/':    Individual recipe detail view (recipe_detail)
"""
from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('recipes/create/', views.create_recipe, name='create_recipe'),
    path('recipes/<int:recipe_id>/', views.recipe_detail, name='recipe_detail'),
    path('recipes/my/', views.my_recipes, name='my_recipes'),
]

