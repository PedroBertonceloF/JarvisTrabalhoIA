import pytest
import os
from src.storage import Storage

@pytest.fixture
def temp_db():
    db_path = "tests/test_jarvis.db"
    # Garante que o banco comece limpo
    if os.path.exists(db_path):
        os.remove(db_path)
    
    storage = Storage(db_path)
    yield storage
    
    # Limpa depois do teste
    if os.path.exists(db_path):
        os.remove(db_path)

def test_add_event(temp_db):
    event_id = temp_db.add_event("Aula de IA", "2026-05-18", "19:00")
    events = temp_db.get_all_events()
    
    assert len(events) == 1
    assert events[0]["description"] == "Aula de IA"
    assert events[0]["date"] == "2026-05-18"
    assert events[0]["time"] == "19:00"

def test_add_task(temp_db):
    task_id = temp_db.add_task("Estudar Redes Neurais", "2026-05-20")
    tasks = temp_db.get_all_tasks()
    
    assert len(tasks) == 1
    assert tasks[0]["description"] == "Estudar Redes Neurais"
    assert tasks[0]["due_date"] == "2026-05-20"
    assert tasks[0]["completed"] == 0

def test_complete_task(temp_db):
    task_id = temp_db.add_task("Fazer exercício de IA", "2026-05-19")
    success = temp_db.complete_task(task_id)
    
    assert success is True
    tasks = temp_db.get_all_tasks()
    assert tasks[0]["completed"] == 1

def test_get_agenda_by_date(temp_db):
    temp_db.add_event("Aula de IA", "2026-05-18", "19:00")
    temp_db.add_task("Estudar para prova", "2026-05-18")
    temp_db.add_task("Outra tarefa", "2026-05-19")
    
    agenda = temp_db.get_agenda_by_date("2026-05-18")
    
    assert len(agenda["events"]) == 1
    assert len(agenda["tasks"]) == 1
    assert agenda["events"][0]["description"] == "Aula de IA"
    assert agenda["tasks"][0]["description"] == "Estudar para prova"
