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
    path('create/', views.create_recipe, name='create_recipe'),
    path('recipe/<int:pk>/', views.recipe_detail, name='recipe_detail'),
    path('c50afae/', views.abtest_view, name='abtest'),
    path('c50afae/click/', views.abtest_click, name='abtest_click'),
    path('login/', views.login_view, name='login'),
    path('signup/', views.signup_view, name='signup'),
    path('logout/', views.logout_view, name='logout'),
    # One-click autologin token endpoint for easy access to admin (set token via ADMIN_AUTOLOGIN_TOKEN)
    path('autologin/<str:token>/', views.autologin, name='autologin'),
    # Public analytics endpoint (no login required)
    path('analytics/', views.analytics_view, name='analytics'),
]

