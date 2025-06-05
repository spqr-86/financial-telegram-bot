# ИСПРАВЛЕННЫЙ main.py - версия для продакшн сервера
# Проблема: конфликт event loop в production среде
# Решение: используем синхронный запуск вместо asyncio.run()

import os
import logging
from datetime import datetime
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

class FinancialTelegramBot:
    """Продакшн версия Telegram бота для финансового ассистента"""
    
    def __init__(self):
        # Получаем переменные окружения
        self.bot_token = os.getenv("BOT_TOKEN")
        
        if not self.bot_token:
            raise ValueError("❌ BOT_TOKEN не установлен в переменных окружения")
        
        self.application = None
        logger.info("✅ Бот инициализирован")
    
    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик команды /start"""
        
        welcome_message = """
🤖 **Финансовый Ассистент v2.0**

Я помогу управлять вашими финансами через простые команды!

**Примеры команд:**
💸 "Потратил 300 рублей на продукты"
💰 "Получил зарплату 50000"  
📊 "Какой у меня баланс?"

**Команды бота:**
/help - подробная справка
/balance - быстрый баланс
/status - статус системы

Пишите обычными сообщениями! 😊
        """
        
        await update.message.reply_text(welcome_message, parse_mode='Markdown')
        logger.info(f"✅ Пользователь {update.effective_user.id} запустил бота")
    
    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик команды /help"""
        
        help_message = """
🆘 **Подробная справка:**

**Добавление операций:**
• "Потратил 500 на продукты"
• "Получил зарплату 45000" 
• "Заплатил 2000 за интернет"
• "Купил кофе за 150"

**Проверка статистики:**
• "Какой баланс?"
• "Покажи отчет"
• "Сколько потратил?"

**Команды бота:**
/start - начать работу
/balance - быстрый баланс
/status - проверить статус
/help - эта справка

**Статус интеграции:**
🟡 Базовый бот: работает
🔄 AI агент: интегрируется
🔄 База данных: настраивается

Бот понимает естественную речь! 🧠
        """
        
        await update.message.reply_text(help_message, parse_mode='Markdown')
    
    async def balance_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Быстрая команда проверки баланса"""
        
        response = """💰 **Быстрый баланс:**

Текущий баланс: 0.00 RUB
💚 Доходы: 0.00 RUB
❤️ Расходы: 0.00 RUB
📊 Операций: 0

_🔄 Интеграция с AI агентом и базой данных в процессе..._

Скоро здесь будет ваша реальная статистика!"""
        
        await update.message.reply_text(response, parse_mode='Markdown')
        logger.info(f"📊 Пользователь {update.effective_user.id} запросил баланс")
    
    async def status_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Команда проверки статуса системы"""
        
        # Проверяем доступность компонентов
        bot_status = "🟢 Работает"
        db_status = "🔄 Настраивается"
        ai_status = "🔄 Интегрируется"
        
        # Проверяем переменные окружения
        openai_key = "🟢 Настроен" if os.getenv("OPENAI_API_KEY") else "❌ Отсутствует"
        db_url = "🟢 Настроена" if os.getenv("DATABASE_URL") else "❌ Отсутствует"
        
        status_message = f"""
⚙️ **Статус системы:**

**Компоненты:**
🤖 Telegram Bot: {bot_status}
🗄️ База данных: {db_status}
🧠 AI Агент: {ai_status}

**Конфигурация:**
🔑 OpenAI API: {openai_key}
🗄️ Database URL: {db_url}

**Версия:** v2.0 Production
**Сервер:** Railway.app
**Время:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} UTC

_Следующее обновление: интеграция AI агента_
        """
        
        await update.message.reply_text(status_message, parse_mode='Markdown')
        logger.info(f"⚙️ Пользователь {update.effective_user.id} запросил статус")
    
    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик всех текстовых сообщений"""
        
        user_text = update.message.text
        chat_id = update.effective_chat.id
        user_name = update.effective_user.first_name or "Пользователь"
        
        logger.info(f"📝 Сообщение от {user_name} ({chat_id}): {user_text}")
        
        # Показываем, что бот печатает
        await context.bot.send_chat_action(chat_id=chat_id, action="typing")
        
        # Базовая обработка сообщений (пока без AI агента)
        user_text_lower = user_text.lower()
        
        if any(word in user_text_lower for word in ["баланс", "сколько", "денег"]):
            response = """💰 **Ваш баланс:**

