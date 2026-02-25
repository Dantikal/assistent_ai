from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.utils import timezone
from .models import KnowledgeCard, AIConversation, StudyProgress
from .auth_views import register
from schedule.models import ClassSchedule, Subject, Student, StudentGroup
from datetime import date, timedelta
import random
import ast
import operator
import re


@login_required
def dashboard(request):
    """Главная панель студента"""
    try:
        student = request.user.student
    except Student.DoesNotExist:
        # Создаем студента с группой по умолчанию
        default_group, _ = StudentGroup.objects.get_or_create(
            name="Не указана",
            defaults={
                'description': 'Студенты без указанной группы',
                'faculty': 'Не указан',
                'course': 1,
                'is_active': True
            }
        )
        student = Student.objects.create(user=request.user, group=default_group)
    
    # Расписание на сегодня
    today = date.today()
    day_of_week = today.weekday() + 1  # Конвертация в формат модели (1-7)
    today_schedules = ClassSchedule.objects.filter(
        group=student.group,
        day_of_week=day_of_week,
        is_active=True
    ).order_by('start_time')
    
    # Ближайшая пара
    next_class = None
    now = timezone.now().time()
    for schedule in today_schedules:
        if schedule.start_time > now:
            next_class = schedule
            break
    
    # Прогресс изучения
    recent_progress = StudyProgress.objects.filter(
        user=request.user
    ).order_by('-last_accessed')[:5]
    
    context = {
        'student': student,
        'today_schedules': today_schedules,
        'next_class': next_class,
        'recent_progress': recent_progress,
    }
    
    return render(request, 'ai_assistant/dashboard.html', context)


@login_required
def schedule_view(request):
    """Просмотр расписания"""
    try:
        student = request.user.student
    except Student.DoesNotExist:
        # Создаем студента с группой по умолчанию
        from schedule.models import StudentGroup
        default_group, _ = StudentGroup.objects.get_or_create(
            name="Не указана",
            defaults={
                'description': 'Студенты без указанной группы',
                'faculty': 'Не указан',
                'course': 1,
                'is_active': True
            }
        )
        student = Student.objects.create(user=request.user, group=default_group)

    from schedule.forms import PersonalScheduleItemForm, ScheduleNoteForm
    from schedule.models import PersonalScheduleItem, ScheduleNote

    if request.method == 'POST':
        action = request.POST.get('action')

        if action == 'delete_personal':
            item_id = request.POST.get('item_id')
            PersonalScheduleItem.objects.filter(id=item_id, user=request.user).delete()
            return redirect('schedule')

        if action == 'delete_note':
            note_id = request.POST.get('note_id')
            ScheduleNote.objects.filter(id=note_id, user=request.user).delete()
            return redirect('schedule')

        if action == 'add_note':
            note_form = ScheduleNoteForm(request.POST)
            schedule_type = request.POST.get('schedule_type')
            schedule_id = request.POST.get('schedule_id')

            if note_form.is_valid() and schedule_type in ['group', 'personal'] and schedule_id:
                note = note_form.save(commit=False)
                note.user = request.user

                if schedule_type == 'group':
                    schedule = ClassSchedule.objects.filter(
                        id=schedule_id,
                        group=student.group,
                        is_active=True,
                    ).first()
                    if schedule:
                        note.class_schedule = schedule
                        note.save()
                        return redirect('schedule')

                if schedule_type == 'personal':
                    item = PersonalScheduleItem.objects.filter(
                        id=schedule_id,
                        user=request.user,
                        is_active=True,
                    ).first()
                    if item:
                        note.personal_item = item
                        note.save()
                        return redirect('schedule')

        form = PersonalScheduleItemForm(request.POST)
        if form.is_valid():
            item = form.save(commit=False)
            item.user = request.user
            item.save()
            return redirect('schedule')
    else:
        form = PersonalScheduleItemForm()

    note_form = ScheduleNoteForm()
    
    # Получаем расписание на неделю
    week_data = []

    group_ids = list(ClassSchedule.objects.filter(group=student.group, is_active=True).values_list('id', flat=True))
    personal_ids = list(PersonalScheduleItem.objects.filter(user=request.user, is_active=True).values_list('id', flat=True))

    notes_by_group = {}
    if group_ids:
        for n in ScheduleNote.objects.filter(user=request.user, class_schedule_id__in=group_ids).order_by('-created_at'):
            notes_by_group.setdefault(n.class_schedule_id, []).append(n)

    notes_by_personal = {}
    if personal_ids:
        for n in ScheduleNote.objects.filter(user=request.user, personal_item_id__in=personal_ids).order_by('-created_at'):
            notes_by_personal.setdefault(n.personal_item_id, []).append(n)

    for day in range(1, 8):
        group_schedules = ClassSchedule.objects.filter(
            group=student.group,
            day_of_week=day,
            is_active=True
        ).order_by('start_time')

        personal_schedules = PersonalScheduleItem.objects.filter(
            user=request.user,
            day_of_week=day,
            is_active=True,
        ).order_by('start_time')

        group_rows = []
        for s in group_schedules:
            group_rows.append({'obj': s, 'notes': notes_by_group.get(s.id, [])})

        personal_rows = []
        for it in personal_schedules:
            personal_rows.append({'obj': it, 'notes': notes_by_personal.get(it.id, [])})

        week_data.append({
            'day': day,
            'group_schedules': group_rows,
            'personal_schedules': personal_rows,
        })
    
    context = {
        'student': student,
        'week_data': week_data,
        'personal_form': form,
        'note_form': note_form,
    }
    
    return render(request, 'ai_assistant/schedule.html', context)


