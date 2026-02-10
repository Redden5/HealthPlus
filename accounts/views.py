from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages

def login_view(request):
    if request.method == 'POST':
        #Get data from form
        username = request.POST.get('username')
        password = request.POST.get('password')

        #Check if user exists and password is valid
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('/') #dashboard page
        else:
            #handle error
            messages.error(request, 'Username or password is incorrect')
            return render(request, 'accounts/login.html')

    return render(request, 'accounts/login.html')