from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login, logout
from django.db.models import Q, Avg, Sum
from collections import defaultdict
from django.http import HttpResponse
from django.contrib import messages
from django.views.generic import ListView, DetailView, CreateView, UpdateView
from django.urls import reverse_lazy
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.forms import AuthenticationForm

from .models import User, Recipe, Meal, Rating
from .forms import CustomUserCreationForm, RecipeForm, MealLogForm, RatingForm, RecipeSearchForm

# Authentication Views
def register_view(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('home')
    else:
        form = CustomUserCreationForm()
    return render(request, 'auth/register.html', {'form': form})

def login_view(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            return redirect('home')
    else:
        form = AuthenticationForm()
    return render(request, 'auth/login.html', {'form': form})

def logout_view(request):
    logout(request)
    return redirect('home')

@login_required
def profile_view(request):
    user = request.user

    # Retrieve meals logged by the user, assuming each meal is linked to a Recipe
    meals = Meal.objects.filter(user=user).order_by('-logged_at')
    
    # Retrieve ratings provided by the user
    ratings = Rating.objects.filter(user=user)

    # Calculate the average rating (default to 0 if none exist)
    average_rating = ratings.aggregate(Avg('score'))['score__avg'] or 0

    # Count total meal logs
    total_meal_logs = meals.count()

    # Calculate nutrition summary by aggregating values from each meal's related Recipe.
    # The Recipe model includes 'calories', 'protein', 'carbs', and 'fat' fields.
    nutrition_data = meals.aggregate(
        total_calories=Sum('recipe__calories'),
        total_protein=Sum('recipe__protein'),
        total_carbs=Sum('recipe__carbs'),
        total_fat=Sum('recipe__fat'),
    )
    nutrition_summary = {
        'calories': nutrition_data.get('total_calories') or 0,
        'protein': nutrition_data.get('total_protein') or 0,
        'carbs': nutrition_data.get('total_carbs') or 0,
        'fat': nutrition_data.get('total_fat') or 0,
    }

    # Retrieve the user's recipe reviews
    recipe_reviews = Rating.objects.filter(user=user).order_by('-rated_at')

    context = {
        'user': user,
        'meals': meals,
        'ratings': ratings,
        'average_rating': average_rating,
        'total_meal_logs': total_meal_logs,
        'nutrition_summary': nutrition_summary,
        'recipe_reviews': recipe_reviews,
    }

    return render(request, 'auth/profile.html', context)

# Recipe Views
class RecipeListView(ListView):
    model = Recipe
    template_name = 'recipes/recipe_list.html'
    context_object_name = 'recipes'
    paginate_by = 12
    
    def get_queryset(self):
        queryset = Recipe.objects.all()
        form = RecipeSearchForm(self.request.GET)
        
        if form.is_valid():
            search_query = form.cleaned_data.get('search_query')
            tags = form.cleaned_data.get('tags')
            min_protein = form.cleaned_data.get('min_protein')
            max_calories = form.cleaned_data.get('max_calories')
            
            if search_query:
                queryset = queryset.filter(
                    Q(name__icontains=search_query) | 
                    Q(ingredients__icontains=search_query)
                )
            
            if tags:
                tag_list = [tag.strip() for tag in tags.split(',')]
                for tag in tag_list:
                    queryset = queryset.filter(tags__icontains=tag)
            
            if min_protein:
                queryset = queryset.filter(protein__gte=min_protein)
                
            if max_calories:
                queryset = queryset.filter(calories__lte=max_calories)
                
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search_form'] = RecipeSearchForm(self.request.GET)
        return context

class RecipeDetailView(DetailView):
    model = Recipe
    template_name = 'recipes/recipe_detail.html'
    context_object_name = 'recipe'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        recipe = self.get_object()
        
        # Add rating form if user is authenticated
        if self.request.user.is_authenticated:
            user_rating = Rating.objects.filter(
                user=self.request.user, 
                recipe=recipe
            ).first()
            
            if user_rating:
                context['rating_form'] = RatingForm(instance=user_rating)
                context['user_rating'] = user_rating
            else:
                context['rating_form'] = RatingForm()
        
        # Get all ratings for this recipe
        context['ratings'] = recipe.ratings.all().order_by('-rated_at')
        
        # Meal logging form
        context['meal_form'] = MealLogForm(initial={'recipe': recipe})
        
        # Similar recipes based on tags
        recipe_tags = recipe.tags.split(',')
        similar_recipes = Recipe.objects.filter(
            tags__icontains=recipe_tags[0]
        ).exclude(id=recipe.id)[:4]
        context['similar_recipes'] = similar_recipes
        
        return context

class RecipeCreateView(LoginRequiredMixin, CreateView):
    model = Recipe
    form_class = RecipeForm
    template_name = 'recipes/recipe_form.html'
    
    def form_valid(self, form):
        form.instance.author = self.request.user
        return super().form_valid(form)

class RecipeUpdateView(LoginRequiredMixin, UpdateView):
    model = Recipe
    form_class = RecipeForm
    template_name = 'recipes/recipe_form.html'
    
    def dispatch(self, request, *args, **kwargs):
        recipe = self.get_object()
        if recipe.author != request.user and not request.user.is_admin:
            messages.error(request, "You don't have permission to edit this recipe.")
            return redirect('recipe_detail', pk=recipe.pk)
        return super().dispatch(request, *args, **kwargs)

# Meal Logging
@login_required
def log_meal(request, recipe_id=None):
    if request.method == 'POST':
        form = MealLogForm(request.POST)
        if form.is_valid():
            meal = form.save(commit=False)
            meal.user = request.user
            meal.save()
            messages.success(request, f"Successfully logged {meal.recipe.name}")
            return redirect('meal_list')
    else:
        if recipe_id:
            recipe = get_object_or_404(Recipe, id=recipe_id)
            form = MealLogForm(initial={'recipe': recipe})
        else:
            form = MealLogForm()
    
    return render(request, 'meals/meal_form.html', {'form': form})

@login_required
def meal_list(request):
    meals = Meal.objects.filter(user=request.user).order_by('-logged_at')
    
    # Group meals by date
    meals_by_date = defaultdict(list)
    
    total_calories = 0
    total_carbs = 0
    total_proteins = 0
    total_fats = 0
    
    for meal in meals:
        date = meal.logged_at.date()
        if date not in meals_by_date:
            meals_by_date[date] = []
        meals_by_date[date].append(meal)
        total_calories += meal.recipe.calories
        total_carbs += meal.recipe.carbs
        total_proteins += meal.recipe.protein
        total_fats += meal.recipe.fat
    
    meals_by_date_with_calories = {}
    for date, meals in meals_by_date.items():
        daily_calories = sum(meal.recipe.calories for meal in meals)
        meals_by_date_with_calories[date] = {
            'meals': meals,
            'daily_calories': daily_calories
        }
    
    context = {
        'meals_by_date': meals_by_date,
        'total_calories': total_calories,
        'meals_by_date_with_calories': meals_by_date_with_calories,
        'total_carbs': total_carbs,
        'total_proteins': total_proteins,
        'total_fats': total_fats
    }
    return render(request, 'meals/meal_list.html', context)

# Rating System
@login_required
def rate_recipe(request, recipe_id):
    recipe = get_object_or_404(Recipe, id=recipe_id)
    
    # Check if user already rated this recipe
    existing_rating = Rating.objects.filter(
        user=request.user,
        recipe=recipe
    ).first()
    
    if request.method == 'POST':
        form = RatingForm(request.POST, instance=existing_rating)
        if form.is_valid():
            rating = form.save(commit=False)
            if not existing_rating:
                rating.user = request.user
                rating.recipe = recipe
            rating.save()
            messages.success(request, "Your rating has been saved!")
            return redirect('recipe_detail', pk=recipe.id)
    else:
        if existing_rating:
            form = RatingForm(instance=existing_rating)
        else:
            form = RatingForm()
    
    context = {
        'form': form,
        'recipe': recipe
    }
    return render(request, 'recipes/recipe_rating.html', context)

# Recipe Recommendations
@login_required
def recipe_recommendations(request):
    # Get recipes rated highly by the user
    user_high_ratings = Rating.objects.filter(
        user=request.user,
        score__gte=4.0
    )
    
    # Extract tags from highly rated recipes
    liked_tags = []
    for rating in user_high_ratings:
        recipe_tags = rating.recipe.tags.split(',')
        liked_tags.extend([tag.strip() for tag in recipe_tags])
    
    # Count tag occurrences to find preferences
    from collections import Counter
    tag_counter = Counter(liked_tags)
    favorite_tags = [tag for tag, count in tag_counter.most_common(5)]
    
    # Find recipes with those tags that user hasn't rated yet
    user_rated_recipes = Rating.objects.filter(user=request.user).values_list('recipe_id', flat=True)
    
    recommended_recipes = []
    for tag in favorite_tags:
        tag_recipes = Recipe.objects.filter(
            tags__icontains=tag
        ).exclude(
            id__in=user_rated_recipes
        )
        recommended_recipes.extend(list(tag_recipes))
    
    # Remove duplicates
    recommended_recipes = list({recipe.id: recipe for recipe in recommended_recipes}.values())
    
    context = {
        'recommended_recipes': recommended_recipes[:10],  # Top 10 recommendations
        'favorite_tags': favorite_tags,
    }
    return render(request, 'recipes/recipe_recommendations.html', context)

# Sharing functionality
def share_recipe(request, recipe_id):
    recipe = get_object_or_404(Recipe, id=recipe_id)
    
    # Generate a printer-friendly version
    return render(request, 'recipes/recipe_share.html', {'recipe': recipe})

# Home page view
def home_view(request):
    # Get popular recipes (highest average rating)
    popular_recipes = Recipe.objects.annotate(
        avg_rating=Avg('ratings__score')
    ).order_by('-avg_rating')[:6]
    
    # Get newest recipes
    newest_recipes = Recipe.objects.order_by('-id')[:6]
    
    context = {
        'popular_recipes': popular_recipes,
        'newest_recipes': newest_recipes,
        'search_form': RecipeSearchForm(),
    }
    return render(request, 'home.html', context)