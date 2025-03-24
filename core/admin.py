from django.contrib import admin

# Register your models here.
from .models import Recipe  # Import your Recipe model

admin.site.register(Recipe)