from django.urls import path
from . import views

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('schedule/', views.schedule_view, name='schedule'),
    path('knowledge-cards/', views.knowledge_cards, name='knowledge_cards'),
    path('knowledge-cards/<int:card_id>/', views.knowledge_card_detail, name='card_detail'),
    path('knowledge-cards/<int:card_id>/update/', views.update_progress, name='update_progress'),
    path('ai-chat/', views.ai_chat, name='ai_chat'),
    # Страница "О нас"
    path('about/', views.about, name='about'),
    path('profile/', views.profile, name='profile'),
    path('leaderboard/', views.leaderboard, name='leaderboard'),
    path('task-tracker/', views.task_tracker, name='task_tracker'),
    path('games/', views.games_index, name='games'),
    path('games/math/', views.games_math, name='games_math'),
    path('games/programming/', views.games_programming, name='games_programming'),
    path('games/physics/', views.games_physics, name='games_physics'),
    path('games/database/', views.games_database, name='games_database'),
    path('games/english/', views.games_english, name='games_english'),
    path('games/chess/', views.chess_home, name='chess_home'),
    path('games/chess/new/', views.chess_new_game, name='chess_new_game'),
    path('games/chess/game/<int:game_id>/', views.chess_game, name='chess_game'),
    path('games/chess/make-move/<int:game_id>/', views.chess_make_move, name='chess_make_move'),
    path('games/chess/stats/', views.chess_stats, name='chess_stats'),
    
    # URL для заметок
    path('notes/create/', views.create_quick_note, name='create_quick_note'),
    path('notes/<int:note_id>/toggle/', views.toggle_note_complete, name='toggle_note_complete'),
    path('notes/<int:note_id>/delete/', views.delete_note, name='delete_note'),
]
