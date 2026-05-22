from django.urls import path
from .views import *

urlpatterns=[
    path('',register,name='register'),
    path('login/',user_login,name='login'),
    path('home/',home,name='home'),
    path('logout/',user_logout, name='logout'),
    path('profile/',profile, name='profile'),
    path('reset-password/', reset_password, name='reset_password'),

    path('create-event/', create_event, name='create_event'),
    path('events/', view_events, name='view_events'),
    path('delete-event/<int:event_id>/', delete_event, name='delete_event'),
    path('submit/<int:event_id>/', submit_project, name='submit_project'),
    path('evaluate/<int:submission_id>/',evaluate_project, name='evaluate_project'),
    path('leaderboard/<int:event_id>/', leaderboard, name='leaderboard'),
    path('notifications/', user_notifications, name='user_notifications'),   
    
    path('organizer/', organizer_dashboard, name='organizer_dashboard'),
    path('participant/', participant_dashboard, name='participant_dashboard'),
    path('judge/', judge_dashboard, name='judge_dashboard')
]





