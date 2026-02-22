from django import forms
from .models import PatientProfile

class ConsentForm(forms.ModelForm):
    class Meta:
        model = PatientProfile
        fields = ['terms_agreed', 'private_policy', 'electronic_policy']

    def clean_terms_agreed(self):
        data = self.cleaned_data.get('terms_agreed')
        if not data:
            raise forms.ValidationError("Please accept terms to continue.")
        return data