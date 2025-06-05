import asyncpg
import json
import uuid
from typing import List, Dict, Optional
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class DatabaseManager:
    """Менеджер базы данных для финансового бота"""
    
    def __init__(self, database_url: str):
        self.database_url = database_url
        self.pool = None
    
    async def initialize(self):
        """Инициализация пула соединений и создание таблиц"""
        
        try:
            # Создаем пул соединений
            self.pool = await asyncpg.create_pool(
                self.database_url,
                min_size=1,
                max_size=5,
                command_timeout=60
            )
            
            # Создаем таблицы
            async with self.pool.acquire() as conn:
                # Таблица пользователей
                await conn.execute("""
                    CREATE TABLE IF NOT EXISTS users (
                        telegram_id BIGINT PRIMARY KEY,
                        username VARCHAR(255),
                        first_name VARCHAR(255),
                        created_at TIMESTAMP DEFAULT NOW(),
                        settings JSONB DEFAULT '{}'::jsonb
                    )
                """)
                
                # Таблица транзакций
                await conn.execute("""
                    CREATE TABLE IF NOT EXISTS transactions (
                        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                        telegram_id BIGINT REFERENCES users(telegram_id),
                        type VARCHAR(10) NOT NULL CHECK (type IN ('income', 'expense')),
                        amount DECIMAL(12,2) NOT NULL CHECK (amount > 0),
                        currency VARCHAR(3) DEFAULT 'RUB',
                        category_or_source VARCHAR(100) NOT NULL,
                        comment TEXT,
                        transaction_date TIMESTAMP DEFAULT NOW(),
                        created_at TIMESTAMP DEFAULT NOW()
                    )
                """)
                
                # Индексы для производительности
                await conn.execute("""
                    CREATE INDEX IF NOT EXISTS idx_transactions_user_date 
                    ON transactions(telegram_id, transaction_date DESC)
                """)
                
                await conn.execute("""
                    CREATE INDEX IF NOT EXISTS idx_transactions_type 
                    ON transactions(telegram_id, type)
                """)
            
            logger.info("✅ База данных инициализирована")
            
        except Exception as e:
            logger.error(f"❌ Ошибка инициализации БД: {e}")
            raise
    
    async def create_user_if_not_exists(self, telegram_id: int, username: str = None, first_name: str = None):
        """Создание пользователя если не существует"""
        
        try:
            async with self.pool.acquire() as conn:
                await conn.execute("""
                    INSERT INTO users (telegram_id, username, first_name) 
                    VALUES ($1, $2, $3) 
                    ON CONFLICT (telegram_id) DO UPDATE SET
                        username = EXCLUDED.username,
                        first_name = EXCLUDED.first_name
                """, telegram_id, username, first_name)
                
        except Exception as e:
            logger.error(f"❌ Ошибка создания пользователя: {e}")
            raise
    
    async def save_transaction(self, telegram_id: int, transaction_data: Dict):
        """Сохранение транзакции"""
        
        try:
            async with self.pool.acquire() as conn:
                # Сначала создаем пользователя если не существует
                await self.create_user_if_not_exists(telegram_id)
                
                # Сохраняем транзакцию
                transaction_id = await conn.fetchval("""
                    INSERT INTO transactions 
                    (telegram_id, type, amount, currency, category_or_source, comment, transaction_date)
                    VALUES ($1, $2, $3, $4, $5, $6, $7)
                    RETURNING id
                """, 
                    telegram_id,
                    transaction_data['type'],
                    float(transaction_data['amount']),
                    transaction_data.get('currency', 'RUB'),
                    transaction_data['category_or_source'],
                    transaction_data.get('comment'),
                    transaction_data.get('date', datetime.now())
                )
                
                logger.info(f"✅ Транзакция сохранена: {transaction_id}")
                return str(transaction_id)
                
        except Exception as e:
            logger.error(f"❌ Ошибка сохранения транзакции: {e}")
            raise
    
    async def get_user_transactions(self, telegram_id: int, limit: int = 100) -> List[Dict]:
        """Получение транзакций пользователя"""
        
        try:
            async with self.pool.acquire() as conn:
                rows = await conn.fetch("""
                    SELECT 
                        id, type, amount, currency, category_or_source, 
                        comment, transaction_date, created_at
                    FROM transactions 
                    WHERE telegram_id = $1 
                    ORDER BY transaction_date DESC 
                    LIMIT $2
                """, telegram_id, limit)
                
                return [dict(row) for row in rows]
                
        except Exception as e:
            logger.error(f"❌ Ошибка получения транзакций: {e}")
            return []
    
    async def get_balance(self, telegram_id: int) -> Dict:
        """Расчет баланса пользователя"""
        
        try:
            async with self.pool.acquire() as conn:
                result = await conn.fetchrow("""
                    SELECT 
                        COALESCE(SUM(CASE WHEN type = 'income' THEN amount ELSE 0 END), 0) as total_income,
                        COALESCE(SUM(CASE WHEN type = 'expense' THEN amount ELSE 0 END), 0) as total_expense,
                        COUNT(*) as transaction_count
                    FROM transactions 
                    WHERE telegram_id = $1
                """, telegram_id)
                
                if result and result['transaction_count'] > 0:
                    balance = float(result['total_income']) - float(result['total_expense'])
                    return {
                        'balance': balance,
                        'total_income': float(result['total_income']),
                        'total_expense': float(result['total_expense']),
                        'transaction_count': result['transaction_count']
                    }
                else:
                    return {
                        'balance': 0.0,
                        'total_income': 0.0,
                        'total_expense': 0.0,
                        'transaction_count': 0
                    }
                    
        except Exception as e:
            logger.error(f"❌ Ошибка расчета баланса: {e}")
            return {
                'balance': 0.0,
                'total_income': 0.0,
                'total_expense': 0.0,
                'transaction_count': 0
            }
    
    async def get_expenses_by_category(self, telegram_id: int) -> Dict[str, float]:
        """Получение расходов по категориям"""
        
        try:
            async with self.pool.acquire() as conn:
                rows = await conn.fetch("""
                    SELECT category_or_source, SUM(amount) as total
                    FROM transactions 
                    WHERE telegram_id = $1 AND type = 'expense'
                    GROUP BY category_or_source
                    ORDER BY total DESC
                """, telegram_id)
                
                return {row['category_or_source']: float(row['total']) for row in rows}
                
        except Exception as e:
            logger.error(f"❌ Ошибка получения расходов по категориям: {e}")
            return {}
    
    async def close(self):
        """Закрытие соединений с базой данных"""
        if self.pool:
            await self.pool.close()
            logger.info("✅ Соединения с БД закрыты")
