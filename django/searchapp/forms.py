from django import forms
from . import models
import uuid

class CreateDocument(forms.Form):
    # class Meta:
    #     model = models.Document
    #     fields = ['title', 'date', 'acceptance_state', 'url', 'website']
    id = forms.UUIDField(disabled=True)
    title = forms.CharField(max_length=150)
    date = forms.DateField()
    acceptance_state = forms.ChoiceField(choices=models.AcceptanceState.choices)
    url = forms.CharField(max_length=150)

