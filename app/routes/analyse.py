from app.database.read import get_clusterisation, get_scores, get_clusters
from app.services.analyse_doc import create_clusterisation

from fastapi import APIRouter

router = APIRouter()

@router.post("/create_clusterisation")
async def create_clusterisation_route(liste_id_doc: list[int], liste_id_question: list[int], nb_clusters: int, distance: str):
    if nb_clusters == 0:
        nb_clusters = None

    scores = get_scores(liste_id_doc, liste_id_question)

    id_clusterisation = get_clusterisation(liste_id_doc, liste_id_question, nb_clusters, distance)
    if id_clusterisation is None:
        id_clusterisation = create_clusterisation(liste_id_doc, liste_id_question, nb_clusters, distance)
    
    clusters = get_clusters(id_clusterisation)

    return {
        "status": "success",
        "scores": scores,
        "id_clusterisation": id_clusterisation,
        "clusters": clusters,
    }