import os
import json
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

class JarvisLLM:
    def __init__(self, tool_registry):
        self.tool_registry = tool_registry
        self.client = OpenAI(
            base_url=os.getenv("OPENAI_BASE_URL"),
            api_key=os.getenv("OPENAI_API_KEY")
        )
        self.model = os.getenv("MODEL_NAME")

    def _build_system_prompt(self):
        tools = self.tool_registry.get_tools()
        if not tools:
            return "Você é o Jarvis, um assistente acadêmico autônomo."
            
        prompt = "Você é o Jarvis, um assistente acadêmico autônomo. Você tem acesso às seguintes ferramentas:\n\n"
        for t in tools:
            func = t.get("function", {})
            prompt += f"- Nome da ferramenta: {func.get('name')}\n"
            prompt += f"  Descrição: {func.get('description')}\n"
            prompt += f"  Parâmetros: {json.dumps(func.get('parameters', {}), ensure_ascii=False)}\n\n"
            
        prompt += """
IMPORTANTE: Se você precisar consultar a agenda, adicionar tarefas ou buscar material, você DEVE usar uma das ferramentas acima.
Para usar uma ferramenta, a sua resposta DEVE ser EXCLUSIVAMENTE um objeto JSON válido, sem nenhum texto antes ou depois, seguindo este exato formato:

```json
{
    "tool_call": "nome_da_ferramenta",
    "arguments": {
        "chave_do_parametro": "valor"
    }
}
```

Se você não precisar de nenhuma ferramenta (por exemplo, se já tiver a informação para responder ou for uma conversa casual), responda normalmente em linguagem natural.
"""
        return prompt

    def _parse_tool_call(self, text):
        if not text:
            return None
        try:
            cleaned = text.strip()
            if cleaned.startswith("```json"):
                cleaned = cleaned[7:-3].strip()
            elif cleaned.startswith("```"):
                cleaned = cleaned[3:-3].strip()
            
            data = json.loads(cleaned)
            if "tool_call" in data:
                return data
        except json.JSONDecodeError:
            pass
        return None

    def chat(self, messages):
        system_msg = {"role": "system", "content": self._build_system_prompt()}
        
        # Filtra mensagens antigas de sistema para não poluir
        filtered_messages = [m for m in messages if m.get("role") not in ["system", "tool_call_request", "tool_call_result"]]
        current_context = [system_msg] + filtered_messages
        
        response = self.client.chat.completions.create(
            model=self.model,
            messages=current_context
        )
        
        response_text = response.choices[0].message.content
        parsed_tool = self._parse_tool_call(response_text)
        
        if parsed_tool:
            func_name = parsed_tool.get("tool_call")
            func_args = parsed_tool.get("arguments", {})
            
            # Adiciona ao histórico do Streamlit para log visual
            messages.append({
                "role": "tool_call_request",
                "tool_name": func_name,
                "tool_args": json.dumps(func_args, ensure_ascii=False)
            })
            
            # Executa a função localmente
            function_response = self.tool_registry.execute(func_name, func_args)
            
            # Adiciona resultado ao histórico do Streamlit para log visual
            messages.append({
                "role": "tool_call_result",
                "content": str(function_response)
            })
            
            # Adiciona a requisição e a resposta ao contexto do LLM para a segunda chamada
            current_context.append({"role": "assistant", "content": response_text})
            current_context.append({
                "role": "user",
                "content": f"RESULTADO DA FERRAMENTA '{func_name}':\n{function_response}\n\nBaseado neste resultado, continue respondendo ao meu pedido original ou formule sua resposta final."
            })
            
            # Chama o LLM novamente com o resultado
            second_response = self.client.chat.completions.create(
                model=self.model,
                messages=current_context
            )
            return second_response.choices[0].message.content

        return response_text
