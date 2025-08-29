from transformers import pipeline, AutoTokenizer, AutoModelForSequenceClassification
import os

from dotenv import load_dotenv
load_dotenv()


def analyse_sentiment(textes: list[str], sentiment_analyzer):
    """
    Entrée : liste de textes et une pipeline de sentiment analysis
    Sortie : liste de scores (entre 1 et 5)
    """
    results = sentiment_analyzer(textes)
    return [
        sum(d["score"] * int(d["label"][0]) for d in result)
        for result in results
    ]

def analyse_sentiment_with_ai_manager(textes: list[str], ai_manager):
    """
    Entrée : liste de textes et AIManager
    Sortie : liste de scores (entre 1 et 5)
    """
    sentiment_analyzer = ai_manager.get_sentiment_analyzer()
    return analyse_sentiment(textes, sentiment_analyzer)