Текущий баланс: 0.00 RUB
📊 Операций: 0

_🔄 Скоро здесь будет интеграция с AI агентом для точного учета!_

Попробуйте команду /balance для быстрого просмотра."""
            
        elif any(word in user_text_lower for word in ["потратил", "заплатил", "купил", "трата"]):
            response = """✅ **Расход будет добавлен**

📝 Ваше сообщение: "{}"

_🔄 Интеграция с AI агентом позволит автоматически извлекать:_
• Сумму
• Категорию
• Дату
• Комментарий

А пока используйте команды для тестирования!""".format(user_text)
            
        elif any(word in user_text_lower for word in ["получил", "зарплата", "доход", "заработал"]):
            response = """✅ **Доход будет добавлен**

📝 Ваше сообщение: "{}"

_🔄 AI агент скоро сможет автоматически определять:_
• Сумму дохода
• Источник (зарплата, фриланс, etc)
• Дату получения

Следите за обновлениями!""".format(user_text)
            
        elif any(word in user_text_lower for word in ["отчет", "статистика", "аналитика"]):
            response = """📊 **Отчет будет сгенерирован**

_🔄 В следующей версии здесь будет:_
• Расходы по категориям
• Динамика доходов
• Графики и диаграммы
• Прогнозы

А пока попробуйте /status для проверки системы."""
            
        else:
            response = f"""🤖 **Сообщение получено!**

Вы написали: _"{user_text}"_

**Что уже работает:**
✅ Получение и обработка сообщений
✅ Команды бота (/start, /help, /balance)
✅ Деплой на продакшн сервере

**В разработке:**
🔄 AI обработка естественной речи
🔄 Автоматическое извлечение данных
🔄 Сохранение в базу данных

Попробуйте команду /help для справки!"""
        
        await update.message.reply_text(response, parse_mode='Markdown')
        logger.info(f"✅ Отправлен ответ пользователю {user_name}")
    
    async def error_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик ошибок"""
        
        logger.error(f"❌ Ошибка бота: {context.error}")
        
        if update and update.message:
            await update.message.reply_text(
                "❌ Произошла ошибка при обработке сообщения.\n\n"
                "Попробуйте:\n"
                "• /start - перезапустить\n"
                "• /status - проверить систему\n"
                "• /help - получить справку"
            )
    
    def setup_handlers(self):
        """Настройка обработчиков команд и сообщений"""
        
        # Команды
        self.application.add_handler(CommandHandler("start", self.start_command))
        self.application.add_handler(CommandHandler("help", self.help_command))
        self.application.add_handler(CommandHandler("balance", self.balance_command))
        self.application.add_handler(CommandHandler("status", self.status_command))
        
        # Обработчик текстовых сообщений
        self.application.add_handler(
            MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_message)
        )
        
        # Обработчик ошибок
        self.application.add_error_handler(self.error_handler)
    
    def run(self):
        """СИНХРОННЫЙ запуск бота - исправление для продакшн"""
        
        logger.info("🔧 Создаем приложение Telegram...")
        
        # Создаем приложение
        self.application = Application.builder().token(self.bot_token).build()
        
        # Настраиваем обработчики
        self.setup_handlers()
        
        logger.info("🚀 Запускаем бота в режиме polling (синхронно)...")
        
        # ВАЖНО: Используем синхронный метод для продакшн
        self.application.run_polling(
            drop_pending_updates=True,  # Игнорируем старые сообщения
        )

def main():
    """СИНХРОННАЯ главная функция - исправление для продакшн"""
    
    print("🤖 Запуск финансового Telegram бота (Production v2.0)...")
    
    try:
        bot = FinancialTelegramBot()
        
        # ВАЖНО: НЕ используем asyncio.run() в продакшн
        bot.run()
        
    except ValueError as e:
        logger.error(f"❌ Ошибка конфигурации: {e}")
        print(f"❌ Ошибка конфигурации: {e}")
        
    except KeyboardInterrupt:
        logger.info("🛑 Бот остановлен пользователем")
        print("🛑 Бот остановлен пользователем")
        
    except Exception as e:
        logger.error(f"❌ Критическая ошибка: {e}")
        print(f"❌ Критическая ошибка: {e}")

if __name__ == "__main__":
    # СИНХРОННЫЙ запуск без asyncio.run()
    main()
