# ФИНАЛЬНЫЙ ИСПРАВЛЕННЫЙ main.py v3.1
# Исправлена проблема с event loop для продакшн среды

import os
import logging
import asyncio
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

class FinancialTelegramBot:
    """Продакшн версия финансового Telegram бота с AI агентом"""
    
    def __init__(self):
        # Получаем переменные окружения
        self.bot_token = os.getenv("BOT_TOKEN")
        self.database_url = os.getenv("DATABASE_URL")
        self.openai_key = os.getenv("OPENAI_API_KEY")
        
        # Проверяем обязательные переменные
        if not self.bot_token:
            raise ValueError("❌ BOT_TOKEN не установлен в переменных окружения")
        if not self.database_url:
            raise ValueError("❌ DATABASE_URL не установлен в переменных окружения")
        if not self.openai_key:
            raise ValueError("❌ OPENAI_API_KEY не установлен в переменных окружения")
        
        # Инициализируем компоненты
        self.application = None
        self.db_manager = None
        self.agent = None
        self.is_initialized = False
        
        logger.info("✅ Бот создан, ожидание инициализации...")
    
    async def initialize_components(self):
        """Асинхронная инициализация базы данных и AI агента"""
        
        try:
            logger.info("🔧 Инициализируем базу данных...")
            
            # Инициализируем менеджер базы данных
            self.db_manager = DatabaseManager(self.database_url)
            await self.db_manager.initialize()
            
            logger.info("🤖 Инициализируем AI агента...")
            
            # Инициализируем финансового агента
            self.agent = FinancialAgent(self.db_manager)
            
            self.is_initialized = True
            logger.info("✅ Все компоненты инициализированы успешно!")
            
        except Exception as e:
            logger.error(f"❌ Ошибка инициализации компонентов: {e}")
            raise
    
    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик команды /start"""
        
        # Создаем пользователя в БД если нужно
        if self.is_initialized:
            try:
                await self.db_manager.create_user_if_not_exists(
                    update.effective_chat.id,
                    update.effective_user.username,
                    update.effective_user.first_name
                )
            except Exception as e:
                logger.error(f"❌ Ошибка создания пользователя: {e}")
        
        welcome_message = """
🤖 **Финансовый Ассистент v3.1**

Теперь с полной AI интеграцией! 🧠

**Что умею:**
💸 Автоматически извлекать суммы и категории
💰 Понимать естественную речь
📊 Вести учет в базе данных
📈 Генерировать умные отчеты

**Попробуйте:**
• "Потратил 300 рублей на продукты в Пятерочке"
• "Получил зарплату 75000 рублей"
• "Какой у меня баланс?"
• "Покажи отчет по тратам"

**Команды:**
/help - справка
/balance - быстрый баланс
/report - отчет
/status - состояние системы

