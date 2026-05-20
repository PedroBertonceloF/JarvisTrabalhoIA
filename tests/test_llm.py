import pytest
import json
from unittest.mock import MagicMock, patch
from src.llm import JarvisLLM

@pytest.fixture
def mock_registry():
    registry = MagicMock()
    # Para o teste não quebrar se ele pedir schemas:
    registry.get_tools.return_value = [{"type": "function", "function": {"name": "adicionar_tarefa"}}]
    return registry

@pytest.fixture
def llm_service(mock_registry):
    with patch('src.llm.OpenAI'):
        return JarvisLLM(mock_registry)

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

def test_chat_tool_call(llm_service, mock_registry):
    # Simula o LLM decidindo chamar uma ferramenta via conteúdo (formato customizado do Jarvis)
    tool_call_json = json.dumps({
        "tool_call": "adicionar_tarefa",
        "arguments": {
            "descricao": "Estudar para prova",
            "data_entrega": "2026-05-20"
        }
    })
    tool_call_content = f"```json\n{tool_call_json}\n```"

    # Primeira resposta: LLM pede a ferramenta no content
    mock_response_1 = MagicMock()
    mock_message_1 = MagicMock(content=tool_call_content)
    mock_response_1.choices = [MagicMock(message=mock_message_1)]

    # Segunda resposta: LLM confirma após execução
    mock_response_2 = MagicMock()
    mock_response_2.choices = [
        MagicMock(message=MagicMock(content="Tarefa adicionada!", tool_calls=None))
    ]

    llm_service.client.chat.completions.create.side_effect = [mock_response_1, mock_response_2]
    
    # Simula a execução da ferramenta no registry
    mock_registry.execute.return_value = "Tarefa 1 adicionada."

    messages = [{"role": "user", "content": "Adicione uma tarefa"}]
    response = llm_service.chat(messages)

    # Verifica se o registry foi chamado corretamente
    mock_registry.execute.assert_called_once_with(
        "adicionar_tarefa", 
        {"descricao": "Estudar para prova", "data_entrega": "2026-05-20"}
    )
    assert response == "Tarefa adicionada!"

