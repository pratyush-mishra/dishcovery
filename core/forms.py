from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import User, Recipe, Meal, Rating

class CustomUserCreationForm(UserCreationForm):
    class Meta:
        model = User
        fields = ('username', 'email', 'password1', 'password2')

class RecipeForm(forms.ModelForm):
    class Meta:
        model = Recipe
        exclude = ['author']
        widgets = {
            'ingredients': forms.Textarea(attrs={'rows': 5, 'placeholder': 'Enter ingredients, one per line'}),
            'tags': forms.TextInput(attrs={'placeholder': 'Enter tags separated by commas'})
        }

class MealLogForm(forms.ModelForm):
    class Meta:
        model = Meal
        fields = ['recipe']

class RatingForm(forms.ModelForm):
    class Meta:
        model = Rating
        fields = ['score', 'comment']
        widgets = {
            'score': forms.NumberInput(attrs={'min': 1, 'max': 5, 'step': 0.5}),
            'comment': forms.Textarea(attrs={'rows': 3})
        }

class RecipeSearchForm(forms.Form):
    search_query = forms.CharField(required=False, label='', 
                                  widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Search by name or ingredient'}))
    tags = forms.CharField(required=False, label='Tags',
                          widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter tags separated by commas'}))
    min_protein = forms.FloatField(required=False, label='Min Protein (g)')
    max_calories = forms.FloatField(required=False, label='Max Calories')