import pytest
from src.tools import ToolRegistry

def test_tool_registry_registration():
    registry = ToolRegistry()
    schema = {"name": "test_tool"}
    
    # Dummy function
    def my_tool(x): return x * 2
    
    registry.register(schema, my_tool)
    
    tools = registry.get_tools()
    assert len(tools) == 1
    assert tools[0]["name"] == "test_tool"

def test_tool_registry_execution():
    registry = ToolRegistry()
    registry.register({"name": "add"}, lambda a, b: a + b)
    
    result = registry.execute("add", {"a": 2, "b": 3})
    assert result == 5

def test_tool_registry_execution_not_found():
    registry = ToolRegistry()
    result = registry.execute("unknown", {})
    assert "Ferramenta desconhecida" in result

def test_tool_registry_error_handling():
    registry = ToolRegistry()
    
    def failing_tool():
        raise ValueError("Banco de dados explodiu")
        
    registry.register({"name": "fail"}, failing_tool)
    
    # Deve capturar o erro e retornar como string, não deve dar raise
    result = registry.execute("fail", {})
    assert "Erro na execução da ferramenta: Banco de dados explodiu" in str(result)