@login_required
def knowledge_cards(request):
    """Список карточек знаний"""
    subject_id = request.GET.get('subject')
    difficulty = request.GET.get('difficulty')
    
    cards = KnowledgeCard.objects.filter(is_active=True)
    
    if subject_id:
        cards = cards.filter(subject_id=subject_id)
    if difficulty:
        cards = cards.filter(difficulty_level=difficulty)
    
    # Получаем прогресс для каждой карточки
    for card in cards:
        try:
            progress = StudyProgress.objects.get(user=request.user, knowledge_card=card)
            card.user_progress = progress.mastery_level
        except StudyProgress.DoesNotExist:
            card.user_progress = 1
    
    context = {
        'cards': cards,
        'subjects': Subject.objects.all(),
    }
    
    return render(request, 'ai_assistant/knowledge_cards.html', context)


@login_required
def knowledge_card_detail(request, card_id):
    """Детальная просмотр карточки знаний"""
    card = get_object_or_404(KnowledgeCard, id=card_id, is_active=True)
    
    # Обновляем прогресс
    progress, created = StudyProgress.objects.get_or_create(
        user=request.user,
        knowledge_card=card,
        defaults={'mastery_level': 2, 'access_count': 1}
    )
    
    if not created:
        progress.access_count += 1
        progress.last_accessed = timezone.now()
        progress.save()
    
    context = {
        'card': card,
        'progress': progress,
    }
    
    return render(request, 'ai_assistant/card_detail.html', context)


@login_required
def ai_chat(request):
    """Чат с AI-ассистентом"""
    if request.method == 'POST':
        question = request.POST.get('question')
        
        try:
            # Используем реальный AI-ассистент
            from .ai_service import ai_assistant
            
            # Для скорости временно отключаем поиск карточек
            relevant_cards = []  # ai_assistant.find_relevant_cards(question)
            
            # Генерируем ответ AI
            ai_response = ai_assistant.generate_response(question, relevant_cards)
            
            # Сохраняем диалог
            conversation = AIConversation.objects.create(
                user=request.user,
                student_question=question,
                ai_response=ai_response
            )
            
            # Добавляем релевантные карточки
            if relevant_cards:
                conversation.related_cards.add(*relevant_cards)
            
            return JsonResponse({
                'success': True,
                'response': ai_response,
                'conversation_id': conversation.id
            })
            
        except Exception as e:
            print(f"AI Chat Error: {e}")
            return JsonResponse({
                'success': False,
                'error': 'Произошла ошибка при обработке запроса. Попробуйте еще раз.',
                'response': '🤖 Извините, произошла техническая ошибка. Попробуйте задать вопрос еще раз.'
            }, status=500)
    
    # GET запрос - отображение страницы чата
    # Загрузка истории диалогов
    conversations = AIConversation.objects.filter(user=request.user).order_by('-created_at')[:10]
    conversation_history = []
    
    for conv in conversations:
        conversation_history.append({
            'id': conv.id,
            'question': conv.student_question,
            'response': conv.ai_response,
            'created_at': conv.created_at.strftime('%H:%M')
        })
    
    context = {
        'conversation_history': conversation_history
    }
    
    return render(request, 'ai_assistant/ai_chat.html', context)


