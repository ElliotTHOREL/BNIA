import os
import openai
from transformers import pipeline, AutoTokenizer, AutoModelForSequenceClassification

from dotenv import load_dotenv
load_dotenv()

# Configuration globale
def configu():
    client = openai.AsyncOpenAI(
        api_key=os.getenv("OPENAI_API_KEY"),
        base_url=os.getenv("OPENAI_API_BASE")
    )
    Embedding_model = os.getenv("EMBEDDING_MODEL")
    LLM_model = os.getenv("LLM_MODEL")

    sentiment_model_name = os.getenv("SENTIMENT_MODEL")
    sentiment_tokenizer = AutoTokenizer.from_pretrained(sentiment_model_name)
    sentiment_model = AutoModelForSequenceClassification.from_pretrained(sentiment_model_name)

    sentiment_analyzer = pipeline(
        "sentiment-analysis",
        model=sentiment_model,
        tokenizer=sentiment_tokenizer,
        device=-1,            # CPU
        framework="pt",
        top_k=None
    )

    return {"client": client, "Embedding_model": Embedding_model, "LLM_model": LLM_model, "sentiment_analyzer": sentiment_analyzer}


