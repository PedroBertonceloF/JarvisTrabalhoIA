class ToolRegistry:
    def __init__(self):
        self._tools = {}
        self._schemas = []

    def register(self, schema: dict, func: callable):
        """
        Registra uma ferramenta.
        O schema no formato da OpenAI deve conter 'function' e dentro dele o 'name'.
        """
        # A API da OpenAI espera o schema envelopado: {"type": "function", "function": {"name": ...}}
        # Vamos extrair o nome de dentro de "function", ou dar fallback para a raiz se vier diferente.
        function_def = schema.get("function", schema)
        tool_name = function_def.get("name")
        
        if not tool_name:
            raise ValueError("O schema da ferramenta deve conter a chave 'name' (diretamente ou dentro de 'function').")
        
        # Guardamos a função para execução
        self._tools[tool_name] = func
        
        # Guardamos o schema completo no formato esperado pela OpenAI
        self._schemas.append(schema)

    def get_tools(self) -> list:
        """
        Retorna a lista de schemas registrados.
        """
        return self._schemas

    def execute(self, tool_name: str, arguments: dict):
        """
        Executa a função correspondente à ferramenta, capturando erros.
        """
        func = self._tools.get(tool_name)
        if not func:
            return "Ferramenta desconhecida."
        
        try:
            # Desempacota os argumentos do JSON como kwargs para a função
            return func(**arguments)
        except Exception as e:
            return f"Erro na execução da ferramenta: {str(e)}"
