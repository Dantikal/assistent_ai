from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.auth import views as auth_views

from ai_assistant import views as ai_views
from ai_assistant.auth_views import CustomLogoutView, logout_view


urlpatterns = [
    path('admin/', admin.site.urls),
    path('admin-panel/', include('ai_assistant.admin_urls')),
    path('accounts/login/', auth_views.LoginView.as_view(template_name='registration/login.html'), name='login'),
    path('accounts/logout/', CustomLogoutView.as_view(), name='logout'),
    path('logout/', logout_view, name='logout_simple'),
    path('register/', ai_views.register, name='register'),
    path('', include('ai_assistant.urls')),
    path('schedule/', include('schedule.urls')),
    path('notifications/', include('notifications.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)