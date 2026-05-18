import pytest
import os
import shutil
from src.rag import RAGService

@pytest.fixture
def temp_chroma():
    db_path = "tests/test_chroma_db"
    if os.path.exists(db_path):
        try:
            shutil.rmtree(db_path)
        except Exception:
            pass # Ignora erro se já estiver bloqueado de um teste anterior
        
    rag = RAGService(db_path)
    yield rag
    
    # No Windows, o ChromaDB segura o lock dos arquivos
    # Precisamos limpar a referência do cliente para liberar o arquivo
    rag.client.clear_system_cache()
    del rag
    
    if os.path.exists(db_path):
        try:
            shutil.rmtree(db_path)
        except PermissionError:
            print("Aviso: Não foi possível deletar a pasta temporária do ChromaDB no Windows devido a file lock.")

def test_ingest_and_retrieve(temp_chroma):
    # Simula o texto de um documento
    document_text = "A Regressão Logística é um algoritmo de aprendizado de máquina usado para classificação. Ele prevê a probabilidade de um resultado categórico."
    
    # 1. Testa a ingestão
    success = temp_chroma.ingest_text(
        text=document_text, 
        disciplina="Inteligência Artificial", 
        source_name="aula_1.txt"
    )
    assert success is True

    # 2. Testa a recuperação (RAG)
    results = temp_chroma.search("O que é regressão logística?", n_results=1)
    
    assert len(results) == 1
    assert "classificação" in results[0]["text"]
    assert results[0]["metadata"]["disciplina"] == "Inteligência Artificial"
    assert results[0]["metadata"]["source"] == "aula_1.txt"
