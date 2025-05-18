from django.urls import path
from . import views

urlpatterns = [
    path('', views.social_hub, name='social_hub'),
    path('group/<str:group_id>', views.group_feed, name='group_feed'),
    path('challenges', views.leaderboard, name='challenges'),
    path('challenges/join/<str:challenge_id>', views.join_challenge, name='join_challenge'),
    path('challenges/leave/<str:challenge_id>', views.leave_challenge, name='leave_challenge')
]