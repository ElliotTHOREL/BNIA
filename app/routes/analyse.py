
from app.services.analyse_doc import find_clusterisation

from fastapi import APIRouter, Request
from pydantic import BaseModel
from typing import List


router = APIRouter()



class ClusterRequest(BaseModel):
    liste_id_doc: List[int]
    liste_id_question: List[int]
    questions_filtrees: List[int]
    filtres: List[List[int]]
    nb_clusters: int
    distance: str


@router.post("/create_clusterisation")
async def create_clusterisation_route(request: Request, req: ClusterRequest):
    ai_manager = request.app.state.aimanager
    return await find_clusterisation(
        req.liste_id_doc,
        req.liste_id_question,
        req.questions_filtrees,
        req.filtres,
        req.nb_clusters,
        req.distance,
        ai_manager
    )