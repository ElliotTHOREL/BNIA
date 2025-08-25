from app.database.read import check_clusterisation
from app.services.analyse_doc import create_clusterisation

from fastapi import APIRouter

router = APIRouter()

@router.post("/create_clusterisation")
async def create_clusterisation(liste_id_doc: list[int], liste_id_question: list[int], nb_clusters: int, distance: str):
    check = check_clusterisation(liste_id_doc, liste_id_question, nb_clusters, distance)
    if check is None:
        return create_clusterisation(liste_id_doc, liste_id_question, nb_clusters, distance)
    else:
        return {
            "status": "already_exists",
            "id_clusterisation": check,
            "id_questions": liste_id_question,
            "id_documents": liste_id_doc,
            "auto_number": nb_clusters is None,
            #"nb_clusters": len(rep_idees),
            #"nb_idees": len(ids),
            "distance": distance
        }