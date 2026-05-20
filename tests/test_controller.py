import pytest
from unittest.mock import MagicMock
from src.controller import AppController

@pytest.fixture
def mock_rag():
    return MagicMock()

@pytest.fixture
def mock_learning():
    return MagicMock()

@pytest.fixture
def mock_llm():
    return MagicMock()

@pytest.fixture
def mock_storage():
    return MagicMock()

@pytest.fixture
def controller(mock_rag, mock_learning, mock_llm, mock_storage):
    return AppController(mock_rag, mock_learning, mock_llm, mock_storage)

def test_process_material_txt(controller, mock_rag):
    mock_rag.ingest_text.return_value = True
    
    success, message = controller.process_material(
        filename="aula.txt",
        content=b"Texto da aula",
        disciplina="IA"
    )
    
    assert success is True
    assert "salvo" in message
    mock_rag.ingest_text.assert_called_once_with(
        text="Texto da aula",
        disciplina="IA",
        source_name="aula.txt"
    )

def test_process_material_empty_disciplina(controller):
    success, message = controller.process_material("aula.txt", b"txt", "")
    assert success is False
    assert "Preencha a disciplina" in message

def test_start_review_session(controller, mock_learning, mock_llm):
    # Simula o retorno da geração de pergunta
    mock_learning.generate_question.return_value = {
        "question": "O que é IA?",
        "context": "Contexto de IA"
    }
    
    state = {}
    success, message = controller.start_review_session("IA", state)
    
    assert success is True
    assert state["review_mode"] is True
    assert state["review_disciplina"] == "IA"
    assert state["review_question"] == "O que é IA?"
    assert state["review_context"] == "Contexto de IA"

def test_evaluate_review_answer_correct(controller, mock_learning, mock_storage):
    mock_learning.evaluate_answer.return_value = {
        "status": "CORRECT",
        "feedback": "Muito bem",
        "topic": "Conceitos"
    }
    
    state = {
        "review_disciplina": "IA",
        "review_question": "Pergunta",
        "review_context": "Contexto",
        "review_mode": True
    }
    
    evaluation = controller.evaluate_review_answer(state, "Minha resposta")
    
    assert evaluation["status"] == "CORRECT"
    assert state["review_mode"] is False # Encerra após responder
    mock_storage.add_difficulty.assert_not_called()

def test_evaluate_review_answer_incorrect(controller, mock_learning, mock_storage):
    mock_learning.evaluate_answer.return_value = {
        "status": "INCORRECT",
        "feedback": "Errado",
        "topic": "Redes Neurais"
    }
    
    state = {
        "review_disciplina": "IA",
        "review_question": "Pergunta",
        "review_context": "Contexto",
        "review_mode": True
    }
    
    evaluation = controller.evaluate_review_answer(state, "Minha resposta")
    
    assert evaluation["status"] == "INCORRECT"
    assert state["review_mode"] is False
    mock_storage.add_difficulty.assert_called_once_with("IA", "Redes Neurais")

def test_register_academic_tools(controller):
    mock_registry = MagicMock()
    
    # Act
    controller.register_tools(mock_registry)
    
    # Assert: Verifica se as ferramentas obrigatórias foram registradas
    # O mock_registry.register.call_args_list conterá todas as chamadas
    registered_tool_names = [call.args[0]["function"]["name"] for call in mock_registry.register.call_args_list]
    
    expected_tools = [
        "adicionar_tarefa", 
        "adicionar_evento", 
        "consultar_agenda", 
        "listar_tarefas", 
        "concluir_tarefa", 
        "buscar_material_rag", 
        "gerar_plano_estudos"
    ]
    
    for tool in expected_tools:
        assert tool in registered_tool_names

def test_extract_study_plan(controller):
    content = """Aqui está seu plano:
- Estude IA.
```json
[{"description": "Estudar IA", "due_date": "2026-05-20"}]
```"""
    plan = controller.extract_study_plan(content)
    assert plan is not None
    assert len(plan) == 1
    assert plan[0]["description"] == "Estudar IA"

def test_extract_study_plan_none(controller):
    content = "Apenas um texto normal."
    plan = controller.extract_study_plan(content)
    assert plan is None

def test_accept_study_plan(controller, mock_storage):
    plan = [{"description": "Tarefa 1", "due_date": "2026-05-20"}]
    count = controller.accept_study_plan(plan)
    assert count == 1
    mock_storage.add_task.assert_called_once_with("Tarefa 1", "2026-05-20")