@login_required
def profile(request):
    from .forms import UserProfileForm
    from .models import UserProfile

    profile, _ = UserProfile.objects.get_or_create(user=request.user)
    
    # Вычисляем точность ответов
    accuracy = profile.get_accuracy_percentage()

    if request.method == 'POST':
        form = UserProfileForm(request.POST, request.FILES, instance=profile)
        if form.is_valid():
            form.save()
            return render(request, 'ai_assistant/profile.html', {
                'form': form, 
                'profile': profile, 
                'accuracy': accuracy,
                'saved': True
            })
    else:
        form = UserProfileForm(instance=profile)

    return render(request, 'ai_assistant/profile.html', {
        'form': form, 
        'profile': profile,
        'accuracy': accuracy
    })


@login_required
def games_index(request):
    from .models import UserProfile

    profile, _ = UserProfile.objects.get_or_create(user=request.user)
    return render(request, 'ai_assistant/games_index.html', {'points': profile.points})


@login_required
def games_math(request):
    from .models import UserProfile

    profile, _ = UserProfile.objects.get_or_create(user=request.user)

    def _safe_eval_arithmetic(expr):
        expr = (expr or '').strip()
        if not expr:
            raise ValueError('empty')
        if not re.fullmatch(r"[0-9\s\+\-\*\/\(\)\.]+", expr):
            raise ValueError('bad_chars')

        node = ast.parse(expr, mode='eval')
        ops = {
            ast.Add: operator.add,
            ast.Sub: operator.sub,
            ast.Mult: operator.mul,
            ast.Div: operator.truediv,
        }

        def _eval(n):
            if isinstance(n, ast.Expression):
                return _eval(n.body)
            if isinstance(n, ast.Constant) and isinstance(n.value, (int, float)):
                return n.value
            if isinstance(n, ast.Num):
                return n.n
            if isinstance(n, ast.UnaryOp) and isinstance(n.op, (ast.UAdd, ast.USub)):
                val = _eval(n.operand)
                return val if isinstance(n.op, ast.UAdd) else -val
            if isinstance(n, ast.BinOp) and type(n.op) in ops:
                left = _eval(n.left)
                right = _eval(n.right)
                return ops[type(n.op)](left, right)
            raise ValueError('unsupported')

        return _eval(node)

    def _generate_example(level):
        if level == 'easy':
            a = random.randint(1, 20)
            b = random.randint(1, 20)
            expr = f"{a} + {b}"
        elif level == 'normal':
            a = random.randint(2, 30)
            b = random.randint(2, 20)
            c = random.randint(1, 20)
            choice = random.choice(['mix1', 'mix2', 'div'])

            if choice == 'mix1':
                expr = f"({a} + {b}) * {c}"
            elif choice == 'mix2':
                expr = f"{a} * {b} - {c}"
            else:
                denom = random.randint(2, 12)
                quotient = random.randint(2, 25)
                numerator = denom * quotient
                add = random.randint(0, 20)
                expr = f"{numerator} / {denom} + {add}"
        else:
            a = random.randint(10, 60)
            b = random.randint(2, 40)
            c = random.randint(2, 25)
            d = random.randint(1, 30)
            e = random.randint(2, 15)
            choice = random.choice(['nested', 'div_nested', 'neg', 'mix3'])

            if choice == 'nested':
                expr = f"(({a} - {b}) * {c} + {d})"
            elif choice == 'div_nested':
                denom = random.randint(2, 15)
                quotient = random.randint(5, 40)
                numerator = denom * quotient
                expr = f"({numerator} / {denom}) + ({a} - {b}) * {e}"
            elif choice == 'neg':
                x = random.randint(5, 30)
                y = random.randint(5, 30)
                expr = f"-({x} * {y}) + ({a} - {b})"
            else:
                denom = random.randint(2, 12)
                quotient = random.randint(5, 30)
                numerator = denom * quotient
                expr = f"(({a} + {b}) * {c} - {d}) / {denom} + {numerator} / {denom}"

        answer = _safe_eval_arithmetic(expr)
        if isinstance(answer, float) and answer.is_integer():
            answer = int(answer)
        return expr, answer

    level = request.GET.get('level') or request.POST.get('level') or 'easy'
    if level not in ['easy', 'normal', 'hard']:
        level = 'easy'

    session_key_seen = f"games_seen_{level}"
    seen = request.session.get(session_key_seen, [])
    if not isinstance(seen, list):
        seen = []

    message = None
    result = None
    current_expr = request.session.get('games_current_expr')
    current_answer = request.session.get('games_current_answer')
    current_level = request.session.get('games_current_level')

    if current_level and current_level != level:
        current_expr = None
        current_answer = None
        current_level = None

    if request.method == 'POST':
        action = request.POST.get('action')

        if action == 'new' or not current_expr or current_level != level:
            current_expr = None
            current_answer = None
            current_level = None
        else:
            user_answer_raw = (request.POST.get('answer') or '').strip().replace(',', '.')
            try:
                user_answer = float(user_answer_raw) if '.' in user_answer_raw else int(user_answer_raw)
                correct = float(current_answer) == float(user_answer)
            except Exception:
                correct = False

            if correct:
                points_awarded = 100 if level == 'hard' else 50
                profile.points += points_awarded
                profile.correct_answers += 1
                profile.save(update_fields=['points', 'correct_answers'])
                seen.append(current_expr)
                request.session[session_key_seen] = seen
                message = f"Правильно! +{points_awarded} очков"
                result = True
                current_expr = None
                current_answer = None
                current_level = None
            else:
                profile.wrong_answers += 1
                penalty = 50
                if level == 'normal':
                    penalty = 70
                elif level == 'hard':
                    penalty = 100

                profile.points = max(0, profile.points - penalty)
                profile.save(update_fields=['points', 'wrong_answers'])
                message = f"Неправильно. -{penalty} очков. Попробуйте ещё раз"
                result = False

    if not current_expr:
        for _ in range(100):
            expr, ans = _generate_example(level)
            if expr not in seen:
                current_expr = expr
                current_answer = ans
                current_level = level
                break
        else:
            seen = []
            request.session[session_key_seen] = seen
            current_expr, current_answer = _generate_example(level)
            current_level = level

        request.session['games_current_expr'] = current_expr
        request.session['games_current_answer'] = current_answer
        request.session['games_current_level'] = current_level

    context = {
        'level': level,
        'expr': current_expr,
        'message': message,
        'result': result,
        'points': profile.points,
        'seen_count': len(seen),
    }
    return render(request, 'ai_assistant/games.html', context)


