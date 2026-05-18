import os
import json
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

class JarvisLLM:
    def __init__(self, storage):
        self.storage = storage
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
                            "descricao": {
                                "type": "string",
                                "description": "A descrição da tarefa a ser feita."
                            },
                            "data_entrega": {
                                "type": "string",
                                "description": "A data de entrega da tarefa no formato YYYY-MM-DD."
                            }
                        },
                        "required": ["descricao", "data_entrega"]
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
                function_args = json.loads(tool_call.function.arguments)
                
                # Executa a função correspondente
                if function_name == "adicionar_tarefa":
                    task_id = self.storage.add_task(
                        description=function_args.get("descricao"),
                        due_date=function_args.get("data_entrega")
                    )
                    function_response = f"Tarefa adicionada com sucesso! ID: {task_id}"
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
