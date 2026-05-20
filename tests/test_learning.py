import pytest
import json
from unittest.mock import MagicMock
from src.learning import LearningService

@pytest.fixture
def mock_rag():
    return MagicMock()

@pytest.fixture
def mock_llm():
    return MagicMock()

@pytest.fixture
def learning_service(mock_rag):
    return LearningService(mock_rag)

def test_generate_review_question(learning_service, mock_rag, mock_llm):
    # Arrange
    mock_rag.search.return_value = [
        {"text": "Redes Neurais Artificiais são sistemas de computação inspirados nas redes neurais biológicas que constituem os cérebros dos animais.", "metadata": {"source": "ia_aula.txt"}}
    ]
    
    mock_llm.chat.return_value = "O que inspirou a criação das Redes Neurais Artificiais?"
    
    # Act
    question_data = learning_service.generate_question("Inteligência Artificial", mock_llm)
    
    # Assert
    assert "question" in question_data
    assert "context" in question_data
    assert "redes neurais" in question_data["context"].lower()
    mock_rag.search.assert_called_once()
    mock_llm.chat.assert_called_once()

def test_evaluate_answer_structured(learning_service, mock_llm):
    # Arrange
    question = "O que inspirou a criação das Redes Neurais Artificiais?"
    context = "Redes Neurais Artificiais são sistemas de computação inspirados nas redes neurais biológicas que constituem os cérebros dos animais."
    user_answer = "Foram inspiradas nos cérebros de animais."
    
    # Simula a LLM retornando o JSON estruturado
    expected_json = {
        "status": "CORRECT",
        "feedback": "Correto! As RNAs são inspiradas nas redes neurais biológicas dos cérebros animais.",
        "topic": "Redes Neurais Artificiais"
    }
    mock_llm.chat.return_value = json.dumps(expected_json)
    
    # Act
    evaluation = learning_service.evaluate_answer(question, context, user_answer, mock_llm)
        
    # Assert
    assert evaluation["status"] == "CORRECT"
    assert "Correto" in evaluation["feedback"]
    assert evaluation["topic"] == "Redes Neurais Artificiais"
    mock_llm.chat.assert_called_once()

def test_generate_study_plan(learning_service, mock_llm, mock_rag):
    # Setup mocks
    mock_storage = MagicMock()
    mock_storage.get_agenda_by_date_range.return_value = {
        "events": [{"description": "Aula de IA", "date": "2026-05-18"}],
        "tasks": [{"description": "Estudar RAG", "due_date": "2026-05-19"}]
    }
    mock_storage.get_difficulties.return_value = [{"topic": "Chunking", "disciplina": "IA"}]
    
    mock_rag.search.return_value = [{"text": "O chunking é importante...", "metadata": {"source": "rag.pdf"}}]
    
    # Simula resposta da LLM com o formato bipartido
    mock_llm.chat.return_value = """Aqui está seu plano:
- Estude Chunking.
```json
[{"description": "Estudar Chunking", "due_date": "2026-05-18"}]
```"""
    
    # Act
    plan = learning_service.generate_study_plan(
        "2026-05-18", "2026-05-24", "IA", mock_llm, mock_storage
    )
    
    # Assert
    assert "Aqui está seu plano" in plan
    assert "```json" in plan
    mock_storage.get_agenda_by_date_range.assert_called_once()
    mock_rag.search.assert_called()
    mock_llm.chat.assert_called_once()

