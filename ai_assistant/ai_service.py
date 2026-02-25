import openai
from django.conf import settings
from .models import KnowledgeCard
import requests
import re
import ast
import operator
from urllib.parse import quote

try:
    import ollama
    OLLAMA_AVAILABLE = True
except ImportError:
    OLLAMA_AVAILABLE = False


class AIAssistant:
    """Класс для работы с AI-ассистентом"""
    
    def __init__(self):
        self.openai_enabled = (
            settings.OPENAI_API_KEY and 
            settings.OPENAI_API_KEY != 'YOUR_OPENAI_API_KEY_HERE'
        )
        self.deepseek_enabled = (
            hasattr(settings, 'DEEPSEEK_API_KEY') and 
            settings.DEEPSEEK_API_KEY and 
            settings.DEEPSEEK_API_KEY != 'YOUR_DEEPSEEK_API_KEY_HERE'
        )
        self.ollama_enabled = OLLAMA_AVAILABLE and hasattr(settings, 'OLLAMA_ENABLED') and settings.OLLAMA_ENABLED
        
        self.enabled = self.openai_enabled or self.deepseek_enabled or self.ollama_enabled
    
    def generate_response(self, question, context_cards=None):
        """Генерация ответа на вопрос студента"""
        if not self.enabled:
            return self._fallback_response()
        
        try:
            math_result = self._try_solve_arithmetic(question)
            if math_result is not None:
                return math_result

            # Формируем контекст из карточек знаний
            context = self._build_context(context_cards)
            
            # Используем Wikipedia для получения структурированных ответов
            print("Using Wikipedia API") # Отладка
            response = self._get_wikipedia_response(question)
            print("Wikipedia response:", response) # Отладка
            return response
                
        except Exception as e:
            print(f"AI Error: {e}")
            return self._simple_fallback(question)
        
        return self._simple_fallback(question)
    
    def _get_wikipedia_response(self, question):
        """Получение структурированного ответа из Wikipedia"""
        try:
            topic = self._extract_wikipedia_topic(question)

            # Ищем статью в Wikipedia
            encoded_title = quote(topic.replace(" ", "_"), safe="")
            search_url = f"https://ru.wikipedia.org/api/rest_v1/page/summary/{encoded_title}"
            response = requests.get(search_url, timeout=10, headers=self._wikipedia_headers())
            
            if response.status_code == 200:
                data = response.json()
                return self._format_wikipedia_response(data, topic)
            else:
                # Если не найдено, пробуем поиск
                return self._search_wikipedia(topic)
                
        except Exception as e:
            print(f"Wikipedia Error: {e}")
            return self._simple_fallback(question)
    
    def _search_wikipedia(self, question):
        """Поиск в Wikipedia"""
        try:
            params = {
                "action": "query",
                "list": "search",
                "srsearch": question,
                "utf8": 1,
                "format": "json",
                "srlimit": 1,
            }
            response = requests.get(
                "https://ru.wikipedia.org/w/api.php",
                params=params,
                timeout=8,
                headers=self._wikipedia_headers(),
            )
            if response.status_code != 200:
                return self._simple_fallback(question)

            data = response.json() or {}
            search_results = (((data.get("query") or {}).get("search")) or [])
            if not search_results:
                return self._simple_fallback(question)

            title = (search_results[0].get("title") or "").strip()
            if not title:
                return self._simple_fallback(question)

            encoded_title = quote(title.replace(" ", "_"), safe="")
            summary_url = f"https://ru.wikipedia.org/api/rest_v1/page/summary/{encoded_title}"
            summary_response = requests.get(summary_url, timeout=8, headers=self._wikipedia_headers())
            if summary_response.status_code != 200:
                return self._simple_fallback(question)

            return self._format_wikipedia_response(summary_response.json(), title)
            
        except Exception as e:
            print(f"Wikipedia Search Error: {e}")
            return self._simple_fallback(question)

    def _extract_wikipedia_topic(self, question):
        text = (question or "").strip()
        if not text:
            return ""

        lowered = text.lower().strip(" ?!.\t\n\r")
        prefixes = [
            "кто такой ",
            "кто такая ",
            "кто такие ",
            "что такое ",
            "что значит ",
            "расскажи про ",
            "расскажи о ",
            "расскажи об ",
            "объясни ",
            "объясни что такое ",
        ]
        for p in prefixes:
            if lowered.startswith(p):
                topic = text[len(p):].strip(" ?!.")
                return topic or text

        return text

    def _wikipedia_headers(self):
        return {
            "User-Agent": "StudySense/1.0 (AI assistant; educational project)",
        }
    
    def _format_wikipedia_response(self, data, question):
        """Форматирование ответа из Wikipedia в структурированный вид"""
        title = data.get('title', question)
        description = data.get('description', '')
        extract = data.get('extract', '')
        url = data.get('content_urls', {}).get('desktop', {}).get('page', '')
        
        # Формируем структурированный ответ
        response = f"""📚 Тема: {title}

📚 КОНСПЕКТ:
{extract}

🔑 КЛЮЧЕВЫЕ СЛОВА:
- {title}: {description}
- Основное понятие: ключевая сущность темы
- Определение: краткое описание сути
- Характеристики: основные свойства и признаки
- Применение: области использования

📝 КРАТКО:
{description}. {extract[:200]}...

💡 ПРИМЕРЫ:
1. Реальный пример использования в жизни
2. Исторический контекст появления
3. Современное применение в практике

🎯 ПРИМЕНЕНИЕ:
- Образование: изучение концепции и принципов
- Практика: применение в реальных ситуациях
- Исследования: дальнейшее развитие темы
- Промышленность: коммерческое использование

🧠 ЗАПОМНИТЬ:
Запомните ключевые характеристики и основные принципы работы. Используйте ассоциации с уже известными понятиями.

📖 ДОПОЛНИТЕЛЬНО:
Изучите дополнительные материалы по теме для углубления знаний.

🔗 СВЯЗАННЫЕ ТЕМЫ:
- Смежные концепции и области
- Исторические предшественники
- Современные разработки"""
        
        return response
    
    def _simple_fallback(self, question):
        """Быстрый fallback ответ"""
        question_lower = question.lower()

        math_result = self._try_solve_arithmetic(question)
        if math_result is not None:
            return math_result
        
        # Brawl Stars и игры
        if any(word in question_lower for word in ["бравл старс", "brawl stars", "игра", "игры"]):
            return """📚 Тема: Brawl Stars - это популярная мобильная многопользовательская игра

📚 КОНСПЕКТ:
Brawl Stars - это бесплатная мобильная игра в жанре MOBA (многопользовательская онлайновая боевая арена), разработанная компанией Supercell. Игра была выпущена в 2018 году и быстро стала популярной во всем мире. Игроки сражаются в командах в различных режимах на аренах, используя уникальных персонажей с разными способностями.

🔑 КЛЮЧЕВЫЕ СЛОВА:
- Brawl Stars: мобильная MOBA-игра от Supercell
- Бравлер: уникальный персонаж с особыми способностями
- Арена: игровое поле для сражений
- Кубки: система рейтинга и прогресса
- Гемма: игровая валюта для покупки бравлеров

📝 КРАТКО:
Brawl Stars - это командная мобильная игра, где игроки выбирают персонажей и сражаются на различных аренах в разных игровых режимах.

💡 ПРИМЕРЫ:
1. "Захват кристаллов" - команда собирает и защищает кристаллы
2. "Столкновение" - уничтожение вражеского командного центра
3. "Ограбление" - защита сейфа от врагов
4. "Боунти" - сбор звезд за победы над противниками

🎯 ПРИМЕНЕНИЕ:
- Развлечения: отдых и соревновательный азарт
- Социализация: игра с друзьями и общение
- Стратегическое мышление: планирование тактики
- Развитие реакций: улучшение скорости принятия решений

🧠 ЗАПОМНИТЬ:
Каждый бравлер имеет уникальные способности. Изучите сильные и слабые стороны персонажей для эффективной игры.

📖 ДОПОЛНИТЕЛЬНО:
- Изучите всех бравлеров и их способности
- Научитесь работать в команде
- Изучите тактику для разных режимов игры

🔗 СВЯЗАННЫЕ ТЕМЫ:
- Киберспорт и соревновательные игры
- Мобильный гейминг
- Стратегические игры
- Командное взаимодействие"""
        
        # Валюта
        elif any(word in question_lower for word in ["валюта", "деньги", "курс", "доллар", "евро"]):
            return """Валюта - это денежная единица страны, используемая для покупки товаров и услуг. Курс валют показывает, сколько одной валюты можно купить за другую. Например, 1 доллар США стоит около 90 рублей. Валютные курсы постоянно меняются из-за экономических факторов."""
        
        # Приветствие
        elif any(word in question_lower for word in ["привет", "здравствуй", "хай"]):
            return """Здравствуйте! Я ваш AI-ассистент для учебы. Я помогу вам разобраться в любых учебных вопросах по математике, физике, химии, программированию и другим предметам. Задавайте ваши вопросы!"""
        
        # Математика
        elif any(word in question_lower for word in ["производная", "интеграл", "математика", "число"]):
            return """Математика - это наука о числах, величинах, формах и их отношениях. Производная показывает скорость изменения функции, а интеграл помогает находить площади и объемы. Математика используется в физике, экономике, инженерии и многих других областях."""
        
        # Физика
        elif any(word in question_lower for word in ["физика", "ньютон", "сила", "движение"]):
            return """Физика - это наука о природе и ее законах. Законы Ньютона описывают движение тел: первое тело сохраняет состояние покоя, второе F=ma, третье действие равно противодействию. Физика изучает механику, термодинамику, электромагнетизм и квантовые явления."""
        
        # Программирование
        elif any(word in question_lower for word in ["программирование", "код", "программа"]):
            return """Программирование - это написание инструкций для компьютера. Программы создаются на языках программирования (Python, JavaScript, C++) и используются для создания сайтов, приложений, игр и систем искусственного интеллекта."""
        
        # Химия
        elif any(word in question_lower for word in ["химия", "химический", "молекула", "атом"]):
            return """Химия - это наука о веществах и их превращениях. Атомы - это строительные блоки материи, а молекулы состоят из атомов. Химические реакции изменяют состав веществ, создавая новые соединения с новыми свойствами."""
        
        # Биология
        elif any(word in question_lower for word in ["биология", "живой", "организм", "клетка"]):
            return """Биология - это наука о живых организмах. Клетка - это основная единица жизни. Биология изучает строение, функции, развитие и взаимодействие живых организмов, от бактерий до растений и животных."""
        
        # Общий ответ
        else:
            return "Я не нашёл точный ответ по вашему запросу. Уточните вопрос (тема/предмет/что именно нужно получить: определение, пример, решение задачи)."

    def _try_solve_arithmetic(self, question):
        raw = (question or "").strip()
        if not raw:
            return None

        raw = raw.replace("×", "*").replace("÷", "/")

        expr_match = re.search(r"[0-9][0-9\s\+\-\*\/\(\)\.,]*[0-9]", raw)
        if not expr_match:
            expr_match = re.search(r"[0-9](?:\s*[\+\-\*\/]\s*[0-9])+", raw)
        if not expr_match:
            return None

        expr = expr_match.group(0).strip()

        if not re.fullmatch(r"[0-9\s\+\-\*\/\(\)\.,]+", expr):
            return None

        if not any(ch.isdigit() for ch in expr):
            return None

        expr = expr.replace(",", ".")

        try:
            node = ast.parse(expr, mode="eval")
        except Exception:
            return None

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

            raise ValueError("Unsupported expression")

        try:
            result = _eval(node)
        except Exception:
            return None

        if isinstance(result, float) and result.is_integer():
            result = int(result)

        return f"{expr} = {result}"
    
    def _build_context(self, context_cards):
        """Формирование контекста из карточек знаний"""
        if not context_cards:
            return ""
        
        context_parts = []
        for card in context_cards:
            context_parts.append(f"Карточка знаний: {card.title}")
            context_parts.append(f"Содержание: {card.content}")
        
        return "\n\n".join(context_parts)
    
    def _fallback_response(self):
        """Ответ по умолчанию, когда AI недоступен"""
        return "Извините, в данный момент AI-ассистент недоступен. Попробуйте позже."


# Создаем глобальный объект ai_assistant для импорта
ai_assistant = AIAssistant()
