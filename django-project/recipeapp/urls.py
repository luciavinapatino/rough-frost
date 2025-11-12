"""
Main URL configuration for the recipeapp project.

Routes all requests to the appropriate app handlers:
    /admin/    - Django admin interface
    /          - recipes app routes (home, create, detail)
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from recipes import views as recipes_views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('recipes.urls')),
    path("", recipes_views.home, name="home"),
    path("login/", recipes_views.LoginView.as_view(), name="login"),
    path("logout/", recipes_views.LogoutView.as_view(), name="logout"),
    path("register/", recipes_views.RegisterView.as_view(), name="register")
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

