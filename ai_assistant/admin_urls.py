from django.urls import path
from . import admin_views

app_name = 'admin_panel'

urlpatterns = [
    path('points/', admin_views.points_management, name='points_management'),
    path('points/adjust/', admin_views.adjust_user_points, name='adjust_user_points'),
    path('points/bulk/', admin_views.bulk_adjust_points, name='bulk_adjust_points'),
    path('points/user/<int:user_id>/', admin_views.get_user_points, name='get_user_points'),
    path('points/history/', admin_views.points_history, name='points_history'),
    path('points/history/<int:user_id>/', admin_views.points_history, name='user_points_history'),
]