Просто пишите как обычно - я понимаю! 😊
        """
        
        await update.message.reply_text(welcome_message, parse_mode='Markdown')
        logger.info(f"👋 Пользователь {update.effective_user.id} запустил бота")
    
    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик команды /help"""
        
        help_message = """
🆘 **Справка по использованию AI ассистента:**

**💡 Естественные команды:**
• "Потратил 500 на продукты" 
• "Заплатил 2000 за интернет"
• "Получил зарплату 50000"
• "Продал машину за 800000"
• "Купил кофе за 150 в Starbucks"

**📊 Запросы информации:**
• "Какой баланс?"
• "Сколько потратил на продукты?"
• "Покажи отчет за месяц"
• "Статистика по категориям"

**🤖 Команды бота:**
/start - перезапустить
/balance - быстрый баланс  
/report - подробный отчет
/status - состояние системы
/help - эта справка

**🧠 Как работает AI:**
1. Вы пишете обычным текстом
2. AI извлекает сумму, категорию, тип операции
3. Данные сохраняются в базу
4. Получаете подтверждение и актуальный баланс

**Технологии:** GPT-4, LangGraph, PostgreSQL
        """
        
        await update.message.reply_text(help_message, parse_mode='Markdown')
    
    async def balance_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Быстрая команда проверки баланса"""
        
        if not self.is_initialized:
            await update.message.reply_text("⏳ Система инициализируется, попробуйте через несколько секунд...")
            return
        
        try:
            response = await self.agent.process_message("Какой у меня баланс?", update.effective_chat.id)
            await update.message.reply_text(response, parse_mode='Markdown')
            
        except Exception as e:
            logger.error(f"❌ Ошибка в balance_command: {e}")
            await update.message.reply_text(f"❌ Ошибка получения баланса: {str(e)}")
    
    async def report_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Команда генерации отчета"""
        
        if not self.is_initialized:
            await update.message.reply_text("⏳ Система инициализируется, попробуйте через несколько секунд...")
            return
        
        try:
            response = await self.agent.process_message("Покажи подробный отчет", update.effective_chat.id)
            await update.message.reply_text(response, parse_mode='Markdown')
            
        except Exception as e:
            logger.error(f"❌ Ошибка в report_command: {e}")
            await update.message.reply_text(f"❌ Ошибка генерации отчета: {str(e)}")
    
    async def status_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Команда проверки статуса системы"""
        
        # Проверяем статус компонентов
        bot_status = "🟢 Работает"
        db_status = "🟢 Подключена" if self.db_manager and self.is_initialized else "🔴 Не готова"
        ai_status = "🟢 Активен" if self.agent and self.is_initialized else "🔴 Не готов"
        
        # Проверяем переменные окружения
        env_checks = {
            "BOT_TOKEN": "🟢 Настроен" if self.bot_token else "❌ Отсутствует",
            "DATABASE_URL": "🟢 Настроена" if self.database_url else "❌ Отсутствует", 
            "OPENAI_API_KEY": "🟢 Настроен" if self.openai_key else "❌ Отсутствует"
        }
        
        # Получаем статистику пользователя если возможно
        user_stats = "📊 Загружаю..."
        if self.is_initialized:
            try:
                balance_info = await self.db_manager.get_balance(update.effective_chat.id)
                user_stats = f"💰 Баланс: {balance_info['balance']:.2f} RUB, 📊 Операций: {balance_info['transaction_count']}"
            except:
                user_stats = "❌ Ошибка загрузки"
        
        status_message = f"""
⚙️ **Статус системы v3.1:**

**🏗️ Компоненты:**
🤖 Telegram Bot: {bot_status}
🗄️ PostgreSQL: {db_status}
🧠 AI Агент: {ai_status}

**🔧 Конфигурация:**
🔑 {env_checks["BOT_TOKEN"]} BOT_TOKEN
🗄️ {env_checks["DATABASE_URL"]} DATABASE_URL  
🤖 {env_checks["OPENAI_API_KEY"]} OPENAI_API_KEY

**👤 Ваша статистика:**
{user_stats}

**📍 Развертывание:**
🌐 Railway.app
⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} UTC
🔄 Инициализация: {"✅ Завершена" if self.is_initialized else "⏳ В процессе"}

