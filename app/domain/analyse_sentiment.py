from transformers import pipeline
import os

from dotenv import load_dotenv
load_dotenv()


def analyse_sentiment(text: str, sentiment_analyzer):
    result = sentiment_analyzer(text)
    return result

if __name__ == "__main__":
    model = os.getenv("SENTIMENT_MODEL")
    sentiment_analyzer = pipeline("sentiment-analysis", model=model, tokenizer=model)
    print(analyse_sentiment("Je suis content",sentiment_analyzer))