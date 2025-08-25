from app.database.read import get_all_documents
from app.database.update import import_excel_to_bdd, embed_all_answers, analyse_sentiment_all_ideas
from app.database.delete import reset_all

from fastapi import APIRouter, UploadFile, File, Request




router = APIRouter()



@router.get("/documents")
async def get_documents():
    return get_all_documents()

@router.post("/import_excel")
async def import_excel(file: UploadFile = File(...)):
    return import_excel_to_bdd(file)

@router.post("/extraire_idees")
async def extraire_idees(request: Request):
    client = request.app.state["client"]
    modele_embedding = request.app.state["Embedding_model"]
    modele_llm = request.app.state["LLM_model"]
    return embed_all_answers(client, modele_embedding, modele_llm)

@router.post("/analyse_sentiment")
async def analyse_sentiment(request:Request):
    sentiment_analyzer = request.app.state["sentiment_analyzer"]
    return analyse_sentiment_all_ideas(sentiment_analyzer)

@router.delete("/reset_all")
async def reset_all():
    return reset_all()
