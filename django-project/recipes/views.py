from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.models import User
from django.db.models import Q
from django.db import connection

from .models import Recipe, Tag, Step
from .forms import RecipeForm


def _search_recipes_postgres(query, recipes):
    """
    Perform full-text search using PostgreSQL-specific features.
    
    Args:
        query: Search string from user input
        recipes: QuerySet to filter (typically Recipe.objects.all())
    
    Returns:
        QuerySet of Recipe objects ranked by relevance
    """
    try:
        from django.contrib.postgres.search import SearchVector, SearchQuery, SearchRank
    except ImportError:
        return None
    
    vector = (
        SearchVector('title', weight='A')
        + SearchVector('description', weight='B')
        + SearchVector('tags__name', weight='C')
        + SearchVector('steps__instruction_text', weight='C')
    )
    search_query = SearchQuery(query)
    return (
        recipes
        .annotate(rank=SearchRank(vector, search_query))
        .filter(rank__gte=0.001)
        .order_by('-rank')
        .distinct()
    )


def _search_recipes_fallback(query, recipes):
    """
    Perform basic full-text-like search using icontains (SQLite-friendly).
    
    This is slower than PostgreSQL full-text search but works with any database.
    Searches across recipe title, description, tag names, and step instructions.
    
    Args:
        query: Search string from user input
        recipes: QuerySet to filter (typically Recipe.objects.all())
    
    Returns:
        QuerySet of Recipe objects matching the query
    """
    return recipes.filter(
        Q(title__icontains=query)
        | Q(description__icontains=query)
        | Q(tags__name__icontains=query)
        | Q(steps__instruction_text__icontains=query)
    ).distinct()


def _search_recipes(query, recipes):
    """
    Search recipes by query, using PostgreSQL full-text search if available.
    
    Falls back to basic icontains search for SQLite and other databases.
    
    Args:
        query: Search string from user input
        recipes: QuerySet to filter (typically Recipe.objects.all())
    
    Returns:
        QuerySet of matching Recipe objects
    """
    if not query:
        return recipes
    
    # Try PostgreSQL full-text search if available
    is_postgres = 'postgresql' in connection.settings_dict.get('ENGINE', '')
    if is_postgres:
        results = _search_recipes_postgres(query, recipes)
        if results is not None:
            return results
    
    # Fall back to basic search
    return _search_recipes_fallback(query, recipes)


def home(request):
    """
    Home page displaying recipes with optional search functionality.
    
    Supports search via the 'q' GET parameter. Uses PostgreSQL full-text search
    for better relevance when available, otherwise falls back to case-insensitive
    substring matching.
    
    Context:
        recipes: QuerySet of Recipe objects matching the search query (if provided)
        query: The search query string (empty if no search performed)
    """
    query = request.GET.get('q', '').strip()
    recipes = Recipe.objects.all()
    
    if query:
        recipes = _search_recipes(query, recipes)

    context = {
        'recipes': recipes,
        'query': query,
    }
    return render(request, 'home.html', context)


def create_recipe(request):
    """
    Create a new recipe via form submission.
    
    Accepts POST requests with recipe title, description, optional image URL,
    comma-separated tags, and newline-separated cooking steps.
    
    Automatically assigns the current logged-in user as the author. If no user
    is logged in, assigns the recipe to the first user in the database.
    
    On successful creation, displays a success message and redirects to home.
    
    Query Parameters:
        None (form data in POST body)
    
    Context (GET):
        form: Empty RecipeForm instance
    
    Returns:
        GET: Rendered create_recipe.html template
        POST (valid): Redirect to home with success message
        POST (invalid): Rendered create_recipe.html with form errors
    """
    if request.method == 'POST':
        form = RecipeForm(request.POST)
        if form.is_valid():
            # Assign author: prefer logged-in user, otherwise first user in DB
            author = request.user if request.user.is_authenticated else User.objects.first()
            recipe = form.save(commit=False)
            recipe.author = author
            recipe.save()

            # Tags: create or attach
            tag_names = form.cleaned_data.get('tags_csv', [])
            for name in tag_names:
                tag_obj, _ = Tag.objects.get_or_create(name=name)
                recipe.tags.add(tag_obj)

            # Steps: newline separated
            steps_text = form.cleaned_data.get('steps_text', '')
            for idx, line in enumerate([s.strip() for s in steps_text.splitlines() if s.strip()], start=1):
                Step.objects.create(recipe=recipe, step_number=idx, instruction_text=line)

            messages.success(request, 'Recipe created successfully.')
            return redirect('home')
    else:
        form = RecipeForm()

    return render(request, 'create_recipe.html', {'form': form})


def recipe_detail(request, pk):
    """
    Display a single recipe with all details: title, description, author, tags, and steps.
    
    Uses select_related and prefetch_related for efficient database queries.
    Raises Http404 if the recipe with the given pk is not found.
    
    URL Parameters:
        pk (int): Primary key of the recipe to display
    
    Context:
        recipe: The Recipe object
        steps: Ordered QuerySet of Step objects for this recipe
        tags: QuerySet of Tag objects associated with this recipe
    
    Returns:
        Rendered recipe_detail.html template, or Http404 if recipe not found
    """
    recipe = (
        Recipe.objects.select_related('author')
        .prefetch_related('tags', 'steps')
        .filter(pk=pk)
        .first()
    )
    if not recipe:
        # Let Django render a normal 404
        from django.http import Http404

        raise Http404("Recipe not found")

    context = {
        'recipe': recipe,
        'steps': recipe.steps.all(),
        'tags': recipe.tags.all(),
    }
    return render(request, 'recipe_detail.html', context)


