import sqlite3
import os
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash

class Database:
    def __init__(self):
        # ИСПРАВЛЕНИЕ: используем абсолютный путь
        self.db_file = os.path.join(os.getcwd(), 'task_manager.db')
        self.connection = None
        self.connect()
        self.init_db()

    def connect(self):
        """Подключение к SQLite"""
        try:
            self.connection = sqlite3.connect(self.db_file, check_same_thread=False)
            self.connection.row_factory = sqlite3.Row
            print("✅ Успешное подключение к SQLite")
        except Exception as e:
            print(f"❌ Ошибка подключения: {e}")

    def init_db(self):
        """Инициализация таблиц"""
        try:
            cursor = self.connection.cursor()
            
            # Таблица пользователей
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT UNIQUE NOT NULL,
                    email TEXT UNIQUE NOT NULL,
                    password_hash TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Таблица задач
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS tasks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT NOT NULL,
                    description TEXT,
                    status TEXT DEFAULT 'pending',
                    priority TEXT DEFAULT 'medium',
                    due_date TIMESTAMP,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    user_id INTEGER NOT NULL,
                    FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
                )
            ''')
            
            self.connection.commit()
            print("✅ Таблицы инициализированы")
        except Exception as e:
            print(f"❌ Ошибка инициализации БД: {e}")

    def execute_query(self, query, params=None, fetch=False):
        """Выполнение запроса к БД"""
        try:
            cursor = self.connection.cursor()
            cursor.execute(query, params or ())
            
            if fetch:
                result = [dict(row) for row in cursor.fetchall()]
            else:
                result = cursor.lastrowid
                
            self.connection.commit()
            return result
        except Exception as e:
            print(f"❌ Ошибка запроса: {e}")
            return None

    def get_user_by_username(self, username):
        """Получение пользователя по username"""
        query = "SELECT * FROM users WHERE username = ?"
        result = self.execute_query(query, (username,), fetch=True)
        return result[0] if result else None

    def get_user_by_email(self, email):
        """Получение пользователя по email"""
        query = "SELECT * FROM users WHERE email = ?"
        result = self.execute_query(query, (email,), fetch=True)
        return result[0] if result else None

    def get_user_by_id(self, user_id):
        """Получение пользователя по ID"""
        query = "SELECT id, username, email, created_at FROM users WHERE id = ?"
        result = self.execute_query(query, (user_id,), fetch=True)
        return result[0] if result else None

    def create_user(self, username, email, password_hash):
        """Создание нового пользователя"""
        query = """
            INSERT INTO users (username, email, password_hash) 
            VALUES (?, ?, ?)
        """
        user_id = self.execute_query(query, (username, email, password_hash))
        return user_id

    def create_task(self, title, description, status, priority, due_date, user_id):
        """Создание новой задачи"""
        query = """
            INSERT INTO tasks (title, description, status, priority, due_date, user_id)
            VALUES (?, ?, ?, ?, ?, ?)
        """
        task_id = self.execute_query(query, (title, description, status, priority, due_date, user_id))
        return task_id

    def get_user_tasks(self, user_id, status=None, priority=None):
        """Получение задач пользователя с фильтрацией"""
        query = "SELECT * FROM tasks WHERE user_id = ?"
        params = [user_id]

        if status:
            query += " AND status = ?"
            params.append(status)
        if priority:
            query += " AND priority = ?"
            params.append(priority)

        query += " ORDER BY created_at DESC"
        return self.execute_query(query, tuple(params), fetch=True)

    def get_task_by_id(self, task_id, user_id):
        """Получение задачи по ID с проверкой владельца"""
        query = "SELECT * FROM tasks WHERE id = ? AND user_id = ?"
        result = self.execute_query(query, (task_id, user_id), fetch=True)
        return result[0] if result else None

    def update_task(self, task_id, user_id, **updates):
        """Обновление задачи"""
        if not updates:
            return False

        set_clause = ", ".join([f"{key} = ?" for key in updates.keys()])
        query = f"UPDATE tasks SET {set_clause} WHERE id = ? AND user_id = ?"
        
        params = list(updates.values())
        params.extend([task_id, user_id])
        
        self.execute_query(query, tuple(params))
        return True

    def delete_task(self, task_id, user_id):
        """Удаление задачи"""
        query = "DELETE FROM tasks WHERE id = ? AND user_id = ?"
        self.execute_query(query, (task_id, user_id))
        return True

# Глобальный экземпляр базы данных
db = Database()
