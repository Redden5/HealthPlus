from django.urls import path
from . import views
app_name = 'patients'

urlpatterns = [
    path('setup/', views.profile_setup, name='profile_setup'),
    path('preferences/', views.preferences_setup, name='preferences_setup'),
    path('consent/', views.consent_setup, name='consent_setup'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('account/', views.account_profile, name='account'),
    path('edit_profile/', views.edit_profile, name='edit_profile'),
    #path('settings/', views.profile_setup, name='settings'),
]