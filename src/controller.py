import io
import PyPDF2
import json

class AppController:
    def __init__(self, rag_service, learning_service, llm_service, storage_service):
        self.rag_service = rag_service
        self.learning_service = learning_service
        self.llm_service = llm_service
        self.storage_service = storage_service

    def register_tools(self, registry):
        """
        Registra todas as ferramentas acadêmicas no registry fornecido.
        Concentra a lógica de orquestração entre serviços.
        """
        registry.register({
            "type": "function",
            "function": {
                "name": "adicionar_tarefa",
                "description": "Adiciona uma nova tarefa à agenda do usuário.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "descricao": {"type": "string", "description": "A descrição da tarefa."},
                        "data_entrega": {"type": "string", "description": "Data de entrega (YYYY-MM-DD)."}
                    },
                    "required": ["descricao", "data_entrega"]
                }
            }
        }, lambda descricao, data_entrega: f"Tarefa adicionada com sucesso! ID: {self.storage_service.add_task(descricao, data_entrega)}")

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
        }, lambda descricao, data, horario=None: f"Evento adicionado com sucesso! ID: {self.storage_service.add_event(descricao, data, horario)}")

        registry.register({
            "type": "function",
            "function": {
                "name": "consultar_agenda",
                "description": "Consulta eventos e tarefas agendados para uma data específica.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "data": {"type": "string", "description": "Data da consulta no formato YYYY-MM-DD."}
                    },
                    "required": ["data"]
                }
            }
        }, lambda data: json.dumps(self.storage_service.get_agenda_by_date(data), ensure_ascii=False))

        registry.register({
            "type": "function",
            "function": {
                "name": "listar_tarefas",
                "description": "Retorna todas as tarefas salvas no sistema.",
                "parameters": {
                    "type": "object",
                    "properties": {}
                }
            }
        }, lambda: json.dumps(self.storage_service.get_all_tasks(), ensure_ascii=False))

        registry.register({
            "type": "function",
            "function": {
                "name": "concluir_tarefa",
                "description": "Marca uma tarefa como concluída.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "task_id": {"type": "integer", "description": "O ID numérico da tarefa."}
                    },
                    "required": ["task_id"]
                }
            }
        }, lambda task_id: f"Tarefa {task_id} concluída!" if self.storage_service.complete_task(task_id) else "Falha.")

        registry.register({
            "type": "function",
            "function": {
                "name": "buscar_material_rag",
                "description": "Busca informações nos materiais de estudo anexados.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "pergunta": {"type": "string", "description": "A pergunta ou termos de busca."}
                    },
                    "required": ["pergunta"]
                }
            }
        }, lambda pergunta: json.dumps(self.rag_service.search(pergunta), ensure_ascii=False) or "Nenhuma informação relevante.")
        
        registry.register({
            "type": "function",
            "function": {
                "name": "gerar_plano_estudos",
                "description": "Gera um plano de estudos personalizado baseado na agenda, dificuldades e materiais do aluno.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "data_inicio": {"type": "string", "description": "Data de início do plano (YYYY-MM-DD)."},
                        "data_fim": {"type": "string", "description": "Data de término do plano (YYYY-MM-DD)."},
                        "disciplina": {"type": "string", "description": "Opcional: Focar em uma disciplina específica."}
                    },
                    "required": ["data_inicio", "data_fim"]
                }
            }
        }, lambda data_inicio, data_fim, disciplina=None: self.learning_service.generate_study_plan(data_inicio, data_fim, disciplina, self.llm_service, self.storage_service))

    def extract_study_plan(self, content: str) -> list | None:
        """
        Tenta extrair a lista de tarefas estruturadas de um conteúdo de texto (markdown com bloco JSON).
        """
        if "```json" not in content:
            return None
            
        try:
            start = content.find("```json") + 7
            end = content.find("```", start)
            json_str = content[start:end].strip()
            plan_data = json.loads(json_str)
            
            # Valida se é o formato esperado de plano de estudos
            if isinstance(plan_data, list) and len(plan_data) > 0 and "description" in plan_data[0]:
                return plan_data
        except Exception:
            pass
            
        return None

    def accept_study_plan(self, plan: list) -> int:
        """
        Salva as tarefas de um plano na agenda. Retorna a quantidade de tarefas adicionadas.
        """
        count = 0
        for task in plan:
            self.storage_service.add_task(task["description"], task["due_date"])
            count += 1
        return count

    def process_material(self, filename: str, content: bytes, disciplina: str) -> tuple[bool, str]:
        """
        Processa o upload de um material (PDF ou TXT) e salva no RAG.
        Retorna (Sucesso, Mensagem).
        """
        if not disciplina:
            return False, "Preencha a disciplina para anexar o arquivo."
            
        try:
            text_content = ""
            if filename.endswith('.txt'):
                text_content = content.decode("utf-8")
            elif filename.endswith('.pdf'):
                pdf_file = io.BytesIO(content)
                pdf_reader = PyPDF2.PdfReader(pdf_file)
                for page in pdf_reader.pages:
                    text_content += page.extract_text() + "\n"
            else:
                return False, "Formato de arquivo não suportado."

            if not text_content.strip():
                return False, "Não foi possível extrair texto do arquivo."

            success = self.rag_service.ingest_text(
                text=text_content, 
                disciplina=disciplina, 
                source_name=filename
            )
            
            if success:
                return True, f"Material '{filename}' salvo em '{disciplina}' com sucesso!"
            else:
                return False, "Erro interno ao salvar no banco vetorial."
                
        except Exception as e:
            return False, f"Erro ao processar arquivo: {str(e)}"

    def start_review_session(self, disciplina: str, state: dict) -> tuple[bool, str]:
        """
        Inicia uma sessão de revisão, atualizando o dicionário de estado.
        Retorna (Sucesso, Mensagem).
        """
        if not disciplina:
            return False, "Digite uma disciplina para revisar."
            
        question_data = self.learning_service.generate_question(disciplina, self.llm_service)
        
        if "Não encontrei" in question_data["question"]:
            return False, question_data["question"]
            
        # Modifica o estado do Streamlit
        state["review_mode"] = True
        state["review_disciplina"] = disciplina
        state["review_question"] = question_data["question"]
        state["review_context"] = question_data["context"]
        
        return True, "Sessão iniciada."

    def evaluate_review_answer(self, state: dict, answer: str) -> dict:
        """
        Avalia a resposta do usuário, salva dificuldade se houver, encerra o modo e retorna o resultado.
        """
        evaluation = self.learning_service.evaluate_answer(
            state.get("review_question", ""),
            state.get("review_context", ""),
            answer,
            self.llm_service
        )
        
        status = evaluation.get("status", "UNKNOWN")
        
        # Se a resposta foi parcial ou incorreta, registramos a dificuldade para a recomendação
        if status in ["PARTIAL", "INCORRECT"]:
            topic = evaluation.get("topic", "Desconhecido")
            disciplina = state.get("review_disciplina", "Desconhecida")
            self.storage_service.add_difficulty(disciplina, topic)
        
        # Encerra o modo após responder
        state["review_mode"] = False
        
        return evaluation
