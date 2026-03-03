from django.urls import path
from . import views

urlpatterns = [
    path('setup/', views.profile_setup, name='profile_setup'),
    path('preferences/', views.preferences_setup, name='preferences_setup'),
    path('consent/', views.consent_setup, name='consent_setup'),
    #path('dashboard/', views.dashboard_setup, name='dashboard'),
    #path('settings/', views.profile_setup, name='settings'),
    #path('profile/', views.profile_setup, name='profile_view'),
]