# ПРОСТАЯ СИНХРОННАЯ ВЕРСИЯ main.py для Railway
# Убираем все сложное управление event loop

import os
import logging
from datetime import datetime
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# Импортируем наши модули  
from database import DatabaseManager
from agent import FinancialAgent

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Глобальные переменные для компонентов
db_manager = None
agent = None
is_initialized = False

async def initialize_components():
    """Глобальная инициализация компонентов"""
    global db_manager, agent, is_initialized
    
    try:
        logger.info("🔧 Инициализируем базу данных...")
        
        database_url = os.getenv("DATABASE_URL")
        if not database_url:
            raise ValueError("DATABASE_URL не установлен")
        
        # Инициализируем БД
        db_manager = DatabaseManager(database_url)
        await db_manager.initialize()
        
        logger.info("🤖 Инициализируем AI агента...")
        
        # Инициализируем агента
        agent = FinancialAgent(db_manager)
        
        is_initialized = True
        logger.info("✅ Все компоненты инициализированы!")
        
    except Exception as e:
        logger.error(f"❌ Ошибка инициализации: {e}")
        raise

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /start"""
    
    global db_manager, is_initialized
    
    # Создаем пользователя в БД
    if is_initialized and db_manager:
        try:
            await db_manager.create_user_if_not_exists(
                update.effective_chat.id,
                update.effective_user.username,
                update.effective_user.first_name
            )
        except Exception as e:
            logger.error(f"❌ Ошибка создания пользователя: {e}")
    
    welcome_message = """
🤖 **Финансовый Ассистент v3.2**

Полная AI интеграция! 🧠

**Что умею:**
💸 Автоматически извлекать суммы и категории
💰 Понимать естественную речь
📊 Вести учет в PostgreSQL
📈 Генерировать отчеты

**Попробуйте:**
• "Потратил 300 рублей на продукты"
• "Получил зарплату 75000"
• "Какой у меня баланс?"
• "Покажи отчет"

**Команды:**
/help - справка
/balance - баланс
/report - отчет
/status - статус

Просто пишите как обычно! 😊
    """
    
    await update.message.reply_text(welcome_message, parse_mode='Markdown')
    logger.info(f"👋 Пользователь {update.effective_user.id} запустил бота")

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /help"""
    
    help_message = """
🆘 **Справка по AI ассистенту:**

**💡 Естественные команды:**
• "Потратил 500 на продукты" 
• "Заплатил 2000 за интернет"
• "Получил зарплату 50000"
• "Купил кофе за 150"

**📊 Запросы информации:**
• "Какой баланс?"
• "Покажи отчет"
• "Статистика по тратам"

**🤖 Команды:**
/start - начать
/balance - баланс  
/report - отчет
/status - статус
/help - справка

**🧠 AI обработка:**
1. Пишете обычным текстом
2. AI извлекает данные
3. Сохраняется в базу
4. Получаете подтверждение

**Tech:** GPT-4o, LangGraph, PostgreSQL
    """
    
    await update.message.reply_text(help_message, parse_mode='Markdown')

async def balance_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /balance"""
    
    global agent, is_initialized
    
    if not is_initialized:
        await update.message.reply_text("⏳ Система загружается, попробуйте через 10 секунд...")
        return
    
    try:
        response = await agent.process_message("Какой у меня баланс?", update.effective_chat.id)
        await update.message.reply_text(response, parse_mode='Markdown')
    except Exception as e:
        logger.error(f"❌ Ошибка баланса: {e}")
        await update.message.reply_text(f"❌ Ошибка: {str(e)}")

async def report_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /report"""
    
    global agent, is_initialized
    
    if not is_initialized:
        await update.message.reply_text("⏳ Система загружается, попробуйте через 10 секунд...")
        return
    
    try:
        response = await agent.process_message("Покажи подробный отчет", update.effective_chat.id)
        await update.message.reply_text(response, parse_mode='Markdown')
    except Exception as e:
        logger.error(f"❌ Ошибка отчета: {e}")
        await update.message.reply_text(f"❌ Ошибка: {str(e)}")

