import os
import asyncio
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
🤖 **Финансовый Ассистент запущен!**

Я помогу управлять вашими финансами через простые команды.

**Примеры команд:**
💸 "Потратил 300 рублей на продукты"
💰 "Получил зарплату 50000"  
📊 "Какой у меня баланс?"

**Команды бота:**
/help - справка
/balance - быстрый баланс
/clear - очистить данные

Пишите обычными сообщениями! 😊
        """
        
        await update.message.reply_text(welcome_message, parse_mode='Markdown')
        logger.info(f"Пользователь {update.effective_user.id} запустил бота")
    
    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик команды /help"""
        
        help_message = """
🆘 **Справка по использованию:**

**Добавление операций:**
• "Потратил 500 на продукты"
• "Получил зарплату 45000" 
• "Заплатил 2000 за интернет"

**Проверка статистики:**
• "Какой баланс?"
• "Покажи отчет"
• "Сколько потратил?"

**Команды:**
/start - начать работу
/balance - быстрый баланс
/clear - очистить все данные

Бот понимает естественную речь! 🧠
        """
        
        await update.message.reply_text(help_message, parse_mode='Markdown')
    
    async def balance_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Быстрая команда проверки баланса"""
        
        # Здесь будет интеграция с вашим агентом
        # Пока заглушка для тестирования
        
        response = "💰 **Быстрый баланс:**\n\nБаланс: 0.00 RUB\n📝 Транзакций: 0\n\n_Интеграция с агентом в процессе..._"
        await update.message.reply_text(response, parse_mode='Markdown')
    
    async def clear_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Очистка данных пользователя"""
        
        # Здесь будет очистка через базу данных
        # Пока заглушка
        
        await update.message.reply_text("🗑️ **Данные очищены**\n\n_Функция в разработке..._", parse_mode='Markdown')
    
    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик всех текстовых сообщений"""
        
        user_text = update.message.text
        chat_id = update.effective_chat.id
        user_name = update.effective_user.first_name or "Пользователь"
        
        logger.info(f"Сообщение от {user_name} ({chat_id}): {user_text}")
        
        # Показываем, что бот печатает
        await context.bot.send_chat_action(chat_id=chat_id, action="typing")
        
        # ЗДЕСЬ БУДЕТ ИНТЕГРАЦИЯ С ВАШИМ LANGRAPH АГЕНТОМ
        # Пока простая заглушка для тестирования
        
        if "баланс" in user_text.lower():
            response = "💰 Ваш текущий баланс: 0.00 RUB\n\n_Интеграция с агентом скоро будет добавлена_"
        elif "потратил" in user_text.lower() or "заплатил" in user_text.lower():
            response = "✅ Расход будет добавлен\n\n_Интеграция с агентом в процессе..._"
        elif "получил" in user_text.lower():
            response = "✅ Доход будет добавлен\n\n_Интеграция с агентом в процессе..._"
        else:
            response = f"🤖 Получил ваше сообщение: \"{user_text}\"\n\n_Полная интеграция с AI агентом будет добавлена на следующем шаге_"
        
        await update.message.reply_text(response, parse_mode='Markdown')
        logger.info(f"Отправлен ответ пользователю {user_name}")
    
    async def error_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик ошибок"""
        
        logger.error(f"Ошибка бота: {context.error}")
        
        if update and update.message:
            await update.message.reply_text(
                "❌ Произошла ошибка. Попробуйте еще раз или обратитесь к администратору."
            )
    
    def setup_handlers(self):
        """Настройка обработчиков команд и сообщений"""
        
        # Команды
        self.application.add_handler(CommandHandler("start", self.start_command))
        self.application.add_handler(CommandHandler("help", self.help_command))
        self.application.add_handler(CommandHandler("balance", self.balance_command))
        self.application.add_handler(CommandHandler("clear", self.clear_command))
        
        # Обработчик текстовых сообщений
        self.application.add_handler(
            MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_message)
        )
        
        # Обработчик ошибок
        self.application.add_error_handler(self.error_handler)
    
    async def run(self):
        """Запуск бота в режиме polling"""
        
        # Создаем приложение
        self.application = Application.builder().token(self.bot_token).build()
        
        # Настраиваем обработчики
        self.setup_handlers()
        
        logger.info("🚀 Запускаем бота в режиме polling...")
        
        # Запускаем polling
        await self.application.run_polling(
            drop_pending_updates=True,  # Игнорируем старые сообщения
            close_loop=False
        )

async def main():
    """Главная функция запуска"""
    
    try:
        bot = FinancialTelegramBot()
        await bot.run()
    except ValueError as e:
        logger.error(e)
        print("❌ Ошибка конфигурации:", e)
    except Exception as e:
        logger.error(f"Критическая ошибка: {e}")
        print("❌ Критическая ошибка:", e)

if __name__ == "__main__":
    print("🤖 Запуск финансового Telegram бота...")
    asyncio.run(main())
