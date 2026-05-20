import json

class LearningService:
    def __init__(self, rag_service):
        self.rag_service = rag_service

    def generate_question(self, disciplina: str, llm_service) -> dict:
        """
        Busca material relevante no RAG para a disciplina e usa a LLM para gerar uma pergunta.
        """
        resultados = self.rag_service.search(query=disciplina, n_results=3)
        
        if not resultados:
            return {
                "question": f"Não encontrei materiais sobre {disciplina} para gerar uma pergunta. Que tal adicionar alguns?",
                "context": ""
            }
        
        context = "\n---\n".join([r["text"] for r in resultados])
        
        prompt = f"""
        Você é o Jarvis, um assistente acadêmico.
        Baseado estritamente no CONTEXTO abaixo, formule UMA pergunta direta e objetiva para testar o conhecimento do aluno.
        
        CONTEXTO:
        {context}
        """
        
        messages = [{"role": "user", "content": prompt}]
        question = llm_service.chat(messages)
        
        return {
            "question": question,
            "context": context
        }

    def evaluate_answer(self, question: str, context: str, user_answer: str, llm_service) -> dict:
        """
        Usa o LLM para avaliar a resposta do usuário e retorna um JSON estruturado.
        """
        prompt = f"""
        Você é o Jarvis, um assistente acadêmico. 
        Avalie a resposta do aluno para a pergunta abaixo, usando o contexto fornecido como referência de verdade.
        
        CONTEXTO:
        {context}
        
        PERGUNTA:
        {question}
        
        RESPOSTA DO ALUNO:
        {user_answer}
        
        Você DEVE responder EXCLUSIVAMENTE com um JSON válido no seguinte formato:
        {{
            "status": "CORRECT" ou "PARTIAL" ou "INCORRECT",
            "feedback": "Um feedback construtivo explicando o porquê.",
            "topic": "Uma string curta (2-4 palavras) resumindo o tópico que foi testado."
        }}
        """
        
        messages = [{"role": "user", "content": prompt}]
        response_text = llm_service.chat(messages)
        
        try:
            # Tenta limpar o texto caso a LLM retorne markdown (ex: ```json ... ```)
            cleaned_text = response_text.strip()
            if cleaned_text.startswith("```json"):
                cleaned_text = cleaned_text[7:-3].strip()
            elif cleaned_text.startswith("```"):
                cleaned_text = cleaned_text[3:-3].strip()
                
            return json.loads(cleaned_text)
        except json.JSONDecodeError:
            # Fallback seguro caso a LLM falhe em gerar o JSON
            return {
                "status": "PARTIAL",
                "feedback": f"Aqui está a avaliação: {response_text}",
                "topic": "Tópico Desconhecido"
            }

    def generate_study_plan(self, data_inicio: str, data_fim: str, disciplina: str, llm_service, storage_service) -> str:
        """
        Gera um plano de estudos consolidado.
        Busca agenda, dificuldades e materiais relevantes para compor o prompt.
        """
        # 1. Busca dados da Agenda (Eventos e Tarefas)
        agenda = storage_service.get_agenda_by_date_range(data_inicio, data_fim)
        
        # 2. Busca Dificuldades (filtradas por disciplina se fornecida)
        dificuldades = storage_service.get_difficulties(disciplina if disciplina else None)
        
        # 3. Busca Materiais no RAG (baseado nas dificuldades ou na disciplina)
        query_rag = disciplina if disciplina else " ".join([d["topic"] for d in dificuldades[:3]])
        materiais = []
        if query_rag.strip():
            materiais = self.rag_service.search(query=query_rag, n_results=5)
        
        # 4. Constrói o Prompt
        context_agenda = json.dumps(agenda, ensure_ascii=False, indent=2)
        context_dificuldades = json.dumps(dificuldades[:5], ensure_ascii=False, indent=2)
        context_materiais = "\n---\n".join([f"FONTE: {m['metadata']['source']}\nCONTEÚDO: {m['text']}" for m in materiais])
        
        prompt = f"""
        Você é o Jarvis, um assistente acadêmico. Sua tarefa é gerar um PLANO DE ESTUDOS personalizado.
        
        INTERVALO DO PLANO: {data_inicio} até {data_fim}
        DISCIPLINA FOCO: {disciplina if disciplina else "Todas"}
        
        CONTEXTO DA AGENDA (Eventos e Tarefas agendadas):
        {context_agenda}
        
        DIFICULDADES RECENTES DO ALUNO:
        {context_dificuldades}
        
        MATERIAIS DE ESTUDO DISPONÍVEIS (RAG):
        {context_materiais}
        
        REQUISITOS DO PLANO:
        1. Organize os estudos de forma lógica entre as datas fornecidas.
        2. Priorize os tópicos de dificuldade do aluno.
        3. Recomende a leitura de materiais específicos (cite o nome da fonte).
        4. Respeite os horários de eventos (aulas/provas) já agendados.
        
        FORMATO DA RESPOSTA:
        Sua resposta deve ser dividida em duas partes:
        Parte 1: Um texto Markdown amigável e motivador detalhando o plano dia a dia.
        Parte 2: Um bloco de código JSON contendo EXCLUSIVAMENTE uma lista de tarefas estruturadas para serem adicionadas à agenda, seguindo este formato exato:
        
        ```json
        [
            {{"description": "Estudar [Tópico]", "due_date": "YYYY-MM-DD"}},
            ...
        ]
        ```
        """
        
        messages = [{"role": "user", "content": prompt}]
        return llm_service.chat(messages)

