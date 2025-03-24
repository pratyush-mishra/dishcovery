from django.db import models
from django.contrib.auth.models import AbstractUser
from django.urls import reverse

class User(AbstractUser):
    """Extended user model with additional fields"""
    is_admin = models.BooleanField(default=False)
    
    def __str__(self):
        return self.username

class Recipe(models.Model):
    """Recipe model as shown in ER diagram"""
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=30)
    recipe = models.TextField()
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_recipes')
    cooking_time = models.IntegerField(help_text="Cooking time in minutes")
    image = models.ImageField(upload_to='recipes/', blank=True, null=True)
    protein = models.FloatField()
    carbs = models.FloatField()
    fat = models.FloatField()
    calories = models.FloatField()
    ingredients = models.TextField()
    tags = models.TextField(help_text="Comma separated tags")
    
    def __str__(self):
        return self.name
    
    def get_absolute_url(self):
        return reverse("recipe_detail", kwargs={"pk": self.pk})
    
    def get_average_rating(self):
        ratings = self.ratings.all()
        if ratings:
            return sum(rating.score for rating in ratings) / len(ratings)
        return 0

class Meal(models.Model):
    """Meal model for logging user meals"""
    id = models.AutoField(primary_key=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='meals')
    recipe = models.ForeignKey(Recipe, on_delete=models.CASCADE, related_name='meals')
    logged_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.user.username}'s meal: {self.recipe.name} on {self.logged_at.date()}"

class Rating(models.Model):
    """Rating model for user recipe ratings"""
    id = models.AutoField(primary_key=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='ratings')
    recipe = models.ForeignKey(Recipe, on_delete=models.CASCADE, related_name='ratings')
    score = models.FloatField(help_text="Rating from 1-5")
    rated_at = models.DateTimeField(auto_now_add=True)
    comment = models.TextField(blank=True, null=True)
    
    class Meta:
        # Ensure a user can only rate a recipe once
        unique_together = ('user', 'recipe')
    
    def __str__(self):
        return f"{self.user.username}'s rating for {self.recipe.name}: {self.score}"