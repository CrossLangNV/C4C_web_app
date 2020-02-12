from django import forms
from .models import AcceptanceState

class CreateDocument(forms.Form):
    title = forms.CharField(max_length=150)
    date = forms.DateField()
    acceptance_state = forms.ChoiceField(choices=AcceptanceState.choices)
    url = forms.CharField(max_length=150)
    content = forms.CharField(widget=forms.Textarea)

class CreateWebsite(forms.Form):
    name = forms.CharField(max_length=32)
    url = forms.CharField(max_length=100)
    content = forms.CharField(widget=forms.Textarea)