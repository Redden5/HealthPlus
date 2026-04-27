from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.contrib import messages
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from .notifications import send_password_reset_email

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

def logout_view(request):
    logout(request)
    return redirect('/accounts/login/')

def forgot_password(request):
    if request.method == 'POST':
        email = request.POST.get('email', '').strip()

        if not email:
            messages.error(request, 'Please enter your email address.')
            return render(request, 'accounts/forgot_password.html')

        try:
            user = User.objects.get(email=email)
            token = default_token_generator.make_token(user)
            uid = urlsafe_base64_encode(force_bytes(user.pk))

            reset_link = request.build_absolute_uri(
                f'/accounts/reset-password/{uid}/{token}/'
            )

            first_name = user.first_name or user.username
            send_password_reset_email(user.email, first_name, reset_link)
        except User.DoesNotExist:
            # Don't reveal whether an account exists
            pass

        return redirect('/accounts/password-reset-sent/')

    return render(request, 'accounts/forgot_password.html')


def password_reset_sent(request):
    return render(request, 'accounts/password_reset_sent.html')


def reset_password_confirm(request, uidb64, token):
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None

    token_valid = user is not None and default_token_generator.check_token(user, token)

    if not token_valid:
        return render(request, 'accounts/reset_password_confirm.html', {'invalid_link': True})

    if request.method == 'POST':
        new_password = request.POST.get('new_password', '')
        confirm_password = request.POST.get('confirm_password', '')

        errors = []

        if not new_password:
            errors.append('Password is required.')
        elif new_password != confirm_password:
            errors.append('Passwords do not match.')
        else:
            try:
                validate_password(new_password, user)
            except ValidationError as e:
                errors.extend(e.messages)

        if errors:
            return render(request, 'accounts/reset_password_confirm.html', {
                'errors': errors,
                'uidb64': uidb64,
                'token': token,
            })

        user.set_password(new_password)
        user.save()
        messages.success(request, 'Your password has been reset. You can now log in.')
        return redirect('/accounts/login/')

    return render(request, 'accounts/reset_password_confirm.html', {
        'uidb64': uidb64,
        'token': token,
    })


def redirect_by_role(user):
    print("User: ", user.username)
    print("Groups: ", user.groups.values_list('name', flat=True))

    if user.groups.filter(name='Doctor').exists():
        return redirect('/doctors/dashboard/')
    elif user.groups.filter(name='Patient').exists():
        return redirect('/patients/dashboard/')
    elif user.groups.filter(name='Receptionist').exists():
        return redirect('/receptionist/dashboard/')
    else:
        return redirect('/')