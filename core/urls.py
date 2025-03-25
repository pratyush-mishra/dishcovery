from django.urls import path
from . import views

urlpatterns = [
    # Authentication
    path('register/', views.register_view, name='register'),
    path('profile/', views.profile_view, name='profile'),
    path('auth/login/', views.login_view, name='login'),
    path('auth/logout/', views.logout_view, name='logout'),
    
    # Recipes
    path('', views.home_view, name='home'),
    path('recipes/', views.RecipeListView.as_view(), name='recipe_list'),
    path('recipes/<int:pk>/', views.RecipeDetailView.as_view(), name='recipe_detail'),
    path('recipes/create/', views.RecipeCreateView.as_view(), name='recipe_create'),
    path('recipes/<int:pk>/edit/', views.RecipeUpdateView.as_view(), name='recipe_edit'),
    path('recipes/<int:recipe_id>/rate/', views.rate_recipe, name='rate_recipe'),
    path('recipes/<int:recipe_id>/share/', views.share_recipe, name='share_recipe'),
    
    # Meals
    path('meals/', views.meal_list, name='meal_list'),
    path('meals/log/', views.log_meal, name='log_meal'),
    path('meals/log/<int:recipe_id>/', views.log_meal, name='log_meal_with_recipe'),
    
    # Recommendations
    path('recommendations/', views.recipe_recommendations, name='recommendations'),
    path('ajax/recipes/', views.ajax_recipe_search, name='ajax_recipe_search'),

]