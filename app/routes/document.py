from app.database.read import get_all_documents, get_all_questions, get_all_idees_in_cluster, get_possible_answers, get_details_idee
from app.database.update import import_excel_to_bdd, rename_document, embed_all_answers, analyse_sentiment_all_ideas, rescorer_idee, switch_type_question, merge_questions, de_masquer_cluster
from app.database.delete import  delete_one_document, reset_all, delete_one_question, reset_all_clusterisation

from fastapi import APIRouter, UploadFile, File, Request, Body


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

@router.get("/possible_answers")
async def get_possible_answers_route(id_question: int):
    return get_possible_answers(id_question)

@router.get("/get_details_idee")
async def get_details_idee_route(id_idee: int, id_clusterisation: int):
    return get_details_idee(id_idee, id_clusterisation)

@router.post("/rescorer_idee")
async def rescorer_idee_route(id_idee: int, idee_score: float):
    return rescorer_idee(id_idee, idee_score)

@router.post("/rename_doc")
async def rename_doc(id: int, new_name: str):
    return rename_document(id, new_name)

@router.post("/switch_question_type")
async def switch_question_type_route(id_question: int):
    return switch_type_question(id_question)

@router.post("/merge_questions")
async def merge_questions_route(data: dict = Body(...)):
    liste_id_questions = data.get("liste_id_questions")
    new_question = data.get("new_question")
    return merge_questions(liste_id_questions, new_question)

@router.post("/de_masquer_cluster")
async def de_masquer_cluster_route(id_cluster: int):
    return de_masquer_cluster(id_cluster)


@router.post("/import_excel")
async def import_excel(file: UploadFile = File(...)):
    return await import_excel_to_bdd(file)


@router.post("/extraire_idees")
async def extraire_idees(request: Request):
    ai_manager = request.app.state.aimanager
    return await embed_all_answers(ai_manager)

@router.post("/analyse_sentiment")
async def analyse_sentiment(request:Request):
    ai_manager = request.app.state.aimanager
    return analyse_sentiment_all_ideas(ai_manager)


@router.post("/import_excel_complete")
async def import_excel_complete(request: Request, file: UploadFile = File(...)):
    ai_manager = request.app.state.aimanager
    await import_excel_to_bdd(file)
    await embed_all_answers(ai_manager)
    analyse_sentiment_all_ideas(ai_manager)
    return {"status": "imported", "name": file.filename}




@router.delete("/delete_one_document")
async def delete_document(id_document: int):
    return delete_one_document(id_document)

@router.delete("/delete_one_question")
async def delete_question_route(id_question: int):
    return delete_one_question(id_question)

@router.delete("/reset_clusterisation")
async def reset_clusterisation_route():
    return reset_all_clusterisation()


@router.delete("/reset_all")
async def reset_all_route():
    return reset_all()
