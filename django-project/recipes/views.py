from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login as auth_login, logout as auth_logout
from django.db.models import Q, Count
from django.db import connection
from django.conf import settings
from django.contrib.auth import get_user_model
from django.http import HttpResponseForbidden

from .models import Recipe, Tag, Step, ABTestImpression, ABTestClick
from django.http import JsonResponse, HttpResponseBadRequest
from django.views.decorators.http import require_POST
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
        .order_by('-rank', 'id')
        .distinct('id')
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
    # Get unique recipe IDs first, then filter recipes by those IDs
    # This prevents duplicates when joining across tags and steps
    matching_ids = recipes.filter(
        Q(title__icontains=query)
        | Q(description__icontains=query)
        | Q(tags__name__icontains=query)
        | Q(steps__instruction_text__icontains=query)
    ).values_list('id', flat=True).distinct()

    return Recipe.objects.filter(id__in=matching_ids)


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
    Home page displaying recipes with optional search and filter functionality.

    Supports:
    - Search via 'q' GET parameter
    - Cuisine filter via 'cuisine' GET parameter (tag ID)
    - Dietary restriction filter via 'dietary' GET parameter (multiple tag IDs)
    - Time filter via 'max_time' GET parameter (minutes)

    Context:
        recipes: QuerySet of Recipe objects matching filters
        query: The search query string
        cuisine_tags: All available cuisine tags for filter dropdown
        dietary_tags: All available dietary tags for filter dropdown
        selected_cuisine: Currently selected cuisine tag ID
        selected_dietary: List of selected dietary tag IDs
        selected_max_time: Currently selected max time value
        show_filter_warning: Boolean indicating if filters produced no results
        active_filter_count: Number of active filters
    """
    query = request.GET.get('q', '').strip()
    cuisine_filter = request.GET.get('cuisine', '').strip()
    dietary_filters = request.GET.getlist('dietary')  # Multiple selections allowed
    max_time_filter = request.GET.get('max_time', '').strip()

    recipes = Recipe.objects.all()

    # Apply search
    if query:
        recipes = _search_recipes(query, recipes)

    # Apply cuisine filter
    if cuisine_filter:
        recipes = recipes.filter(tags__id=cuisine_filter)

    # Apply dietary filters (must have ALL selected dietary tags)
    if dietary_filters:
        for dietary_id in dietary_filters:
            recipes = recipes.filter(tags__id=dietary_id)

    # Apply time filter
    if max_time_filter:
        try:
            max_time = int(max_time_filter)
            # Filter recipes where total_time (prep + cook) <= max_time
            # Use Q objects to handle NULL values
            recipes = recipes.filter(
                Q(prep_time__isnull=False) | Q(cook_time__isnull=False)
            ).extra(
                where=["COALESCE(prep_time, 0) + COALESCE(cook_time, 0) <= %s"],
                params=[max_time]
            )
        except ValueError:
            pass  # Ignore invalid time values

    # Remove duplicates (can occur when filtering by multiple tags)
    recipes = recipes.distinct()

    # Add cuisine tag to each recipe for display
    for recipe in recipes:
        cuisine_tag = recipe.tags.filter(category='cuisine').first()
        recipe.cuisine_tag = cuisine_tag.name if cuisine_tag else None

    # Check if filters are active and produced no results
    active_filter_count = (
        (1 if cuisine_filter else 0) +
        len(dietary_filters) +
        (1 if max_time_filter else 0)
    )
    show_filter_warning = (active_filter_count > 0 or query) and not recipes.exists()

    # Get all tags for filter UI
    cuisine_tags = Tag.objects.filter(category='cuisine').order_by('name')
    dietary_tags = Tag.objects.filter(category='dietary').order_by('name')

    context = {
        'recipes': recipes,
        'query': query,
        'cuisine_tags': cuisine_tags,
        'dietary_tags': dietary_tags,
        'selected_cuisine': cuisine_filter,
        'selected_dietary': dietary_filters,
        'selected_max_time': max_time_filter,
        'show_filter_warning': show_filter_warning,
        'active_filter_count': active_filter_count,
    }
    return render(request, 'home.html', context)


def create_recipe(request):
    """
    Create a new recipe via form submission.

    Accepts POST requests with recipe title, description, recipe author (original creator),
    source URL, image URL, ingredients, prep/cook times, comma-separated tags,
    and newline-separated cooking steps.

    Automatically assigns the current logged-in user as the uploader (author field).
    If no user is logged in, assigns the recipe to the first user in the database.

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

            # Cuisine type: add if selected
            cuisine_tag = form.cleaned_data.get('cuisine_type')
            if cuisine_tag:
                recipe.tags.add(cuisine_tag)

            # Additional tags: create or attach
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
        cuisine_tags: Tags categorized as cuisine
        dietary_tags: Tags categorized as dietary restrictions
        other_tags: Other uncategorized tags

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

    # Categorize tags
    tags = recipe.tags.all()
    cuisine_tags = tags.filter(category='cuisine')
    dietary_tags = tags.filter(category='dietary')
    other_tags = tags.filter(category='other')

    context = {
        'recipe': recipe,
        'steps': recipe.steps.all(),
        'tags': tags,
        'cuisine_tags': cuisine_tags,
        'dietary_tags': dietary_tags,
        'other_tags': other_tags,
    }
    return render(request, 'recipe_detail.html', context)


