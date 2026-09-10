from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from .forms import SkillForm, PracticeLogForm
from .models import Skill, PracticeLog
import json
from datetime import timedelta
from django.utils import timezone

@login_required
def create_skill(request):
    if request.method == "POST":
        form = SkillForm(request.POST)
        if form.is_valid():
            skill = form.save(commit=False)
            skill.user = request.user
            skill.save()
            return redirect('dashboard')
    else:
        form = SkillForm()

    return render(request, 'skills/create_skill.html', {'form': form})

def edit_skill(request, id):
    skill = get_object_or_404(Skill, id=id, user=request.user)

    if request.method == 'POST':
        form = SkillForm(request.POST, instance=skill)
        if form.is_valid():
            form.save()
            return redirect('dashboard')
    else:
        form = SkillForm(instance=skill)

    return render(request, 'skills/create_skill.html', {'form': form})

def delete_skill(request, id):
    skill = get_object_or_404(Skill, id=id, user=request.user)

    if request.method == 'POST':
        skill.delete()
        return redirect('dashboard')
    
    return render(request, 'skills/delete_confirm.html', {'skill': skill})

def add_practice(request, id):
    skill = get_object_or_404(Skill, id=id, user=request.user)
    
    if request.method == 'POST':
        form = PracticeLogForm(request.POST)
        if form.is_valid():
            practice = form.save(commit=False)
            practice.skill = skill
            # The save() method will automatically calculate post_practice_retention
            practice.save()
            messages.success(request, "Practice logged successfully!")
            return redirect('dashboard')
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = PracticeLogForm(initial={'date': timezone.now().date()})
    
    return render(request, 'skills/add_practice.html', {'form': form, 'skill': skill})

@login_required
def skills_list(request):
    skills = Skill.objects.filter(user=request.user, is_archived=False)

    return render(request, 'skills/skills_list.html', {'skills': skills})

@login_required
def practice_history(request):
    logs = PracticeLog.objects.filter(skill__user=request.user).order_by('-date')

    return render(request, 'skills/practice_history.html', {'logs': logs})

@login_required
def skill_detail(request, id):
    skill = get_object_or_404(Skill, id=id, user=request.user)

    logs = skill.practicelog_set.all().order_by('date')

    # Retention Timeline (last 10 days)
    today = timezone.now().date()
    days = [today - timedelta(days=i) for i in range(9, -1, -1)]

    retention_values = []

    for day in days:
        last_log = logs.filter(date__lte=day).order_by('-date').first()

        if not last_log:
            days_passed = (day - skill.created_at.date()).days
            score = 100 - (days_passed * skill.decay_rate)
        else:
            days_passed = (day - last_log.date).days

            boost_map = {
                    'LOW': 0,
                    'MEDIUM': 5,
                    'DEEP': 10
                }

            boost = boost_map.get(last_log.quality, 0)
            score = 100 - (days_passed * skill.decay_rate) + boost
        
        score = max(0, min(100, round(score, 2)))
        retention_values.append(score)
        
    context = {
        'skill': skill,
        'logs': logs,
        'dates': json.dumps([d.strftime("%Y-%m-%d") for d in days]),
        'retention_values': json.dumps(retention_values),
    }

    return render(request, 'skills/skill_detail.html', context)