from django.urls import path
from . import views

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('schedule/', views.schedule_view, name='schedule'),
    path('knowledge-cards/', views.knowledge_cards, name='knowledge_cards'),
    path('knowledge-cards/<int:card_id>/', views.knowledge_card_detail, name='card_detail'),
    path('knowledge-cards/<int:card_id>/update/', views.update_progress, name='update_progress'),
    path('ai-chat/', views.ai_chat, name='ai_chat'),
    path('profile/', views.profile, name='profile'),
    path('leaderboard/', views.leaderboard, name='leaderboard'),
    path('games/', views.games_index, name='games'),
    path('games/math/', views.games_math, name='games_math'),
    path('games/programming/', views.games_programming, name='games_programming'),
    path('games/physics/', views.games_physics, name='games_physics'),
    path('games/english/', views.games_english, name='games_english'),
]
