from django.urls import path
from . import views

urlpatterns = [
    path('create/', views.create_skill, name='create_skill'),
    path('edit/<int:id>/', views.edit_skill, name='edit_skill'),
    path('delete/<int:id>/', views.delete_skill, name='delete_skill'),
    path('practice/<int:id>/', views.add_practice, name='add_practice'),
    path('skills/', views.skills_list, name='skills_list'),
    path('practice-history/', views.practice_history, name='practice_history'),
    path('skill/<int:id>/', views.skill_detail, name='skill_detail'),
]