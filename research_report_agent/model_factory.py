import os
from smolagents import LiteLLMModel

def create_model():
    """Cria o modelo usando a API gratuita do Google Gemini."""
    
    api_key = os.getenv("GOOGLE_API_KEY")
    
    # Recomendação: use o modelo Flash para maior velocidade e bom custo-benefício.
    return LiteLLMModel(
        model_id="gemini/gemini-3.1-flash-lite",
        api_key=api_key,
        temperature=0.0,  # Menos criativo para respostas precisas do GAIA
        max_tokens=4096,
    )
    
    
# OLLAMA 
# import os
# from smolagents import LiteLLMModel

# def create_model():
#     """Cria o modelo usando Ollama local."""
    
#     model_id = os.getenv("OLLAMA_MODEL", "ollama/qwen2.5-coder:7b")
#     api_base = os.getenv("OLLAMA_API_BASE", "http://localhost:11434")
    
#     return LiteLLMModel(
#         model_id=model_id,
#         api_base=api_base,
#         temperature=0.0,
#         max_tokens=1000,
#     )
    
