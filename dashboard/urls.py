from django.urls import path
from .views import dashboard_view
from . import views

urlpatterns = [
    path('', views.home, name="home"),
    path('dashboard/', views.dashboard_view, name="dashboard"),
]