from app.database.read import get_exigence, get_filtration, get_scores, get_clusterisation, get_clusters
from app.database.update import create_exigence, create_filtration, create_clusterisation

import logging
import time

       

async def find_clusterisation(liste_id_doc, liste_id_question, questions_filtrees, filtres, nb_clusters, distance, ai_manager):
    if nb_clusters == 0:
        nb_clusters = None

    drapeau_1=True
    drapeau_2=True

    nb_filtres = len(questions_filtrees)
    liste_id_exigences=[]
    for i in range(nb_filtres):
        id_exigence = get_exigence(questions_filtrees[i], filtres[i])
        if id_exigence is None:
            id_exigence = create_exigence(questions_filtrees[i], filtres[i])
            drapeau_1 = False
        liste_id_exigences.append(id_exigence)

    if drapeau_1: # Si on vient de créer une exigence, ce n'est pas le peine de chercher une filtration qui la contient
        id_filtration = get_filtration(liste_id_doc, liste_id_exigences)
    if not drapeau_1 or id_filtration is None:
        logging.info("Création de la filtration")
        id_filtration = create_filtration(liste_id_doc,liste_id_exigences)
        drapeau_2 = False

    if drapeau_2:# Si on vient de créer la filtration, ce n'est pas le peine de chercher la clusterisation
        id_clusterisation = get_clusterisation(liste_id_question, id_filtration, nb_clusters, distance)
    if not drapeau_2 or id_clusterisation is None:
        logging.info("Création de la clusterisation")
        id_clusterisation = await create_clusterisation(liste_id_question, id_filtration, ai_manager, nb_clusters, distance)
    
    if id_clusterisation == -1:
        return {
            "status": "failure pas assez d'idées",
            "scores": [],
            "id_clusterisation": None,
            "clusters": [],
        }

    else:
        scores = get_scores(liste_id_question, id_filtration)
        clusters = get_clusters(id_clusterisation)
        return {
            "status": "success",
            "scores": scores,
            "id_clusterisation": id_clusterisation,
            "clusters": clusters,
        }
    