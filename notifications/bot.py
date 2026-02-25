import telegram
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters
from django.conf import settings
from django.contrib.auth.models import User
from schedule.models import Student


def start(update, context):
    """Обработчик команды /start"""
    user = update.effective_user
    chat_id = update.effective_chat.id
    
    # Приветственное сообщение
    welcome_text = f"👋 Привет, {user.first_name}!\n\n" \
                  f"Я ваш персональный ассистент для учебы.\n\n" \
                  f"📚 Что я могу делать:\n" \
                  f"• Присылать уведомления о парах\n" \
                  f"• Помогать с учебными вопросами через AI-ассистента\n" \
                  f"• Показывать расписание\n\n" \
                  f"🔐 Для привязки аккаунта введите:\n" \
                  f"/connect ваш_логин"
    
    context.bot.send_message(chat_id=chat_id, text=welcome_text)


def connect(update, context):
    """Привязка Telegram аккаунта к студенческому"""
    chat_id = update.effective_chat.id
    
    if len(context.args) != 1:
        context.bot.send_message(
            chat_id=chat_id,
            text="❌ Неверный формат. Используйте: /connect ваш_логин"
        )
        return
    
    username = context.args[0]
    
    try:
        user = User.objects.get(username=username)
        student = Student.objects.get(user=user)
        
        # Привязываем chat_id
        student.telegram_chat_id = str(chat_id)
        student.save()
        
        context.bot.send_message(
            chat_id=chat_id,
            text=f"✅ Аккаунт успешно привязан!\n\n"
                 f"👤 Студент: {user.get_full_name()}\n"
                 f"👥 Группа: {student.group}\n\n"
                 f"Теперь вы будете получать уведомления о парах!"
        )
    except User.DoesNotExist:
        context.bot.send_message(
            chat_id=chat_id,
            text="❌ Пользователь с таким логином не найден"
        )
    except Student.DoesNotExist:
        context.bot.send_message(
            chat_id=chat_id,
            text="❌ Студент не найден в системе"
        )


def help_command(update, context):
    """Показать справку"""
    help_text = "📖 Справка по командам:\n\n" \
               "/start - Начать работу с ботом\n" \
               "/connect логин - Привязать аккаунт студента\n" \
               "/schedule - Показать расписание на сегодня\n" \
               "/help - Показать эту справку\n\n" \
               "❓ Задайте любой вопрос по учебе, и AI-ассистент поможет!"
    
    context.bot.send_message(chat_id=update.effective_chat.id, text=help_text)


def schedule_today(update, context):
    """Показать расписание на сегодня"""
    chat_id = update.effective_chat.id
    
    try:
        student = Student.objects.get(telegram_chat_id=str(chat_id))
        from datetime import date
        today = date.today()
        day_of_week = today.weekday() + 1  # Конвертация в формат модели
        
        schedules = ClassSchedule.objects.filter(
            group=student.group,
            day_of_week=day_of_week,
            is_active=True
        ).order_by('start_time')
        
        if not schedules:
            context.bot.send_message(
                chat_id=chat_id,
                text="📅 На сегодня пар нет. Отдыхайте! 😊"
            )
            return
        
        schedule_text = f"📅 Расписание на сегодня ({today.strftime('%d.%m.%Y')}):\n\n"
        
        for schedule in schedules:
            schedule_text += f"🕐 {schedule.start_time} - {schedule.end_time}\n" \
                           f"📚 {schedule.subject.name}\n" \
                           f"👨‍🏫 {schedule.subject.teacher.get_full_name()}\n" \
                           f"📍 {schedule.room}\n\n"
        
        context.bot.send_message(chat_id=chat_id, text=schedule_text)
        
    except Student.DoesNotExist:
        context.bot.send_message(
            chat_id=chat_id,
            text="❌ Сначала привяжите аккаунт командой /connect логин"
        )


def handle_message(update, context):
    """Обработчик текстовых сообщений для AI-ассистента"""
    chat_id = update.effective_chat.id
    user_message = update.message.text
    
    # Здесь можно добавить интеграцию с AI-ассистентом
    context.bot.send_message(
        chat_id=chat_id,
        text="🤖 AI-ассистент находится в разработке. Скоро я смогу отвечать на ваши вопросы!"
    )


def setup_bot():
    """Настройка и запуск бота"""
    if not settings.TELEGRAM_BOT_TOKEN or settings.TELEGRAM_BOT_TOKEN == 'YOUR_BOT_TOKEN_HERE':
        print("⚠️ TELEGRAM_BOT_TOKEN не настроен. Бот не будет запущен.")
        return None
    
    updater = Updater(token=settings.TELEGRAM_BOT_TOKEN, use_context=True)
    dispatcher = updater.dispatcher
    
    # Добавление обработчиков команд
    dispatcher.add_handler(CommandHandler('start', start))
    dispatcher.add_handler(CommandHandler('connect', connect))
    dispatcher.add_handler(CommandHandler('help', help_command))
    dispatcher.add_handler(CommandHandler('schedule', schedule_today))
    
    # Обработчик текстовых сообщений
    dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_message))
    
    return updater


if __name__ == '__main__':
    updater = setup_bot()
    if updater:
        updater.start_polling()
        updater.idle()
