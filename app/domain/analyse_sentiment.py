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

if __name__ == "__main__":
    model_name = os.getenv("SENTIMENT_MODEL")
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    model = AutoModelForSequenceClassification.from_pretrained(model_name)

    sentiment_analyzer = pipeline(
        "sentiment-analysis",
        model=model,
        tokenizer=tokenizer,
        device=-1,            # CPU
        framework="pt",
        top_k=None
    )
    print(analyse_sentiment(["peut mieux faire"],sentiment_analyzer))