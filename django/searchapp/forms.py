from django import forms

from .models import Website, Document, EiopaDocument


class WebsiteForm(forms.ModelForm):
    class Meta:
        model = Website
        fields = ['name', 'url', 'content']


class DocumentForm(forms.ModelForm):
    class Meta:
        model = Document
        fields = ['title', 'date', 'acceptance_state', 'url', 'content']
        widgets = {
            'date': forms.DateInput(attrs={
                'type': 'date'
            })
        }


class ExtendedDocumentForm(forms.Form):
    pass