def edit_recipe(request, pk):
    """
    Edit an existing recipe.

    Only the recipe author can edit their own recipes. The form is prepopulated
    with existing recipe data including tags and steps.

    URL Parameters:
        pk (int): Primary key of the recipe to edit

    Context:
        form: RecipeForm instance prepopulated with recipe data
        recipe: The Recipe object being edited

    Returns:
        GET: Rendered edit_recipe.html template with prepopulated form
        POST (valid): Redirect to recipe_detail with success message
        POST (invalid): Rendered edit_recipe.html with form errors
        403: If user is not the recipe author
        404: If recipe not found
    """
    from django.http import Http404

    # Get the recipe
    recipe = (
        Recipe.objects.select_related('author')
        .prefetch_related('tags', 'steps')
        .filter(pk=pk)
        .first()
    )
    if not recipe:
        raise Http404("Recipe not found")

    # Check authorization
    if request.user != recipe.author:
        return HttpResponseForbidden("You don't have permission to edit this recipe")

    if request.method == 'POST':
        form = RecipeForm(request.POST, instance=recipe)
        if form.is_valid():
            # Save the recipe (keeps the same author)
            recipe = form.save()

            # Clear existing tags and steps
            recipe.tags.clear()
            recipe.steps.all().delete()

            # Add cuisine tag
            cuisine_tag = form.cleaned_data.get('cuisine_type')
            if cuisine_tag:
                recipe.tags.add(cuisine_tag)

            # Add additional tags
            tag_names = form.cleaned_data.get('tags_csv', [])
            for name in tag_names:
                tag_obj, _ = Tag.objects.get_or_create(name=name)
                recipe.tags.add(tag_obj)

            # Recreate steps
            steps_text = form.cleaned_data.get('steps_text', '')
            for idx, line in enumerate([s.strip() for s in steps_text.splitlines() if s.strip()], start=1):
                Step.objects.create(recipe=recipe, step_number=idx, instruction_text=line)

            messages.success(request, 'Recipe updated successfully.')
            return redirect('recipe_detail', pk=recipe.pk)
    else:
        # Prepopulate the form with existing data
        # Extract cuisine tag
        cuisine_tag = recipe.tags.filter(category='cuisine').first()

        # Extract other tags (non-cuisine)
        other_tags = recipe.tags.exclude(category='cuisine')
        tags_csv = ', '.join([tag.name for tag in other_tags])

        # Extract steps
        steps_text = '\n'.join([step.instruction_text for step in recipe.steps.all()])

        # Create form with instance and initial data for custom fields
        form = RecipeForm(instance=recipe, initial={
            'cuisine_type': cuisine_tag,
            'tags_csv': tags_csv,
            'steps_text': steps_text,
        })

    return render(request, 'edit_recipe.html', {'form': form, 'recipe': recipe})


