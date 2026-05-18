import os
import json
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

class JarvisLLM:
    def __init__(self, storage, rag_service):
        self.storage = storage
        self.rag_service = rag_service
        self.client = OpenAI(
            base_url=os.getenv("OPENAI_BASE_URL", "http://localhost:11434/v1"),
            api_key=os.getenv("OPENAI_API_KEY", "ollama")
        )
        self.model = os.getenv("MODEL_NAME", "gemma")

    def get_tools(self):
        return [
            {
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
            },
            {
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
            },
            {
                "type": "function",
                "function": {
                    "name": "listar_tarefas",
                    "description": "Retorna todas as tarefas salvas no sistema, incluindo seus IDs e status.",
                    "parameters": {
                        "type": "object",
                        "properties": {}
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "concluir_tarefa",
                    "description": "Marca uma tarefa específica como concluída usando o seu ID.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "task_id": {"type": "integer", "description": "O ID numérico da tarefa."}
                        },
                        "required": ["task_id"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "buscar_material_rag",
                    "description": "Busca informações detalhadas nos materiais de estudo anexados pelo usuário. Use esta ferramenta sempre que o usuário fizer perguntas sobre conteúdos acadêmicos, matérias ou disciplinas.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "pergunta": {"type": "string", "description": "A pergunta específica ou os termos de busca a serem procurados no material."}
                        },
                        "required": ["pergunta"]
                    }
                }
            }
        ]

    def chat(self, messages):
        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            tools=self.get_tools()
        )
        
        response_message = response.choices[0].message
        
        # Verifica se o LLM decidiu chamar alguma ferramenta
        if response_message.tool_calls:
            # Adiciona a mensagem do assistente (com a chamada da ferramenta) ao histórico
            messages.append(response_message)
            
            for tool_call in response_message.tool_calls:
                function_name = tool_call.function.name
                # Fallback para string vazia se arguments vier None (algumas LLMs fazem isso)
                args_str = tool_call.function.arguments or "{}"
                try:
                    function_args = json.loads(args_str)
                except json.JSONDecodeError:
                    function_args = {}
                
                # Executa a função correspondente
                if function_name == "adicionar_tarefa":
                    task_id = self.storage.add_task(
                        description=function_args.get("descricao", "Sem descrição"),
                        due_date=function_args.get("data_entrega", "Sem data")
                    )
                    function_response = f"Tarefa adicionada com sucesso! ID: {task_id}"
                
                elif function_name == "consultar_agenda":
                    data = function_args.get("data", "")
                    agenda = self.storage.get_agenda_by_date(data)
                    function_response = json.dumps(agenda, ensure_ascii=False)
                
                elif function_name == "listar_tarefas":
                    tarefas = self.storage.get_all_tasks()
                    function_response = json.dumps(tarefas, ensure_ascii=False)
                    
                elif function_name == "concluir_tarefa":
                    task_id = function_args.get("task_id")
                    if task_id and self.storage.complete_task(task_id):
                        function_response = f"Tarefa {task_id} concluída com sucesso!"
                    else:
                        function_response = f"Falha ao concluir tarefa {task_id}."
                
                elif function_name == "buscar_material_rag":
                    pergunta = function_args.get("pergunta", "")
                    resultados = self.rag_service.search(pergunta)
                    if resultados:
                        function_response = json.dumps(resultados, ensure_ascii=False)
                    else:
                        function_response = "Nenhuma informação relevante encontrada nos materiais anexados."
                
                else:
                    function_response = "Ferramenta desconhecida."
                
                # Adiciona o resultado da ferramenta ao histórico
                messages.append(
                    {
                        "tool_call_id": tool_call.id,
                        "role": "tool",
                        "name": function_name,
                        "content": function_response,
                    }
                )
            
            # Chama o LLM novamente com o resultado da ferramenta
            second_response = self.client.chat.completions.create(
                model=self.model,
                messages=messages
            )
            return second_response.choices[0].message.content

        return response_message.content
