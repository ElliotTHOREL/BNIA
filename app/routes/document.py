from app.database.read import get_all_documents, get_all_questions, get_all_idees_in_cluster
from app.database.update import import_excel_to_bdd, rename_document, embed_all_answers, analyse_sentiment_all_ideas, rescorer_idee
from app.database.delete import  delete_one_document, reset_all

from fastapi import APIRouter, UploadFile, File, Request


router = APIRouter()

@router.get("/documents")
async def get_documents():
    return get_all_documents()

@router.get("/questions")
async def get_questions():
    return get_all_questions()

@router.get("/idees_in_cluster")
async def get_idees_in_cluster(id_cluster: int):
    return get_all_idees_in_cluster(id_cluster)

@router.post("/rescorer_idee")
async def rescorer_idee_route(id_idee: int, idee_score: float):
    return rescorer_idee(id_idee, idee_score)

@router.post("/rename_doc")
async def rename_doc(id: int, new_name: str):
    return rename_document(id, new_name)

@router.post("/import_excel")
async def import_excel(file: UploadFile = File(...)):
    return await import_excel_to_bdd(file)


@router.post("/extraire_idees")
async def extraire_idees(request: Request):
    client = request.app.state.client
    modele_embedding = request.app.state.Embedding_model
    modele_llm = request.app.state.LLM_model
    return await embed_all_answers(client, modele_embedding, modele_llm)

@router.post("/analyse_sentiment")
async def analyse_sentiment(request:Request):
    sentiment_analyzer = request.app.state.sentiment_analyzer
    return analyse_sentiment_all_ideas(sentiment_analyzer)


@router.post("/import_excel_complete")
async def import_excel_complete(request: Request, file: UploadFile = File(...)):
    client = request.app.state.client
    modele_embedding = request.app.state.Embedding_model
    modele_llm = request.app.state.LLM_model
    sentiment_analyzer = request.app.state.sentiment_analyzer
    await import_excel_to_bdd(file)
    await embed_all_answers(client, modele_embedding, modele_llm)
    analyse_sentiment_all_ideas(sentiment_analyzer)
    return {"status": "imported", "name": file.filename}

@router.delete("/delete_one_document")
async def delete_document(id_document: int):
    return delete_one_document(id_document)


@router.delete("/reset_all")
async def reset_all_route():
    return reset_all()
