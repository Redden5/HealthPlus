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
class QuickEditForm(forms.ModelForm):
    class Meta:
        model = PatientProfile
        fields = ['height', 'weight', 'blood_type','date_of_birth']
        widgets = {
            'height': forms.TextInput(attrs={'class': 'modal-input'}),
            'weight': forms.TextInput(attrs={'class': 'modal-input'}),
            'blood_type': forms.TextInput(attrs={'class': 'modal-input'}),
            'date_of_birth': forms.TextInput(attrs={'class': 'modal-input'}),
            'allergies': forms.TextInput(attrs={'class': 'modal-input'}),
            'medical_conditions': forms.TextInput(attrs={'class': 'modal-input'}),
            'notification_frequency': forms.TextInput(attrs={'class': 'modal-input'}),
        }