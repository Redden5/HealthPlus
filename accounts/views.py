from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages

def login_view(request):
    if request.method == 'POST':
        action = request.POST.get('action')

        # Create Account
        if action == 'createAccount':
            return redirect('/patients/setup/')
        #Get data from form
        username = request.POST.get('username')
        password = request.POST.get('password')

        print('Attempting auth')

        #Check if user exists and password is valid
        user = authenticate(request, username=username, password=password)

        print('user authed')
        if user is not None:
            login(request, user)
            return redirect_by_role(user) #dashboard page
        else:
            #handle error
            messages.error(request, 'Username or password is incorrect')
            return render(request, 'accounts/login.html')

    return render(request, 'accounts/login.html')

def redirect_by_role(user):
    print("User: ", user.username)
    print("Groups: ", user.groups.values_list('name', flat=True))

    if user.groups.filter(name='Doctor').exists():
        return redirect('/doctor/dashboard/')
    elif user.groups.filter(name='Patient').exists():
        return redirect('/patients/dashboard/')
    else: return redirect('/')