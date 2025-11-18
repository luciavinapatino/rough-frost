"""
Main URL configuration for the recipeapp project.

Routes all requests to the appropriate app handlers:
    /admin/    - Django admin interface
    /          - recipes app routes (home, create, detail)
"""
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('recipes.urls')),
]

