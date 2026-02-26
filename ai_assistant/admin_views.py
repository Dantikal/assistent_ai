from django.shortcuts import render, redirect
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib import messages
from django.contrib.auth.models import User
from django.http import JsonResponse
from django.db.models import Q, Sum
from .models import UserProfile, PointsAdjustment
from .forms import PointsAdjustmentForm
from django.utils import timezone


@staff_member_required
def points_management(request):
    """Страница управления очками пользователей"""
    
    # Статистика
    total_users = UserProfile.objects.count()
    total_points = UserProfile.objects.aggregate(total=Sum('points'))['total'] or 0
    avg_points = total_points / total_users if total_users > 0 else 0
    
    # Изменения сегодня
    today = timezone.now().date()
    today_changes = PointsAdjustment.objects.filter(created_at__date=today).count()
    
    # Топ пользователи
    top_users = UserProfile.objects.select_related('user').order_by('-points')[:10]
    
    # Последние изменения
    recent_adjustments = PointsAdjustment.objects.select_related('user', 'created_by').order_by('-created_at')[:20]
    
    # Форма изменения очков
    form = PointsAdjustmentForm()
    
    context = {
        'total_users': total_users,
        'total_points': total_points,
        'avg_points': avg_points,
        'today_changes': today_changes,
        'top_users': top_users,
        'recent_adjustments': recent_adjustments,
        'form': form,
        'points_stats': {
            'total_users': total_users,
            'total_points': total_points,
            'avg_points': avg_points,
            'today_changes': today_changes,
        }
    }
    
    return render(request, 'admin/points_management.html', context)


@staff_member_required
def adjust_user_points(request):
    """AJAX обработчик изменения очков пользователя"""
    if request.method == 'POST':
        form = PointsAdjustmentForm(request.POST)
        
        if form.is_valid():
            adjustment = form.save(commit=False)
            adjustment.created_by = request.user
            
            # Обновляем очки пользователя
            user_profile, created = UserProfile.objects.get_or_create(
                user=adjustment.user,
                defaults={'points': 0}
            )
            user_profile.points = max(0, user_profile.points + adjustment.points_change)
            user_profile.save()
            
            # Сохраняем запись об изменении
            adjustment.save()
            
            return JsonResponse({
                'success': True,
                'new_points': user_profile.points,
                'message': f'Очки пользователя {adjustment.user.username} успешно изменены на {adjustment.points_change:+d}'
            })
        else:
            return JsonResponse({
                'success': False,
                'errors': form.errors
            })
    
    return JsonResponse({'success': False, 'error': 'Invalid request method'})


@staff_member_required
def get_user_points(request, user_id):
    """Получить текущие очки пользователя (AJAX)"""
    try:
        user = User.objects.get(id=user_id)
        user_profile, created = UserProfile.objects.get_or_create(
            user=user,
            defaults={'points': 0}
        )
        
        return JsonResponse({
            'success': True,
            'points': user_profile.points,
            'username': user.username
        })
    except User.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'User not found'})


@staff_member_required
def bulk_adjust_points(request):
    """Массовое изменение очков"""
    if request.method == 'POST':
        action = request.POST.get('action')
        value = float(request.POST.get('value', 0))
        reason = request.POST.get('reason', '')
        filter_type = request.POST.get('filter_users', 'active')
        filter_value = request.POST.get('filter_value', '')
        
        if not reason:
            return JsonResponse({'success': False, 'error': 'Укажите причину изменения'})
        
        # Определяем queryset пользователей
        if filter_type == 'all':
            users = User.objects.all()
        elif filter_type == 'active':
            users = User.objects.filter(userprofile__isnull=False)
        elif filter_type == 'points_above':
            users = User.objects.filter(userprofile__points__gt=int(filter_value))
        elif filter_type == 'points_below':
            users = User.objects.filter(userprofile__points__lt=int(filter_value))
        else:
            users = User.objects.filter(userprofile__isnull=False)
        
        count = 0
        errors = []
        
        for user in users:
            try:
                user_profile, created = UserProfile.objects.get_or_create(
                    user=user,
                    defaults={'points': 0}
                )
                
                old_points = user_profile.points
                
                if action == 'add':
                    change = int(value)
                    user_profile.points += change
                elif action == 'subtract':
                    change = -int(value)
                    user_profile.points = max(0, user_profile.points - int(value))
                elif action == 'set':
                    change = int(value) - old_points
                    user_profile.points = int(value)
                elif action == 'multiply':
                    change = int(old_points * (value - 1))
                    user_profile.points = int(old_points * value)
                else:
                    continue
                
                user_profile.save()
                
                # Создаем запись об изменении
                PointsAdjustment.objects.create(
                    user=user,
                    points_change=change,
                    reason=f"{reason} (массовое изменение)",
                    created_by=request.user
                )
                
                count += 1
                
            except Exception as e:
                errors.append(f"Ошибка с пользователем {user.username}: {str(e)}")
        
        return JsonResponse({
            'success': True,
            'count': count,
            'errors': errors,
            'message': f'Очки успешно изменены для {count} пользователей'
        })
    
    return JsonResponse({'success': False, 'error': 'Invalid request method'})


@staff_member_required
def points_history(request, user_id=None):
    """История изменений очков"""
    if user_id:
        adjustments = PointsAdjustment.objects.filter(user_id=user_id)
        user = User.objects.get(id=user_id)
        title = f'История изменений очков: {user.username}'
    else:
        adjustments = PointsAdjustment.objects.all()
        title = 'История всех изменений очков'
    
    adjustments = adjustments.select_related('user', 'created_by').order_by('-created_at')
    
    context = {
        'adjustments': adjustments,
        'title': title,
        'user_id': user_id,
    }
    
    return render(request, 'admin/points_history.html', context)