@login_required
def games_programming(request):
    from .models import UserProfile

    profile, _ = UserProfile.objects.get_or_create(user=request.user)

    def _penalty_for_level(level):
        if level == 'normal':
            return 70
        if level == 'hard':
            return 100
        return 50

    tasks = {
        'easy': [
            {
                'id': 'e_print_1',
                'prompt': 'Что выведет код?\n\nprint(2 + 3)',
                'answer': '5',
            },
            {
                'id': 'e_type_1',
                'prompt': 'Какой тип у значения: 3.14 ? (ответ: int/float/str/bool)',
                'answer': 'float',
            },
            {
                'id': 'e_bool_1',
                'prompt': 'Что выведет код?\n\nprint(10 > 3)',
                'answer': 'True',
            },
            {
                'id': 'e_len_1',
                'prompt': "Чему равно len('abc') ?",
                'answer': '3',
            },
        ],
        'normal': [
            {
                'id': 'n_slice_1',
                'prompt': "Что выведет код?\n\ns = 'python'\nprint(s[1:4])",
                'answer': 'yth',
            },
            {
                'id': 'n_list_1',
                'prompt': 'Что выведет код?\n\narr = [1, 2, 3]\narr.append(4)\nprint(len(arr))',
                'answer': '4',
            },
            {
                'id': 'n_for_1',
                'prompt': 'Что выведет код?\n\ns = 0\nfor i in range(1, 5):\n    s += i\nprint(s)',
                'answer': '10',
            },
            {
                'id': 'n_dict_1',
                'prompt': "Что выведет код?\n\nd = {'a': 1, 'b': 2}\nprint(d.get('c', 0))",
                'answer': '0',
            },
        ],
        'hard': [
            {
                'id': 'h_comp_1',
                'prompt': 'Что выведет код?\n\nnums = [1, 2, 3, 4]\nres = [x*x for x in nums if x % 2 == 0]\nprint(res)',
                'answer': '[4, 16]',
            },
            {
                'id': 'h_lambda_1',
                'prompt': 'Что выведет код?\n\nitems = [3, 1, 2]\nitems.sort(key=lambda x: -x)\nprint(items)',
                'answer': '[3, 2, 1]',
            },
            {
                'id': 'h_try_1',
                'prompt': 'Что выведет код?\n\ntry:\n    print(1/0)\nexcept ZeroDivisionError:\n    print("zero")',
                'answer': 'zero',
            },
            {
                'id': 'h_func_1',
                'prompt': 'Что выведет код?\n\ndef f(x, acc=[]):\n    acc.append(x)\n    return acc\n\nprint(f(1))\nprint(f(2))',
                'answer': '[1]\n[1, 2]',
            },
        ],
    }

    level = request.GET.get('level') or request.POST.get('level') or 'easy'
    if level not in ['easy', 'normal', 'hard']:
        level = 'easy'

    session_key_seen = f"prog_seen_{level}"
    seen = request.session.get(session_key_seen, [])
    if not isinstance(seen, list):
        seen = []

    message = None
    result = None

    current_id = request.session.get('prog_current_id')
    current_level = request.session.get('prog_current_level')

    if current_level and current_level != level:
        current_id = None
        current_level = None

    if request.method == 'POST':
        action = request.POST.get('action')

        if action == 'new' or not current_id or current_level != level:
            current_id = None
            current_level = None
        else:
            user_answer = (request.POST.get('answer') or '').strip()
            task_map = {t['id']: t for t in tasks[level]}
            task = task_map.get(current_id)
            correct = False
            if task:
                expected = (task['answer'] or '').strip()
                correct = user_answer == expected

            if correct:
                points_awarded = 100 if level == 'hard' else 50
                profile.points += points_awarded
                profile.correct_answers += 1
                profile.save(update_fields=['points', 'correct_answers'])

                seen.append(current_id)
                request.session[session_key_seen] = seen

                message = f"Правильно! +{points_awarded} очков"
                result = True
                current_id = None
                current_level = None
            else:
                penalty = _penalty_for_level(level)
                profile.wrong_answers += 1
                profile.points = max(0, profile.points - penalty)
                profile.save(update_fields=['points', 'wrong_answers'])
                message = f"Неправильно. -{penalty} очков. Попробуйте ещё раз"
                result = False

    if not current_id:
        pool = tasks[level]
        remaining = [t for t in pool if t['id'] not in seen]
        if not remaining:
            seen = []
            request.session[session_key_seen] = seen
            remaining = pool

        chosen = random.choice(remaining)
        current_id = chosen['id']
        current_level = level
        request.session['prog_current_id'] = current_id
        request.session['prog_current_level'] = current_level

    task_map = {t['id']: t for t in tasks[level]}
    current_task = task_map.get(current_id)
    prompt = current_task['prompt'] if current_task else ''

    context = {
        'level': level,
        'prompt': prompt,
        'message': message,
        'result': result,
        'points': profile.points,
        'seen_count': len(seen),
    }
    return render(request, 'ai_assistant/games_programming.html', context)