def delete_recipe(request, pk):
    """
    Delete an existing recipe.

    Only the recipe author can delete their own recipes. Requires POST method
    for security. Displays confirmation dialog via JavaScript before deletion.

    URL Parameters:
        pk (int): Primary key of the recipe to delete

    Returns:
        POST: Redirect to home with success message after deletion
        403: If user is not the recipe author
        404: If recipe not found
        405: If request method is not POST
    """
    from django.http import Http404, HttpResponseNotAllowed

    # Only allow POST requests for deletion
    if request.method != 'POST':
        return HttpResponseNotAllowed(['POST'])

    # Get the recipe
    recipe = (
        Recipe.objects.select_related('author')
        .filter(pk=pk)
        .first()
    )
    if not recipe:
        raise Http404("Recipe not found")

    # Check authorization
    if request.user != recipe.author:
        return HttpResponseForbidden("You don't have permission to delete this recipe")

    # Store recipe title for success message
    recipe_title = recipe.title

    # Delete the recipe (cascading deletes will handle steps and tags)
    recipe.delete()

    messages.success(request, f'Recipe "{recipe_title}" has been deleted successfully.')
    return redirect('home')


def abtest_view(request):
    """
    Public AB test page at /c50afae showing team member nicknames and
    a button with id="abtest" whose text alternates between
    "kudos" (Variant A) and "thanks" (Variant B).

    The variant is chosen randomly on first visit and persisted to
    `localStorage` by the client-side JavaScript so the user sees a
    consistent variant across page reloads.
    """
    # Team member nicknames (project handles)
    team_nicknames = [
        'zealous-newt',
        'rich-manatee',
        'excited-leopard',
        'motionless-horse'
    ]

    # Stateless per-request 50/50 draw: choose a fresh variant on every page
    # load and log each impression to the DB. This gives per-page-view
    # impression counts while avoiding persistent cookies.
    import random
    variant = 'A' if random.random() < 0.5 else 'B'
    label = 'kudos' if variant == 'A' else 'thanks'

    # Log impression (capture the instance so clicks can link to it)
    impression = None
    try:
        impression = ABTestImpression.objects.create(
            variant=variant,
            path=request.path,
            ip_address=request.META.get('REMOTE_ADDR'),
            user_agent=(request.META.get('HTTP_USER_AGENT') or '')[:2000],
        )
    except Exception:
        # swallow DB exceptions to keep the experiment page available
        impression = None

    return render(request, 'abtest.html', {
        'team_nicknames': team_nicknames,
        'ab_variant': variant,
        'ab_label': label,
        'impression_id': impression.pk if impression is not None else None,
    })



@require_POST
def abtest_click(request):
    """Handle AJAX POST when a visitor clicks the AB test button.

    Expects JSON or form data with:
      - impression_id (optional): integer PK of ABTestImpression
      - variant: 'A' or 'B'

    Returns JSON { 'ok': True }
    """
    try:
        data = request.POST if request.POST else request.body
    except Exception:
        data = request.POST

    # Support JSON body
    variant = request.POST.get('variant') or None
    impression_id = request.POST.get('impression_id') or None
    if not variant:
        # Attempt JSON decode
        try:
            import json
            payload = json.loads(request.body.decode('utf-8') or '{}')
            variant = payload.get('variant')
            impression_id = impression_id or payload.get('impression_id')
        except Exception:
            pass

    if variant not in ('A', 'B'):
        return HttpResponseBadRequest('invalid variant')

    imp = None
    try:
        if impression_id:
            imp = ABTestImpression.objects.filter(pk=int(impression_id)).first()
    except Exception:
        imp = None

    try:
        ABTestClick.objects.create(
            impression=imp,
            variant=variant,
            path=request.path,  # this will be the click endpoint path; impression.path stores page path
            ip_address=request.META.get('REMOTE_ADDR'),
            user_agent=(request.META.get('HTTP_USER_AGENT') or '')[:2000]
        )
    except Exception:
        # swallow DB errors but return success so UX isn't affected
        return JsonResponse({'ok': True})

    return JsonResponse({'ok': True})


