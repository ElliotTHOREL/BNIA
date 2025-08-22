import os
import openai

from dotenv import load_dotenv
load_dotenv()

# Configuration globale
client = openai.AsyncOpenAI(
    api_key=os.getenv("OPENAI_API_KEY"),
    base_url=os.getenv("OPENAI_API_BASE")
)
Embedding_model = os.getenv("EMBEDDING_MODEL")
LLM_model = os.getenv("LLM_MODEL")


def check_config():
    """Vérifie que la configuration est correcte"""
    if not os.getenv("OPENAI_API_KEY"):
        raise ValueError("OPENAI_API_KEY non définie dans les variables d'environnement")
    return True