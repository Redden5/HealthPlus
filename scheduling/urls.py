from django.urls import path
from . import views

app_name = 'scheduling'

urlpatterns = [
    path('events/', views.calendar_events, name='calendar_events'),
    path('available-slots/', views.available_slots, name='available_slots'),
    path('book-appointment/', views.book_appointment, name='book_appointment'),
]
