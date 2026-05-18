import pytest
import json
from unittest.mock import MagicMock, patch
from src.llm import JarvisLLM

@pytest.fixture
def mock_storage():
    return MagicMock()

@pytest.fixture
def llm_service(mock_storage):
    with patch('src.llm.OpenAI'):
        return JarvisLLM(mock_storage)

def test_chat_simple_response(llm_service):
    # Simula a resposta da OpenAI
    mock_response = MagicMock()
    mock_response.choices = [
        MagicMock(message=MagicMock(content="Olá, eu sou o Jarvis!", tool_calls=None))
    ]
    llm_service.client.chat.completions.create.return_value = mock_response

    messages = [{"role": "user", "content": "Oi"}]
    response = llm_service.chat(messages)

    assert response == "Olá, eu sou o Jarvis!"
    llm_service.client.chat.completions.create.assert_called_once()

def test_chat_tool_call_add_task(llm_service, mock_storage):
    # Simula o LLM decidindo chamar uma ferramenta
    mock_tool_call = MagicMock()
    mock_tool_call.function.name = "adicionar_tarefa"
    mock_tool_call.function.arguments = json.dumps({
        "descricao": "Estudar para prova",
        "data_entrega": "2026-05-20"
    })
    mock_tool_call.id = "call_123"

    # Primeira resposta: LLM pede a ferramenta
    mock_response_1 = MagicMock()
    mock_message_1 = MagicMock(content=None, tool_calls=[mock_tool_call])
    mock_response_1.choices = [MagicMock(message=mock_message_1)]

    # Segunda resposta: LLM confirma após execução
    mock_response_2 = MagicMock()
    mock_response_2.choices = [
        MagicMock(message=MagicMock(content="Tarefa adicionada!", tool_calls=None))
    ]

    llm_service.client.chat.completions.create.side_effect = [mock_response_1, mock_response_2]

    messages = [{"role": "user", "content": "Adicione uma tarefa"}]
    response = llm_service.chat(messages)

    # Verifica se o storage foi chamado corretamente
    mock_storage.add_task.assert_called_once_with(description="Estudar para prova", due_date="2026-05-20")
    assert response == "Tarefa adicionada!"
