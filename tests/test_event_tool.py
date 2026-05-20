import pytest
import json
from src.tools import ToolRegistry
from src.storage import Storage
import os

def test_adicionar_evento_tool_integration():
    # Setup
    db_path = "tests/test_events_tool.db"
    if os.path.exists(db_path):
        os.remove(db_path)
    
    storage = Storage(db_path)
    registry = ToolRegistry()
    
    # REGISTRO
    registry.register({
        "type": "function",
        "function": {
            "name": "adicionar_evento",
            "description": "Adiciona um novo evento (aula, prova, reunião) à agenda do usuário.",
            "parameters": {
                "type": "object",
                "properties": {
                    "descricao": {"type": "string", "description": "A descrição do evento."},
                    "data": {"type": "string", "description": "Data do evento (YYYY-MM-DD)."},
                    "horario": {"type": "string", "description": "Horário do evento (HH:MM), opcional."}
                },
                "required": ["descricao", "data"]
            }
        }
    }, lambda descricao, data, horario=None: f"Evento adicionado com sucesso! ID: {storage.add_event(descricao, data, horario)}")
    
    # Execução
    result = registry.execute("adicionar_evento", {
        "descricao": "Aula de IA",
        "data": "2026-05-20",
        "horario": "19:00"
    })
    
    # Asserção: Esperamos que o ID do evento seja retornado
    assert "Evento adicionado com sucesso" in str(result)
    
    # Verifica se salvou no banco
    events = storage.get_all_events()
    assert len(events) == 1
    assert events[0]["description"] == "Aula de IA"
    
    if os.path.exists(db_path):
        os.remove(db_path)
