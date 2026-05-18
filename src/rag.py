import os
import chromadb
from chromadb.utils import embedding_functions

class RAGService:
    def __init__(self, db_path: str):
        self.db_path = db_path
        # Garante que a pasta exista
        os.makedirs(self.db_path, exist_ok=True)
        
        # Inicializa o cliente do ChromaDB apontando para a pasta local
        self.client = chromadb.PersistentClient(path=self.db_path)
        
        # Usa o modelo leve que decidimos no ADR 0002
        self.embedding_fn = embedding_functions.SentenceTransformerEmbeddingFunction(
            model_name=os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2")
        )
        
        # Cria ou carrega a coleção onde os textos ficarão salvos
        self.collection = self.client.get_or_create_collection(
            name="materiais_academicos",
            embedding_function=self.embedding_fn
        )

    def _chunk_text(self, text: str, chunk_size: int = 1000, overlap: int = 200) -> list[str]:
        """
        Uma implementação simples de chunking (divisão de texto).
        No mundo real, usaríamos LangChain RecursiveCharacterTextSplitter, 
        mas fazer na mão mantém o sistema leve e sem dependências extras.
        """
        chunks = []
        start = 0
        text_length = len(text)
        
        while start < text_length:
            end = start + chunk_size
            chunks.append(text[start:end])
            start = end - overlap
            
        return chunks

    def ingest_text(self, text: str, disciplina: str, source_name: str) -> bool:
        """Divide o texto em pedaços e salva no banco vetorial."""
        try:
            chunks = self._chunk_text(text)
            
            # Prepara os IDs e Metadados para cada pedaço
            ids = [f"{source_name}_chunk_{i}" for i in range(len(chunks))]
            metadatas = [{"disciplina": disciplina, "source": source_name} for _ in range(len(chunks))]
            
            # Salva no ChromaDB (ele gera os embeddings automaticamente)
            self.collection.add(
                documents=chunks,
                metadatas=metadatas,
                ids=ids
            )
            return True
        except Exception as e:
            print(f"Erro ao ingerir texto: {e}")
            return False

    def search(self, query: str, n_results: int = 3) -> list[dict]:
        """Busca os trechos mais relevantes para a pergunta."""
        try:
            results = self.collection.query(
                query_texts=[query],
                n_results=n_results
            )
            
            # Formata a resposta
            formatted_results = []
            if results["documents"] and len(results["documents"][0]) > 0:
                for i in range(len(results["documents"][0])):
                    formatted_results.append({
                        "text": results["documents"][0][i],
                        "metadata": results["metadatas"][0][i],
                        "distance": results["distances"][0][i] if "distances" in results else None
                    })
            return formatted_results
        except Exception as e:
            print(f"Erro na busca RAG: {e}")
            return []
