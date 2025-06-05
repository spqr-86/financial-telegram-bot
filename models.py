from typing import Literal, Optional, List, TypedDict
from pydantic import BaseModel, Field
from datetime import datetime
import uuid

# Константы для категорий
EXPENSE_CATEGORIES = [
    "Продукты", "Транспорт", "Жилье", "Развлечения", "Здоровье",
    "Образование", "Одежда", "Связь", "Красота", "Путешествия",
    "Подарки", "Кафе/Рестораны", "Спорт", "Автомобиль",
    "Домашние животные", "Дети", "Другое"
]

INCOME_SOURCES = [
    "Зарплата", "Фриланс", "Подработка", "Инвестиции",
    "Дивиденды", "Продажа", "Возврат долга", "Подарок", "Другое"
]

class Transaction(BaseModel):
    """Модель финансовой транзакции"""
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    type: Literal['income', 'expense'] = Field(description="Тип операции: доход или расход")
    amount: float = Field(gt=0, description="Сумма транзакции, должна быть положительной")
    currency: str = Field(default="RUB", description="Валюта транзакции")
    date: datetime = Field(default_factory=datetime.now, description="Дата и время транзакции")
    category_or_source: str = Field(description="Для расходов - категория, для доходов - источник")
    comment: Optional[str] = Field(default=None, description="Дополнительный комментарий")
    
    def to_dict(self) -> dict:
        """Преобразование в словарь для сохранения в БД"""
        return {
            "id": self.id,
            "type": self.type,
            "amount": self.amount,
            "currency": self.currency,
            "date": self.date,
            "category_or_source": self.category_or_source,
            "comment": self.comment
        }
    
    def to_display_dict(self) -> dict:
        """Преобразование для отображения пользователю"""
        return {
            "ID": self.id[:8],
            "Тип": "Доход" if self.type == "income" else "Расход",
            "Сумма": self.amount,
            "Валюта": self.currency,
            "Дата": self.date.strftime("%d.%m.%Y %H:%M"),
            "Категория/Источник": self.category_or_source,
            "Комментарий": self.comment or "-"
        }

class UpdateMemory(TypedDict):
    """Инструмент для агента - определяет тип обновления памяти"""
    update_type: Literal['transaction', 'report_request', 'balance_check']
