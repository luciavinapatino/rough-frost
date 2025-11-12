#!/usr/bin/env python3
"""
Seed the Django database with test data.

This script creates sample users, tags, recipes, steps, and favorites for
testing and demonstration purposes. It is safe to run multiple times as it
uses get_or_create() to avoid duplicates.

Usage:
    From repository root:
        python3 django-project/seed_data.py
    
    Or from django-project directory:
        python3 seed_data.py

Environment:
    Uses the Django settings configured in DJANGO_SETTINGS_MODULE
    (recipeapp.settings by default).

Database:
    Works with any database backend (SQLite, PostgreSQL, etc.) configured
    in Django settings.

Created Objects:
    - 2 Users: alice and bob (both with password 'password123')
    - 2 Tags: 'dessert' and 'breakfast'
    - 2 Recipes: 'Simple Pancakes' and 'Chocolate Chip Cookies'
    - 6 Steps: 3 for each recipe
    - 2 Favorites: users have favorited each other's recipes

Notes:
    Passwords are only for local testing. NEVER use these passwords in production.
"""
from pathlib import Path
import os
import sys


BASE_DIR = Path(__file__).resolve().parent
# Ensure the project package (django-project) is on path and settings can be found
sys.path.insert(0, str(BASE_DIR))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'recipeapp.settings')

import django
django.setup()

from django.contrib.auth.models import User
from recipes.models import Tag, Recipe, Step, Favorite
from django.utils import timezone


def create_user(data):
    """
    Create or update a user with the provided data.
    
    Uses get_or_create to ensure idempotency. If the user already exists,
    updates the password (if provided) to allow re-running the script.
    
    Args:
        data (dict): User data containing:
            - username (required): Unique username
            - email (optional): Email address
            - password (optional): Password to set
    
    Returns:
        User: The created or retrieved user object
    """
    username = data.get('username')
    defaults = {'email': data.get('email', '')}
    user, created = User.objects.get_or_create(username=username, defaults=defaults)
    
    # If a password is provided, set it (overwrites existing password on repeated runs)
    if data.get('password'):
        user.set_password(data['password'])
        user.save()
    
    return user


def main():
    """
    Main entry point for seeding the database.
    
    Creates or verifies the existence of all test data objects and
    prints a summary of created/verified items.
    """
    print('Seeding database...')

    # Create users
    alice = create_user({
        'username': 'alice',
        'email': 'alice@example.com',
        'password': 'password123'
    })
    bob = create_user({
        'username': 'bob',
        'email': 'bob@example.com',
        'password': 'password123'
    })
    print(f'✓ Users: alice and bob')

    # Create tags
    dessert, _ = Tag.objects.get_or_create(name='dessert')
    breakfast, _ = Tag.objects.get_or_create(name='breakfast')
    print(f'✓ Tags: dessert, breakfast')

    # Create recipes with tags
    r1, created_r1 = Recipe.objects.get_or_create(
        title='Simple Pancakes',
        defaults={
            'description': 'Fluffy pancakes made with basic ingredients.',
            'author': alice,
            'image_url': 'https://example.com/pancakes.jpg',
            'created_at': timezone.now(),
        }
    )
    # Ensure tags and author are set correctly (in case recipe already existed)
    r1.author = alice
    r1.image_url = 'https://example.com/pancakes.jpg'
    r1.save()
    r1.tags.add(breakfast)

    r2, created_r2 = Recipe.objects.get_or_create(
        title='Chocolate Chip Cookies',
        defaults={
            'description': 'Crispy edges, chewy center.',
            'author': bob,
            'image_url': 'https://example.com/cookies.jpg',
            'created_at': timezone.now(),
        }
    )
    # Ensure tags and author are set correctly (in case recipe already existed)
    r2.author = bob
    r2.image_url = 'https://example.com/cookies.jpg'
    r2.save()
    r2.tags.add(dessert)
    
    print(f'✓ Recipes: Simple Pancakes (by alice), Chocolate Chip Cookies (by bob)')

    # Create steps for recipe 1
    Step.objects.get_or_create(
        recipe=r1,
        step_number=1,
        defaults={'instruction_text': 'Mix dry ingredients.'}
    )
    Step.objects.get_or_create(
        recipe=r1,
        step_number=2,
        defaults={'instruction_text': 'Add milk and eggs, whisk to combine.'}
    )
    Step.objects.get_or_create(
        recipe=r1,
        step_number=3,
        defaults={'instruction_text': 'Cook on a hot griddle until golden.'}
    )

    # Create steps for recipe 2
    Step.objects.get_or_create(
        recipe=r2,
        step_number=1,
        defaults={'instruction_text': 'Preheat oven to 350°F (175°C).'}
    )
    Step.objects.get_or_create(
        recipe=r2,
        step_number=2,
        defaults={'instruction_text': 'Cream butter and sugars, add eggs and vanilla.'}
    )
    Step.objects.get_or_create(
        recipe=r2,
        step_number=3,
        defaults={'instruction_text': 'Fold in chocolate chips and bake 10-12 minutes.'}
    )
    
    print(f'✓ Steps: 6 steps created (3 per recipe)')

    # Create favorites
    Favorite.objects.get_or_create(
        user=bob,
        recipe=r1,
        defaults={'notes': 'Family favorite'}
    )
    Favorite.objects.get_or_create(
        user=alice,
        recipe=r2,
        defaults={'notes': 'Baked for a party'}
    )
    
    print(f'✓ Favorites: bob favorited pancakes, alice favorited cookies')

    # Print verification summary
    print('\n' + '='*60)
    print('DATABASE SEEDING SUMMARY')
    print('='*60)
    print(f'\nUsers ({User.objects.count()}):')
    for user in User.objects.all():
        print(f'  - {user.username} ({user.email})')

    print(f'\nTags ({Tag.objects.count()}):')
    for tag in Tag.objects.all().order_by('name'):
        print(f'  - {tag.name}')

    print(f'\nRecipes ({Recipe.objects.count()}):')
    for recipe in Recipe.objects.all().order_by('created_at'):
        tags = ', '.join([t.name for t in recipe.tags.all()])
        step_count = recipe.steps.count()
        print(f'  - {recipe.title} by {recipe.author.username}')
        print(f'    Tags: {tags or "(none)"}')
        print(f'    Steps: {step_count}')

    print(f'\nFavorites ({Favorite.objects.count()}):')
    for fav in Favorite.objects.all().order_by('-created_at'):
        print(f'  - {fav.user.username} → {fav.recipe.title}')
        if fav.notes:
            print(f'    Notes: {fav.notes}')

    print('\n' + '='*60)
    print('✓ Seeding complete!')
    print('='*60)