def login_view(request):
    """
    Handle user login with username and password.

    GET: Display login form
    POST: Authenticate user and redirect to home on success
    """
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        user = authenticate(request, username=username, password=password)

        if user is not None:
            auth_login(request, user)
            messages.success(request, f'Welcome back, {user.username}!')
            return redirect('home')
        else:
            messages.error(request, 'Invalid username or password.')

    return render(request, 'login.html', {'show_signup': False})


def signup_view(request):
    """
    Handle user registration.

    GET: Display signup form
    POST: Create new user account and redirect to home on success
    """
    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email')
        password1 = request.POST.get('password1')
        password2 = request.POST.get('password2')

        # Validate passwords match
        if password1 != password2:
            messages.error(request, 'Passwords do not match.')
            return render(request, 'login.html', {'show_signup': True})

        # Check if username already exists
        if User.objects.filter(username=username).exists():
            messages.error(request, 'Username already taken.')
            return render(request, 'login.html', {'show_signup': True})

        # Create user
        user = User.objects.create_user(username=username, email=email, password=password1)
        auth_login(request, user)
        messages.success(request, f'Welcome to RecipeHub, {user.username}!')
        return redirect('home')

    return render(request, 'login.html', {'show_signup': True})


def logout_view(request):
    """
    Log out the current user and redirect to home page.
    """
    auth_logout(request)
    messages.success(request, 'You have been logged out.')
    return redirect('home')


def autologin(request, token):
    """
    Autologin endpoint: logs in the `admin` user when visited with the
    correct token. Token is configured via `ADMIN_AUTOLOGIN_TOKEN` in
    environment/settings (defaults to 'autologin' if not set).

    Usage (example): /autologin/autologin-token/  -> redirects to /admin/

    Warning: This endpoint bypasses entering credentials and should only
    be enabled for development or disposable deployments (like a school project).
    Keep the token secret if the deployment is publicly accessible.
    """
    expected = getattr(settings, 'ADMIN_AUTOLOGIN_TOKEN', 'autologin')
    if not token or token != expected:
        return HttpResponseForbidden('Invalid token')

    UserModel = get_user_model()
    try:
        admin = UserModel.objects.get(username='admin')
    except UserModel.DoesNotExist:
        return HttpResponseForbidden('Admin user not found')

    # Ensure Django knows which auth backend to use for this user object
    admin.backend = 'django.contrib.auth.backends.ModelBackend'
    auth_login(request, admin)
    return redirect('/admin/')


def analytics_data_json(request):
    """
    Public analytics JSON endpoint returning AB-test metrics.
    Used by the analytics dashboard to fetch data via JavaScript.
    """
    try:
        total_impressions = ABTestImpression.objects.count()
        total_clicks = ABTestClick.objects.count()

        impressions_by_variant = (
            ABTestImpression.objects.values('variant')
            .annotate(count=Count('id'))
            .order_by('-count')
        )

        clicks_by_variant = (
            ABTestClick.objects.values('variant')
            .annotate(count=Count('id'))
            .order_by('-count')
        )

        # Variant label mapping
        variant_labels = {'A': 'kudos', 'B': 'thanks'}

        data = {
            'total_impressions': total_impressions,
            'total_clicks': total_clicks,
            'impressions_by_variant': [
                {
                    'variant': item['variant'],
                    'label': variant_labels.get(item['variant'], item['variant']),
                    'count': item['count']
                }
                for item in impressions_by_variant
            ],
            'clicks_by_variant': [
                {
                    'variant': item['variant'],
                    'label': variant_labels.get(item['variant'], item['variant']),
                    'count': item['count']
                }
                for item in clicks_by_variant
            ],
        }
    except Exception as e:
        data = {'error': str(e)}

    return JsonResponse(data)


def analytics_view(request):
    """
    Render the analytics dashboard HTML page.
    The page fetches JSON data via JavaScript from the analytics endpoint.
    """
    return render(request, 'analytics.html')

