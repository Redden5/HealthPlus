from django.urls import path
from . import views

urlpatterns = [
    # This maps 'http://127.0.0.1:8000/accounts/login/' to your login_view
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('forgot-password/', views.forgot_password, name='forgot_password'),
    path('password-reset-sent/', views.password_reset_sent, name='password_reset_sent'),
    path('reset-password/<uidb64>/<token>/', views.reset_password_confirm, name='reset_password_confirm'),
]