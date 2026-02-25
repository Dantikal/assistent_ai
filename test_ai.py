"""
Пример использования AI-ассистента с OpenAI
"""
from ai_assistant.ai_service import ai_assistant

def test_ai_assistant():
    """Тестирование AI-ассистента"""
    
    # Проверяем, включен ли AI
    if not ai_assistant.enabled:
        print("❌ AI-ассистент не настроен. Добавьте OPENAI_API_KEY в settings.py")
        return
    
    # Тестовый вопрос
    question = "Что такое производная в математике?"
    
    # Ищем релевантные карточки
    relevant_cards = ai_assistant.find_relevant_cards(question)
    print(f"🔍 Найдено релевантных карточек: {len(relevant_cards)}")
    
    # Генерируем ответ
    response = ai_assistant.generate_response(question, relevant_cards)
    print(f"🤖 Ответ AI: {response}")

if __name__ == "__main__":
    test_ai_assistant()
