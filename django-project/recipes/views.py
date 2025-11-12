from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login as auth_login, logout as auth_logout
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.contrib.auth.decorators import login_required
from django.views import View
from django.http import HttpResponseRedirect
from django.urls import reverse
from .models import Recipe, Ingredient, Step
from .forms import RecipeForm

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


class LoginView(View):
    template_name = "registration/login.html"

    def get(self, request):
        return render(request, self.template_name, {"form": AuthenticationForm()})

    def post(self, request):
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            auth_login(request, user)
            request.session["user"] = {"username": user.username}
            return HttpResponseRedirect(reverse("home"))
        return render(request, self.template_name, {"form": form, "error": True})

class LogoutView(View):
    def post(self, request):
        auth_logout(request)
        return HttpResponseRedirect(reverse("home"))

class RegisterView(View):
    template_name = "registration/register.html"

    def get(self, request):
        return render(request, self.template_name, {"form": UserCreationForm()})

    def post(self, request):
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            auth_login(request, user)
            request.session["user"] = {"username": user.username}
            return HttpResponseRedirect(reverse("home"))
        return render(request, self.template_name, {"form": form, "error": True})


@login_required
def create_recipe(request):
    """View for creating a new recipe with ingredients and instructions."""
    if request.method == 'POST':
        recipe_form = RecipeForm(request.POST, request.FILES)
        
        if recipe_form.is_valid():
            recipe = recipe_form.save(commit=False)
            recipe.author = request.user
            recipe.save()
            
            # Handle ingredients
            ingredient_names = request.POST.getlist('ingredient_name')
            ingredient_amounts = request.POST.getlist('ingredient_amount')
            for name, amount in zip(ingredient_names, ingredient_amounts):
                if name.strip():  # Only save if name is not empty
                    Ingredient.objects.create(
                        recipe=recipe,
                        name=name.strip(),
                        amount=amount.strip() if amount.strip() else ''
                    )
            
            # Handle instructions (steps)
            instructions = request.POST.getlist('instruction')
            for idx, instruction in enumerate(instructions, start=1):
                if instruction.strip():  # Only save if instruction is not empty
                    Step.objects.create(
                        recipe=recipe,
                        step_number=idx,
                        instruction_text=instruction.strip()
                    )
            
            return redirect('recipe_detail', recipe_id=recipe.id)
    else:
        recipe_form = RecipeForm()
    
    return render(request, 'recipes/create_recipe.html', {
        'recipe_form': recipe_form,
    })


def recipe_detail(request, recipe_id):
    """View for displaying a single recipe."""
    recipe = get_object_or_404(Recipe, id=recipe_id)
    ingredients = recipe.ingredients.all()
    steps = recipe.steps.all()
    
    return render(request, 'recipes/recipe_detail.html', {
        'recipe': recipe,
        'ingredients': ingredients,
        'steps': steps,
    })


@login_required
def my_recipes(request):
    """View for displaying all recipes created by the logged-in user."""
    recipes = Recipe.objects.filter(author=request.user)
    return render(request, 'recipes/my_recipes.html', {
        'recipes': recipes,
    })

