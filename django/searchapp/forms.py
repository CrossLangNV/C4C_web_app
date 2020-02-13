from django import forms
from .models import Website, Document


class DocumentForm(forms.ModelForm):
    class Meta:
        model = Document
        fields = ['title', 'date', 'acceptance_state', 'url', 'content']


class WebsiteForm(forms.ModelForm):
    class Meta:
        model = Website
        fields = ['name', 'url', 'content']