async def status_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /status"""
    
    global db_manager, agent, is_initialized
    
    # Статусы компонентов
    bot_status = "🟢 Работает"
    db_status = "🟢 Подключена" if db_manager and is_initialized else "🔴 Не готова"
    ai_status = "🟢 Активен" if agent and is_initialized else "🔴 Не готов"
    
    # Переменные окружения
    bot_token = "🟢 Есть" if os.getenv("BOT_TOKEN") else "❌ Нет"
    database_url = "🟢 Есть" if os.getenv("DATABASE_URL") else "❌ Нет"
    openai_key = "🟢 Есть" if os.getenv("OPENAI_API_KEY") else "❌ Нет"
    
    # Статистика пользователя
    user_stats = "📊 Загружаю..."
    if is_initialized and db_manager:
        try:
            balance_info = await db_manager.get_balance(update.effective_chat.id)
            user_stats = f"💰 {balance_info['balance']:.2f} RUB, 📊 {balance_info['transaction_count']} операций"
        except:
            user_stats = "❌ Ошибка загрузки"
    
    status_message = f"""
⚙️ **Статус системы v3.2:**

**🏗️ Компоненты:**
🤖 Telegram Bot: {bot_status}
🗄️ PostgreSQL: {db_status}
🧠 AI Агент: {ai_status}

**🔧 Env переменные:**
🔑 BOT_TOKEN: {bot_token}
🗄️ DATABASE_URL: {database_url}
🤖 OPENAI_API_KEY: {openai_key}

**👤 Ваши данные:**
{user_stats}

**📍 Сервер:**
🌐 Railway.app
⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} UTC
🔄 Готовность: {"✅ Готов" if is_initialized else "⏳ Загружается"}

**🚀 Возможности:**
✅ Понимание естественной речи
✅ Автоматическое извлечение данных  
✅ Постоянное хранение в PostgreSQL
✅ Генерация отчетов и аналитики
    """
    
    await update.message.reply_text(status_message, parse_mode='Markdown')

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик всех сообщений через AI"""
    
    global agent, is_initialized
    
    user_text = update.message.text
    chat_id = update.effective_chat.id
    user_name = update.effective_user.first_name or "Пользователь"
    
    logger.info(f"📝 Сообщение от {user_name} ({chat_id}): {user_text}")
    
    # Проверяем готовность
    if not is_initialized:
        await update.message.reply_text(
            "⏳ **Система загружается...**\n\n"
            "AI агент и база данных запускаются.\n"
            "Попробуйте через 15 секунд или /status"
        )
        return
    
    # Показываем, что печатаем
    await context.bot.send_chat_action(chat_id=chat_id, action="typing")
    
    try:
        # ОБРАБОТКА ЧЕРЕЗ AI АГЕНТА
        response = await agent.process_message(user_text, chat_id)
        await update.message.reply_text(response, parse_mode='Markdown')
        
        logger.info(f"✅ AI ответ отправлен пользователю {user_name}")
        
    except Exception as e:
        logger.error(f"❌ Ошибка AI обработки: {e}")
        
        error_response = f"""❌ **Ошибка обработки**

Сообщение: "{user_text}"
Ошибка: {str(e)}

**Попробуйте:**
• /start - перезапустить
• /status - проверить систему
• /help - справка"""
        
        await update.message.reply_text(error_response, parse_mode='Markdown')

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик ошибок"""
    
    logger.error(f"❌ Ошибка бота: {context.error}")
    
    if update and update.message:
        await update.message.reply_text(
            "❌ **Системная ошибка**\n\n"
            "• /start - перезапустить\n"
            "• /status - проверить\n"
            "• /help - справка"
        )

async def post_init(application):
    """Инициализация после создания приложения"""
    await initialize_components()

def main():
    """Простой синхронный запуск"""
    
    print("🤖 Запуск финансового Telegram бота v3.2")
    print("🧠 Простая версия для Railway")
    
    # Проверяем переменные
    bot_token = os.getenv("BOT_TOKEN")
    if not bot_token:
        print("❌ BOT_TOKEN не установлен")
        return
    
    try:
        logger.info("🔧 Создаем приложение...")
        
        # Создаем приложение
        application = Application.builder().token(bot_token).post_init(post_init).build()
        
        # Добавляем обработчики
        application.add_handler(CommandHandler("start", start_command))
        application.add_handler(CommandHandler("help", help_command))
        application.add_handler(CommandHandler("balance", balance_command))
        application.add_handler(CommandHandler("report", report_command))
        application.add_handler(CommandHandler("status", status_command))
        
        # Главный обработчик сообщений
        application.add_handler(
            MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message)
        )
        
        # Обработчик ошибок
        application.add_error_handler(error_handler)
        
        logger.info("🚀 Запускаем polling...")
        
        # ПРОСТОЙ СИНХРОННЫЙ ЗАПУСК
        application.run_polling(drop_pending_updates=True)
        
    except Exception as e:
        logger.error(f"❌ Критическая ошибка: {e}")
        print(f"❌ Критическая ошибка: {e}")

if __name__ == "__main__":
    main()