@login_required
def games_physics(request):
    from .models import UserProfile

    profile, _ = UserProfile.objects.get_or_create(user=request.user)

    def _penalty_for_level(level):
        if level == 'normal':
            return 70
        if level == 'hard':
            return 100
        return 50

    def _points_for_level(level):
        return 100 if level == 'hard' else 50

    tasks = {
        'easy': [
            {
                'id': 'e_speed_1',
                'prompt': 'Скорость: тело прошло 120 м за 10 с. Найди v (м/с).',
                'answer': '12',
            },
            {
                'id': 'e_density_1',
                'prompt': 'Плотность: m = 200 г, V = 100 см³. Найди ρ (г/см³).',
                'answer': '2',
            },
            {
                'id': 'e_pressure_1',
                'prompt': 'Давление: F = 50 Н, S = 10 м². Найди p (Па).',
                'answer': '5',
            },
            {
                'id': 'e_ohm_1',
                'prompt': 'Закон Ома: U = 12 В, R = 3 Ом. Найди I (А).',
                'answer': '4',
            },
        ],
        'normal': [
            {
                'id': 'n_work_1',
                'prompt': 'Работа: F = 20 Н, s = 15 м, сила направлена вдоль движения. Найди A (Дж).',
                'answer': '300',
            },
            {
                'id': 'n_power_1',
                'prompt': 'Мощность: A = 600 Дж за t = 20 с. Найди P (Вт).',
                'answer': '30',
            },
            {
                'id': 'n_kinetic_1',
                'prompt': 'Кинетическая энергия: m = 2 кг, v = 3 м/с. Найди Ek (Дж). (Ek = m*v^2/2)',
                'answer': '9',
            },
            {
                'id': 'n_hooke_1',
                'prompt': 'Закон Гука: k = 200 Н/м, x = 0.05 м. Найди F (Н).',
                'answer': '10',
            },
        ],
        'hard': [
            {
                'id': 'h_series_1',
                'prompt': 'Сопротивления последовательно: R1 = 4 Ом, R2 = 6 Ом. Найди Rобщ (Ом).',
                'answer': '10',
            },
            {
                'id': 'h_parallel_1',
                'prompt': 'Сопротивления параллельно: R1 = 6 Ом, R2 = 3 Ом. Найди Rэкв (Ом). (1/R = 1/R1 + 1/R2)',
                'answer': '2',
            },
            {
                'id': 'h_gravity_1',
                'prompt': 'Сила тяжести: m = 5 кг, g = 9.8 м/с². Найди F (Н).',
                'answer': '49',
            },
            {
                'id': 'h_energy_1',
                'prompt': 'Потенциальная энергия: m = 3 кг, h = 4 м, g = 9.8 м/с². Найди Ep (Дж).',
                'answer': '117.6',
            },
        ],
    }

    level = request.GET.get('level') or request.POST.get('level') or 'easy'
    if level not in ['easy', 'normal', 'hard']:
        level = 'easy'

    session_key_seen = f"phys_seen_{level}"
    seen = request.session.get(session_key_seen, [])
    if not isinstance(seen, list):
        seen = []

    message = None
    result = None

    current_id = request.session.get('phys_current_id')
    current_level = request.session.get('phys_current_level')

    if current_level and current_level != level:
        current_id = None
        current_level = None

    if request.method == 'POST':
        action = request.POST.get('action')

        if action == 'new' or not current_id or current_level != level:
            current_id = None
            current_level = None
        else:
            user_answer = (request.POST.get('answer') or '').strip().replace(',', '.')
            task_map = {t['id']: t for t in tasks[level]}
            task = task_map.get(current_id)
            correct = False
            if task:
                expected = (task['answer'] or '').strip().replace(',', '.')
                if user_answer == expected:
                    correct = True
                else:
                    try:
                        correct = abs(float(user_answer) - float(expected)) < 1e-9
                    except Exception:
                        correct = False

            if correct:
                points_awarded = _points_for_level(level)
                profile.points += points_awarded
                profile.correct_answers += 1
                profile.save(update_fields=['points', 'correct_answers'])

                seen.append(current_id)
                request.session[session_key_seen] = seen

                message = f"Правильно! +{points_awarded} очков"
                result = True
                current_id = None
                current_level = None
            else:
                penalty = _penalty_for_level(level)
                profile.wrong_answers += 1
                profile.points = max(0, profile.points - penalty)
                profile.save(update_fields=['points', 'wrong_answers'])
                message = f"Неправильно. -{penalty} очков. Попробуйте ещё раз"
                result = False

    if not current_id:
        pool = tasks[level]
        remaining = [t for t in pool if t['id'] not in seen]
        if not remaining:
            seen = []
            request.session[session_key_seen] = seen
            remaining = pool

        chosen = random.choice(remaining)
        current_id = chosen['id']
        current_level = level
        request.session['phys_current_id'] = current_id
        request.session['phys_current_level'] = current_level

    task_map = {t['id']: t for t in tasks[level]}
    current_task = task_map.get(current_id)
    prompt = current_task['prompt'] if current_task else ''

    context = {
        'level': level,
        'prompt': prompt,
        'message': message,
        'result': result,
        'points': profile.points,
        'seen_count': len(seen),
    }
    return render(request, 'ai_assistant/games_physics.html', context)


