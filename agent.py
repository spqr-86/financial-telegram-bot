import os
import logging
from datetime import datetime
from typing import Dict, Any
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage
from trustcall import create_extractor
from models import Transaction, UpdateMemory, EXPENSE_CATEGORIES, INCOME_SOURCES
from database import DatabaseManager

logger = logging.getLogger(__name__)

class FinancialAgent:
    """LangGraph агент для финансового анализа, адаптированный для PostgreSQL"""
    
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager
        
        # Инициализируем модель OpenAI
        openai_key = os.getenv("OPENAI_API_KEY")
        if not openai_key:
            raise ValueError("❌ OPENAI_API_KEY не установлен")
            
        self.model = ChatOpenAI(model="gpt-4o-mini", temperature=0)
        
        # Создаем Trustcall экстрактор
        self.transaction_extractor = create_extractor(
            self.model,
            tools=[Transaction],
            tool_choice="Transaction",
            enable_inserts=True
        )
        
        logger.info("✅ Финансовый агент инициализирован")
    
    async def process_message(self, user_text: str, telegram_id: int) -> str:
        """Главная функция обработки сообщения пользователя"""
        
        try:
            # Получаем контекст пользователя из базы данных
            user_context = await self._get_user_context(telegram_id)
            
            # Определяем тип запроса
            request_type = await self._classify_request(user_text, user_context)
            
            # Обрабатываем в зависимости от типа
            if request_type == "transaction":
                return await self._process_transaction(user_text, telegram_id)
            elif request_type == "balance_check":
                return await self._process_balance_request(telegram_id)
            elif request_type == "report_request":
                return await self._process_report_request(telegram_id)
            else:
                return await self._process_general_request(user_text, user_context)
                
        except Exception as e:
            logger.error(f"❌ Ошибка обработки сообщения: {e}")
            return f"❌ Ошибка обработки запроса: {str(e)}"
    
    async def _get_user_context(self, telegram_id: int) -> Dict[str, Any]:
        """Получение контекста пользователя из базы данных"""
        
        try:
            balance_info = await self.db_manager.get_balance(telegram_id)
            recent_transactions = await self.db_manager.get_user_transactions(telegram_id, limit=5)
            
            return {
                "balance": balance_info,
                "recent_transactions": recent_transactions,
                "telegram_id": telegram_id
            }
            
        except Exception as e:
            logger.error(f"❌ Ошибка получения контекста: {e}")
            return {"balance": {"balance": 0, "transaction_count": 0}, "recent_transactions": []}
    
    async def _classify_request(self, user_text: str, context: Dict) -> str:
        """Классификация типа запроса пользователя"""
        
        user_text_lower = user_text.lower()
        
        # Определяем тип запроса по ключевым словам
        if any(word in user_text_lower for word in ["баланс", "сколько", "денег", "остаток"]):
            return "balance_check"
        elif any(word in user_text_lower for word in ["отчет", "статистика", "аналитика", "траты"]):
            return "report_request"
        elif any(word in user_text_lower for word in ["потратил", "заплатил", "купил", "получил", "зарплата", "доход"]):
            return "transaction"
        else:
            return "general"
    
    async def _process_transaction(self, user_text: str, telegram_id: int) -> str:
        """Обработка добавления транзакции через Trustcall"""
        
        try:
            # Формируем инструкцию для Trustcall
            instruction = f"""
Извлеките информацию о финансовой транзакции из сообщения пользователя.

Определите:
1. Тип операции: 'income' (доход) или 'expense' (расход)
2. Сумму (только положительные числа)
3. Категорию для расходов или источник для доходов
4. Дополнительные комментарии

Время: {datetime.now().isoformat()}
Категории расходов: {", ".join(EXPENSE_CATEGORIES)}
Источники доходов: {", ".join(INCOME_SOURCES)}

Сообщение пользователя: "{user_text}"
"""
            
            # Создаем сообщения для Trustcall
            messages = [
                SystemMessage(content=instruction),
                HumanMessage(content=user_text)
            ]
            
            # Извлекаем данные транзакции
            result = self.transaction_extractor.invoke({"messages": messages})
            
            if result["responses"]:
                transaction = result["responses"][0]
                
                # Сохраняем в базу данных
                transaction_data = transaction.to_dict()
                transaction_id = await self.db_manager.save_transaction(telegram_id, transaction_data)
                
                # Формируем ответ пользователю
                transaction_type_ru = "Доход" if transaction.type == "income" else "Расход"
                
                response = f"""✅ **Операция добавлена:**

📊 **{transaction_type_ru}:** {transaction.amount} {transaction.currency}
🏷️ **Категория:** {transaction.category_or_source}"""
                
                if transaction.comment:
                    response += f"\n💬 **Комментарий:** {transaction.comment}"
                
                # Добавляем актуальный баланс
                balance_info = await self.db_manager.get_balance(telegram_id)
                response += f"\n\n💰 **Текущий баланс:** {balance_info['balance']:.2f} RUB"
                
                return response
            else:
                return "❌ Не удалось извлечь данные транзакции из сообщения"
                
        except Exception as e:
            logger.error(f"❌ Ошибка обработки транзакции: {e}")
            return f"❌ Ошибка при добавлении транзакции: {str(e)}"
    
    async def _process_balance_request(self, telegram_id: int) -> str:
        """Обработка запроса баланса"""
        
        try:
            balance_info = await self.db_manager.get_balance(telegram_id)
            
            if balance_info['transaction_count'] == 0:
                return """💰 **Ваш баланс:**

Текущий баланс: 0.00 RUB
📝 У вас пока нет транзакций

Начните добавлять доходы и расходы!
Например: "Потратил 300 рублей на продукты\""""
            
            response = f"""💰 **Ваш финансовый баланс:**

**Текущий баланс:** {balance_info['balance']:.2f} RUB

💚 **Всего доходов:** {balance_info['total_income']:.2f} RUB
❤️ **Всего расходов:** {balance_info['total_expense']:.2f} RUB
📊 **Операций:** {balance_info['transaction_count']}"""
            
            return response
            
        except Exception as e:
            logger.error(f"❌ Ошибка получения баланса: {e}")
            return f"❌ Ошибка при получении баланса: {str(e)}"
    
    async def _process_report_request(self, telegram_id: int) -> str:
        """Обработка запроса отчета"""
        
        try:
            balance_info = await self.db_manager.get_balance(telegram_id)
            
            if balance_info['transaction_count'] == 0:
                return "📊 **Отчет пуст** - добавьте транзакции для анализа"
            
            # Получаем расходы по категориям
            expenses_by_category = await self.db_manager.get_expenses_by_category(telegram_id)
            recent_transactions = await self.db_manager.get_user_transactions(telegram_id, limit=10)
            
            response = "📊 **ФИНАНСОВЫЙ ОТЧЕТ**\\n\\n"
            
            # Общая статистика
            response += f"💰 **Баланс:** {balance_info['balance']:.2f} RUB\\n"
            response += f"💚 **Доходы:** {balance_info['total_income']:.2f} RUB\\n"
            response += f"❤️ **Расходы:** {balance_info['total_expense']:.2f} RUB\\n\\n"
            
            # Расходы по категориям
            if expenses_by_category:
                response += "💸 **РАСХОДЫ ПО КАТЕГОРИЯМ:**\\n"
                for category, amount in sorted(expenses_by_category.items(), key=lambda x: x[1], reverse=True):
                    response += f"   • {category}: {amount:.2f} RUB\\n"
                response += "\\n"
            
            # Последние транзакции
            if recent_transactions:
                response += "📝 **ПОСЛЕДНИЕ ОПЕРАЦИИ:**\\n"
                for t in recent_transactions[:5]:
                    type_emoji = "💚" if t['type'] == 'income' else "❤️"
                    date_str = t['transaction_date'].strftime("%d.%m")
                    response += f"   {type_emoji} {date_str}: {t['amount']:.0f} RUB ({t['category_or_source']})\\n"
            
            return response
            
        except Exception as e:
            logger.error(f"❌ Ошибка генерации отчета: {e}")
            return f"❌ Ошибка при генерации отчета: {str(e)}"
    
    async def _process_general_request(self, user_text: str, context: Dict) -> str:
        """Обработка общих запросов"""
        
        return f"""🤖 **Сообщение получено!**

Вы написали: _"{user_text}"_

**Доступные команды:**
• "Потратил 300 рублей на продукты" - добавить расход
• "Получил зарплату 50000" - добавить доход  
• "Какой у меня баланс?" - проверить баланс
• "Покажи отчет" - получить аналитику

**Ваша статистика:**
💰 Баланс: {context['balance']['balance']:.2f} RUB
📊 Операций: {context['balance']['transaction_count']}"""
