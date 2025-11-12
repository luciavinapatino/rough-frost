from django import forms
from .models import Recipe, Ingredient, Step


class RecipeForm(forms.ModelForm):
    """Form for creating and editing recipes."""
    
    class Meta:
        model = Recipe
        fields = ['title', 'description', 'image', 'image_url']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Recipe name'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Brief description of the recipe'}),
            'image': forms.FileInput(attrs={'class': 'form-control', 'accept': 'image/*'}),
            'image_url': forms.URLInput(attrs={'class': 'form-control', 'placeholder': 'Or enter image URL (optional)'}),
        }
        labels = {
            'title': 'Recipe Title',
            'description': 'Description',
            'image': 'Upload Image (optional)',
            'image_url': 'Or Image URL (optional)',
        }


class IngredientForm(forms.ModelForm):
    """Form for a single ingredient."""
    
    class Meta:
        model = Ingredient
        fields = ['name', 'amount']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ingredient name'}),
            'amount': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Amount (e.g., 2 cups)'}),
        }
        labels = {
            'name': 'Ingredient',
            'amount': 'Amount',
        }


class StepForm(forms.ModelForm):
    """Form for a single instruction step."""
    
    class Meta:
        model = Step
        fields = ['instruction_text']
        widgets = {
            'instruction_text': forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'Enter instruction...'}),
        }
        labels = {
            'instruction_text': 'Instruction',
        }

