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
    """Simple home page view."""
    return render(request, 'home.html')

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

