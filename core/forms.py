from django import forms
from .models import Task

class TaskForm(forms.ModelForm):
    due_date = forms.DateField(
        input_formats=['%d-%m-%Y'],
        widget=forms.DateInput(attrs={'placeholder': 'DD-MM-YYYY'}),
        required=False
    )
    
    class Meta:
        model = Task
        fields = ["title", "description", "due_date", "status", "priority"]
        widgets = {
            'title': forms.TextInput(attrs={'placeholder': 'Enter task title'}),
            'description': forms.Textarea(attrs={'placeholder': 'Enter task description'}),
        }