@login_required
def games_english(request):
    from .models import UserProfile

    profile, _ = UserProfile.objects.get_or_create(user=request.user)

    def _penalty_for_level(level):
        if level == 'normal':
            return 70
        if level == 'hard':
            return 100
        return 50

    def _points_for_level(level):
        return 100 if level == 'hard' else 50

    tasks = {
        'easy': [
            {'id': 'e_word_1', 'prompt': 'Переведи на английский: книга', 'answers': ['book']},
            {'id': 'e_word_2', 'prompt': 'Переведи на английский: школа', 'answers': ['school']},
            {'id': 'e_word_3', 'prompt': 'Переведи на английский: друг', 'answers': ['friend']},
            {'id': 'e_word_4', 'prompt': 'Переведи на английский: яблоко', 'answers': ['apple']},
            {'id': 'e_word_5', 'prompt': 'Переведи на русский: cat', 'answers': ['кот', 'кошка']},
        ],
        'normal': [
            {'id': 'n_phrase_1', 'prompt': 'Переведи на английский: Я люблю музыку', 'answers': ['i love music']},
            {'id': 'n_phrase_2', 'prompt': 'Переведи на английский: У меня есть собака', 'answers': ['i have a dog', 'i have dog']},
            {'id': 'n_phrase_3', 'prompt': 'Переведи на русский: I am tired', 'answers': ['я устал', 'я устала']},
            {'id': 'n_phrase_4', 'prompt': 'Переведи на английский: Он играет в футбол', 'answers': ['he plays football', 'he plays soccer']},
            {'id': 'n_phrase_5', 'prompt': 'Переведи на русский: We are students', 'answers': ['мы студенты']},
        ],
        'hard': [
            {'id': 'h_sentence_1', 'prompt': 'Переведи на английский: Если завтра будет дождь, мы останемся дома', 'answers': ['if it rains tomorrow we will stay at home', 'if it rains tomorrow, we will stay at home']},
            {'id': 'h_sentence_2', 'prompt': 'Переведи на русский: She has been studying for two hours', 'answers': ['она учится уже два часа', 'она занимается уже два часа']},
            {'id': 'h_sentence_3', 'prompt': 'Переведи на английский: Я бы купил это, если бы у меня были деньги', 'answers': ['i would buy it if i had money', 'i would buy it if i had the money']},
            {'id': 'h_sentence_4', 'prompt': 'Переведи на русский: I have never seen anything like this', 'answers': ['я никогда не видел ничего подобного', 'я никогда не видела ничего подобного']},
        ],
    }

    level = request.GET.get('level') or request.POST.get('level') or 'easy'
    if level not in ['easy', 'normal', 'hard']:
        level = 'easy'

    session_key_seen = f"eng_seen_{level}"
    seen = request.session.get(session_key_seen, [])
    if not isinstance(seen, list):
        seen = []

    message = None
    result = None

    current_id = request.session.get('eng_current_id')
    current_level = request.session.get('eng_current_level')

    if current_level and current_level != level:
        current_id = None
        current_level = None

    def _normalize_answer(s):
        s = (s or '').strip().lower()
        s = re.sub(r"\s+", " ", s)
        s = s.replace('’', "'")
        return s

    if request.method == 'POST':
        action = request.POST.get('action')

        if action == 'new' or not current_id or current_level != level:
            current_id = None
            current_level = None
        else:
            user_answer = _normalize_answer(request.POST.get('answer'))
            task_map = {t['id']: t for t in tasks[level]}
            task = task_map.get(current_id)

            correct = False
            if task:
                expected_list = task.get('answers') or []
                expected_norm = [_normalize_answer(x) for x in expected_list]
                correct = user_answer in expected_norm

            if correct:
                points_awarded = _points_for_level(level)
                profile.points += points_awarded
                profile.correct_answers += 1
                profile.save(update_fields=['points', 'correct_answers'])

                seen.append(current_id)
                request.session[session_key_seen] = seen

                message = f"Правильно! +{points_awarded} очков"
                result = True
                current_id = None
                current_level = None
            else:
                penalty = _penalty_for_level(level)
                profile.wrong_answers += 1
                profile.points = max(0, profile.points - penalty)
                profile.save(update_fields=['points', 'wrong_answers'])
                message = f"Неправильно. -{penalty} очков. Попробуйте ещё раз"
                result = False

    if not current_id:
        pool = tasks[level]
        remaining = [t for t in pool if t['id'] not in seen]
        if not remaining:
            seen = []
            request.session[session_key_seen] = seen
            remaining = pool

        chosen = random.choice(remaining)
        current_id = chosen['id']
        current_level = level
        request.session['eng_current_id'] = current_id
        request.session['eng_current_level'] = current_level

    task_map = {t['id']: t for t in tasks[level]}
    current_task = task_map.get(current_id)
    prompt = current_task['prompt'] if current_task else ''

    context = {
        'level': level,
        'prompt': prompt,
        'message': message,
        'result': result,
        'points': profile.points,
        'seen_count': len(seen),
    }
    return render(request, 'ai_assistant/games_english.html', context)


