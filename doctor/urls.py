from django.urls import path
from . import views

urlpatterns = [

    path('dashboard/', views.doctor_dashboard, name='dashboard'),
    #path('settings/', views.profile_setup, name='settings'),
    #path('profile/', views.profile_setup, name='profile_view'),
    #path('patients/list/', views.patients_list, name='patients_list'),
]