**🚀 Возможности:**
✅ Понимание естественной речи
✅ Автоматическое извлечение данных
✅ Постоянное хранение в БД
✅ Генерация отчетов и аналитики
        """
        
        await update.message.reply_text(status_message, parse_mode='Markdown')
        logger.info(f"⚙️ Пользователь {update.effective_user.id} запросил статус")
    
    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик всех текстовых сообщений через AI агента"""
        
        user_text = update.message.text
        chat_id = update.effective_chat.id
        user_name = update.effective_user.first_name or "Пользователь"
        
        logger.info(f"📝 Сообщение от {user_name} ({chat_id}): {user_text}")
        
        # Проверяем готовность системы
        if not self.is_initialized:
            await update.message.reply_text(
                "⏳ **Система инициализируется...**\n\n"
                "AI агент и база данных запускаются.\n"
                "Попробуйте через 10-15 секунд или используйте /status для проверки."
            )
            return
        
        # Показываем, что бот печатает
        await context.bot.send_chat_action(chat_id=chat_id, action="typing")
        
        try:
            # ГЛАВНАЯ МАГИЯ: обрабатываем через AI агента
            response = await self.agent.process_message(user_text, chat_id)
            await update.message.reply_text(response, parse_mode='Markdown')
            
            logger.info(f"✅ AI ответ отправлен пользователю {user_name}")
            
        except Exception as e:
            logger.error(f"❌ Ошибка обработки через AI: {e}")
            
            error_response = f"""❌ **Ошибка обработки сообщения**

Сообщение: "{user_text}"
Ошибка: {str(e)}

**Что можно попробовать:**
• /start - перезапустить
• /status - проверить систему  
• /help - получить справку

Или попробуйте переформулировать запрос."""
            
            await update.message.reply_text(error_response, parse_mode='Markdown')
    
    async def error_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Глобальный обработчик ошибок"""
        
        logger.error(f"❌ Глобальная ошибка бота: {context.error}")
        
        if update and update.message:
            await update.message.reply_text(
                "❌ **Произошла системная ошибка**\n\n"
                "Попробуйте:\n"
                "• /start - перезапустить\n"
                "• /status - проверить систему\n"
                "• /help - получить справку\n\n"
                "Если проблема повторяется - обратитесь к администратору."
            )
    
    def setup_handlers(self):
        """Настройка всех обработчиков"""
        
        # Команды
        self.application.add_handler(CommandHandler("start", self.start_command))
        self.application.add_handler(CommandHandler("help", self.help_command))
        self.application.add_handler(CommandHandler("balance", self.balance_command))
        self.application.add_handler(CommandHandler("report", self.report_command))
        self.application.add_handler(CommandHandler("status", self.status_command))
        
        # Обработчик всех текстовых сообщений (ГЛАВНЫЙ - через AI агента)
        self.application.add_handler(
            MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_message)
        )
        
        # Глобальный обработчик ошибок
        self.application.add_error_handler(self.error_handler)
    
    async def run_async(self):
        """Полностью асинхронный запуск"""
        
        try:
            logger.info("🔧 Создаем приложение Telegram...")
            
            # Создаем приложение
            self.application = Application.builder().token(self.bot_token).build()
            
            # Настраиваем обработчики
            self.setup_handlers()
            
            logger.info("⚙️ Инициализируем компоненты...")
            
            # Инициализируем компоненты
            await self.initialize_components()
            
            logger.info("🚀 Запускаем бота в режиме polling...")
            
            # Запускаем бота асинхронно
            await self.application.run_polling(
                drop_pending_updates=True,
                close_loop=False
            )
            
        except Exception as e:
            logger.error(f"❌ Ошибка в run_async: {e}")
            raise

def main():
    """Главная функция - правильный запуск для продакшн"""
    
    print("🤖 Запуск финансового Telegram бота v3.1")
    print("🧠 С AI агентом, PostgreSQL и полной интеграцией")
    
    try:
        bot = FinancialTelegramBot()
        
        # ПРАВИЛЬНЫЙ способ запуска в продакшн
        if os.name == 'nt':  # Windows
            asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
        
        # Создаем новый event loop для продакшн
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            # Запускаем полностью асинхронно
            loop.run_until_complete(bot.run_async())
        finally:
            # Правильно закрываем loop
            loop.close()
        
    except ValueError as e:
        logger.error(f"❌ Ошибка конфигурации: {e}")
        print(f"❌ Ошибка конфигурации: {e}")
        print("🔧 Проверьте переменные окружения в Railway")
        
    except KeyboardInterrupt:
        logger.info("🛑 Бот остановлен пользователем")
        print("🛑 Бот остановлен пользователем")
        
    except Exception as e:
        logger.error(f"❌ Критическая ошибка: {e}")
        print(f"❌ Критическая ошибка: {e}")

if __name__ == "__main__":
    main()
