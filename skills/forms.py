from django import forms
from django.utils import timezone
from .models import Skill, PracticeLog

class SkillForm(forms.ModelForm):
    class Meta:
        model = Skill
        fields = ['name', 'category', 'priority']

        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter skill (e.g., Python)'}),
            'category': forms.Select(attrs={'class': 'form-control'}),
            'priority': forms.Select(attrs={'class': 'form-control'}),
        }

class PracticeLogForm(forms.ModelForm):
    class Meta:
        model = PracticeLog
        fields = ['date', 'quality', 'notes']

        widgets = {
            'date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control', 'max': timezone.now().date().isoformat()}),
            'quality': forms.Select(attrs={'class': 'form-control'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'What did you practice?'}),
        }

    def clean_date(self):
        date = self.cleaned_data['date']
        if date > timezone.now().date():
            raise forms.ValidationError("Practice date cannot be in the future!!")
        return date