from django.urls import path
from . import views

urlpatterns = [
    # This maps 'http://127.0.0.1:8000/accounts/login/' to your login_view
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
]