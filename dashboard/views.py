from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.views.decorators.cache import never_cache
from skills.models import Skill, UserStreak
import json

def home(request):
    return render(request, 'dashboard/home.html')

def custom_404(request, exception):
    return render(request, '404.html', status=404)

@login_required
@never_cache
def dashboard_view(request):
    skills = Skill.objects.filter(user=request.user, is_archived=False)
    
    total_skills = skills.count()
    
    # Calculate average retention
    if total_skills > 0:
        avg_retention = sum(s.retention_score for s in skills) / total_skills
    else:
        avg_retention = 0
    
    # Only mark as at-risk if retention is actually low
    at_risk = [
        s for s in skills
        if s.retention_score < 50  # Only skills below 50% are "at risk"
    ]

    # Get or create streak for user
    user_streak, created = UserStreak.objects.get_or_create(user=request.user)
    
    # Charts data
    skill_names = [s.name for s in skills]
    retention_scores = [s.retention_score for s in skills]
    
    context = {
        'skills': skills,
        'total_skills': total_skills,
        'avg_retention': round(avg_retention, 2),
        'at_risk_count': len(at_risk),
        'skill_names': json.dumps(skill_names),
        'retention_scores': json.dumps(retention_scores),
        'streak': user_streak,
    }
    
    return render(request, 'dashboard/dashboard.html', context)