def generate_ai_response(question):
    """Генерация ответа AI (заглушка)"""
    responses = [
        "Это интересный вопрос! Давайте разберем его по частям...",
        "Хорошо, я помогу вам понять эту тему.",
        "Понимаю, что это может быть сложным. Объясню проще:",
        "Отличный вопрос! Вот как это можно понять:",
    ]
    
    return random.choice(responses)


@login_required
def update_progress(request, card_id):
    """Обновление прогресса изучения карточки"""
    if request.method == 'POST':
        card = get_object_or_404(KnowledgeCard, id=card_id, is_active=True)
        mastery_level = int(request.POST.get('mastery_level', 1))
        
        progress, created = StudyProgress.objects.get_or_create(
            user=request.user,
            knowledge_card=card,
            defaults={'mastery_level': mastery_level, 'access_count': 1}
        )
        
        if not created:
            progress.mastery_level = mastery_level
            progress.access_count += 1
            progress.save()
        
        return redirect('card_detail', card_id=card.id)
    
    return redirect('knowledge_cards')


def find_relevant_cards(question):
    """Поиск релевантных карточек (упрощенная версия)"""
    # Пока возвращаем случайные карточки
    cards = list(KnowledgeCard.objects.filter(is_active=True))
    return random.sample(cards, min(3, len(cards))) if cards else []


