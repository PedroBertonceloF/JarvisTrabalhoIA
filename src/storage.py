import sqlite3
import os

class Storage:
    def __init__(self, db_path):
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        # Garante que a pasta data exista
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            # Tabela de Tarefas (subclasse de eventos na lógica de negócio)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS tasks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    description TEXT NOT NULL,
                    due_date TEXT NOT NULL,
                    completed INTEGER DEFAULT 0
                )
            """)
            # Tabela de Eventos Gerais (Aulas, Provas)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    description TEXT NOT NULL,
                    date TEXT NOT NULL,
                    time TEXT
                )
            """)
            conn.commit()

    def add_event(self, description: str, date: str, time: str = None) -> int:
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO events (description, date, time) VALUES (?, ?, ?)",
                (description, date, time)
            )
            conn.commit()
            return cursor.lastrowid

    def get_all_events(self):
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM events")
            rows = cursor.fetchall()
            return [dict(row) for row in rows]

    def get_agenda_by_date(self, date: str):
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            # Busca eventos
            cursor.execute("SELECT * FROM events WHERE date = ?", (date,))
            events = [dict(row) for row in cursor.fetchall()]
            
            # Busca tarefas
            cursor.execute("SELECT * FROM tasks WHERE due_date = ?", (date,))
            tasks = [dict(row) for row in cursor.fetchall()]
            
            return {
                "events": events,
                "tasks": tasks
            }

    def add_task(self, description: str, due_date: str) -> int:
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO tasks (description, due_date) VALUES (?, ?)",
                (description, due_date)
            )
            conn.commit()
            return cursor.lastrowid

    def get_all_tasks(self):
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM tasks")
            rows = cursor.fetchall()
            return [dict(row) for row in rows]

    def complete_task(self, task_id: int) -> bool:
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("UPDATE tasks SET completed = 1 WHERE id = ?", (task_id,))
            conn.commit()
            return cursor.rowcount > 0
