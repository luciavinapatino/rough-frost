from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('recipes/create/', views.create_recipe, name='create_recipe'),
    path('recipes/<int:recipe_id>/', views.recipe_detail, name='recipe_detail'),
    path('recipes/my/', views.my_recipes, name='my_recipes'),
]