@login_required
def leaderboard(request):
    """Список лидеров - обще рейтинги и по предметам"""
    from .models import UserProfile, SubjectScore
    from schedule.models import Subject
    
    # Параметры для фильтрации
    subject_filter = request.GET.get('subject', 'all')
    
    # Общий рейтинг (топ 50 студентов)
    if subject_filter == 'all':
        leaders = UserProfile.objects.all().order_by('-points')[:50]
        title = "Общий рейтинг"
    else:
        try:
            subject = Subject.objects.get(id=subject_filter)
            # Получаем студентов с очками по этому предмету
            leaders_data = SubjectScore.objects.filter(subject=subject).order_by('-points')[:50]
            leaders = [score.user_profile for score in leaders_data]
            title = f"Рейтинг по {subject.name}"
        except Subject.DoesNotExist:
            leaders = UserProfile.objects.all().order_by('-points')[:50]
            title = "Общий рейтинг"
    
    # Добавляем ранг и место для каждого студента
    leaders_with_rank = []
    for idx, leader in enumerate(leaders, 1):
        leaders_with_rank.append({
            'place': idx,
            'profile': leader,
            'rank': leader.get_rank(),
            'rank_name': leader.get_rank_name(),
            'points': SubjectScore.objects.get(
                user_profile=leader,
                subject_id=subject_filter
            ).points if subject_filter != 'all' and subject_filter != '' else leader.points,
            'accuracy': leader.get_accuracy_percentage()
        })
    
    # Получаем все предметы для фильтра
    subjects = Subject.objects.all().order_by('name')
    
    # Проверяем текущее место пользователя
    user_position = None
    user_points = None
    
    try:
        user_profile = request.user.profile
        if subject_filter == 'all':
            user_position = UserProfile.objects.filter(points__gt=user_profile.points).count() + 1
            user_points = user_profile.points
        else:
            try:
                subject_score = SubjectScore.objects.get(
                    user_profile=user_profile,
                    subject_id=subject_filter
                )
                user_position = SubjectScore.objects.filter(
                    subject_id=subject_filter,
                    points__gt=subject_score.points
                ).count() + 1
                user_points = subject_score.points
            except SubjectScore.DoesNotExist:
                user_position = None
    except:
        pass
    
    context = {
        'leaders': leaders_with_rank,
        'subjects': subjects,
        'current_subject': subject_filter,
        'title': title,
        'user_position': user_position,
        'user_points': user_points,
    }
    
    return render(request, 'ai_assistant/leaderboard.html', context)
