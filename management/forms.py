from django import forms
from .models import Class, Attendance

class ClassForm(forms.ModelForm):
    """
    Form for Teachers to create or update a class.
    """
    class Meta:
        model = Class
        fields = ['name', 'start_time', 'end_time', 'description']
        widgets = {
            'start_time': forms.TimeInput(attrs={'type': 'time'}),
            'end_time': forms.TimeInput(attrs={'type': 'time'}),
            'description': forms.Textarea(attrs={'rows': 4}),
        }

    def __init__(self, *args, **kwargs):
        self.teacher = kwargs.pop('teacher', None)
        super().__init__(*args, **kwargs)

    def save(self, commit=True):
        instance = super().save(commit=False)
        if self.teacher:
            instance.teacher = self.teacher
        if commit:
            instance.save()
        return instance

class MarkAttendanceForm(forms.Form):
    """
    This form is used as a base for the formset, but we'll use
    a custom form structure in the template for simplicity.
    This file is here to show what a formset-based
    approach would look like.
    
    In our `mark_attendance.html` template, we will build the
    form manually to POST data for each student.
    """
    student_id = forms.IntegerField(widget=forms.HiddenInput())
    status = forms.ChoiceField(choices=Attendance.STATUS_CHOICES, widget=forms.RadioSelect)