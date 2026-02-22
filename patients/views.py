from django.shortcuts import render, redirect

# Create your views here.

from patients.forms import ConsentForm


def profile_setup(request):
    # For now, just render the page.
    # Later, we will add logic here to save the form data.
    return render(request, 'patients/profile_setup.html')

def preferences_setup(request):
    return render(request, 'patients/preferences_setup.html')
def consent_setup(request):
    if request.method == "POST":
        form = ConsentForm(request.POST)
        if form.is_valid():
            profile = form.save(commit=False)
            profile.user = request.user
            profile.save()
            return redirect('dashboard')
    else:
        form = ConsentForm
    return render(request,'patients/review_consent.html',{'form':form})