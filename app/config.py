import os
import openai
from transformers import pipeline, AutoTokenizer, AutoModelForSequenceClassification
import logging
import asyncio

from dotenv import load_dotenv
load_dotenv()



class AIManager:
    def __init__(self):
        self.olympia_client = None
        self.albert_client = None
        self.sentiment_analyzer = None
        self.albert_model_for_llm = os.getenv("ALBERT_LLM_MODEL")
        self.olympia_model_for_llm = os.getenv("OLYMPIA_LLM_MODEL")
        self.olympia_model_for_embedding = os.getenv("OLYMPIA_EMBEDDING_MODEL")
        self.sentiment_model = os.getenv("SENTIMENT_MODEL")

        self._client_lock = asyncio.Lock()
    
    async def get_olympia_client(self):
        async with self._client_lock:
            if self.olympia_client is None:
                self.olympia_client = openai.AsyncOpenAI(
                    api_key=os.getenv("OLYMPIA_API_KEY"),
                    base_url=os.getenv("OLYMPIA_API_BASE")
                )
            return self.olympia_client

    async def get_albert_client(self):
        async with self._client_lock:
            if self.albert_client is None:
                self.albert_client = openai.AsyncOpenAI(
                    api_key=os.getenv("ALBERT_API_KEY"),
                    base_url=os.getenv("ALBERT_API_BASE"),
                    max_retries=0
                )
            return self.albert_client

    def get_sentiment_analyzer(self):
        if self.sentiment_analyzer is None:
            sentiment_tokenizer = AutoTokenizer.from_pretrained(self.sentiment_model)
            sentiment_model = AutoModelForSequenceClassification.from_pretrained(self.sentiment_model)
            self.sentiment_analyzer = pipeline(
                "sentiment-analysis",
                model=sentiment_model,
                tokenizer=sentiment_tokenizer,
                device=-1,            # CPU
                framework="pt",
                top_k=None
            )
        return self.sentiment_analyzer

    async def LLM_treatment(self, messages):
        
        try:
            client = await self.get_albert_client()
            response = await client.chat.completions.create(
                model=self.albert_model_for_llm,
                messages=messages
            )
            return response.choices[0].message.content
        except Exception as e:
            if "Error code: 429" not in str(e):
                logging.warning(f"Echec de l'utilisation d'ALBERT: {e}")
            client = await self.get_olympia_client()
            response = await client.chat.completions.create(
                model=self.olympia_model_for_llm,
                messages=messages
            )
            return response.choices[0].message.content
    
    async def embedding(self, ma_liste: list[str]):
        client = await self.get_olympia_client()
        response = await client.embeddings.create(
            model=self.olympia_model_for_embedding,
            input=ma_liste   
        )
        return response

    def sentiment_analysis(self, textes: list[str]):
        sentiment_analyzer = self.get_sentiment_analyzer()
        return sentiment_analyzer(textes)



