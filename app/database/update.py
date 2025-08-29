from app.connection import get_db_cursor
from app.domain.embed import embed_answers_with_ai_manager
from app.domain.analyse_sentiment import analyse_sentiment, analyse_sentiment_with_ai_manager
from app.database.delete import delete_one_question
from app.database.read import get_all_idees
from app.domain.clusterisation import clusterisation, find_representative_idea_with_ai_manager
from app.domain.tools.text_processor import get_or_create_texte_traite

import pandas as pd
from io import BytesIO
from fastapi import UploadFile, File
import json


async def import_excel_to_bdd(file: UploadFile = File(...)):
    name = file.filename

    with get_db_cursor() as cursor:
        cursor.execute("""SELECT COUNT(*) FROM document WHERE name = %s""", (name,))
        if cursor.fetchone()[0] > 0:
            return {"status": "already_exists", "name": name}

    content = await file.read()
    df = pd.read_excel(BytesIO(content))


    with get_db_cursor() as cursor:
        cursor.execute("""INSERT INTO document
        (name) VALUES (%s)""", 
        (name,))
        id_document = cursor.lastrowid

    # Création des questions
        questions = list(df.columns[:])
        question_ids = {}
        for id_ds_doc, q in enumerate(questions):
            cursor.execute("""INSERT INTO question
                (question, type) VALUES (%s, %s)
                ON DUPLICATE KEY UPDATE id=LAST_INSERT_ID(id)""",
                (q, "opinion"))
            id_question = cursor.lastrowid

            question_ids[id_ds_doc] = id_question


        repondant_data = [(id_document, index) for index in df.index]

        cursor.executemany("""INSERT INTO repondant
            (id_document, num_ds_document) VALUES (%s, %s)""",
            repondant_data)

        cursor.execute("""
        SELECT id, num_ds_document FROM repondant WHERE id_document = %s
        """, (id_document,))
        repondants_dict = {row[1]: row[0] for row in cursor.fetchall()}


        # Récupérer les textes existants
        cursor.execute("SELECT texte FROM texte_reponse")
        existing_texts = [row[0] for row in cursor.fetchall()]

        new_texts = []
        response_data = []

        # Parcourir le DataFrame
        for index, row in df.iterrows():
            id_repondant = repondants_dict[index]
            for id_ds_doc, id_question in question_ids.items():
                val = row.iloc[id_ds_doc]
                reponse = str(val)
                if pd.isna(val):
                    continue
                if reponse not in existing_texts:
                    # Créer le texte traité correspondant
                    id_texte_traite = get_or_create_texte_traite(reponse, cursor)
                    new_texts.append((id_texte_traite, reponse))
                    existing_texts.append(reponse)
                response_data.append((id_question, id_repondant, reponse))

        # Insérer les nouveaux textes
        if new_texts:
            cursor.executemany(
                "INSERT INTO texte_reponse (id_texte_traite, texte) VALUES (%s, %s)",
                new_texts
            )

        # Récupérer les IDs des textes
        cursor.execute("SELECT id, texte FROM texte_reponse")
        texte_to_id = {row[1]: row[0] for row in cursor.fetchall()}

        # Préparer les données finales pour insertion dans reponse
        final_response_data = [
            (id_question, id_repondant, texte_to_id[texte])
            for id_question, id_repondant, texte in response_data
        ]

        # Insérer les réponses
        cursor.executemany(
            "INSERT INTO reponse (id_question, id_repondant, id_texte_reponse) VALUES (%s, %s, %s)",
            final_response_data
        )

    return {"status": "imported", "name": name, "rows": len(df)}

def switch_type_question(id_question: int):
    with get_db_cursor() as cursor:
        cursor.execute("""SELECT type FROM question 
            WHERE id = %s""",
            (id_question,))
        typ = cursor.fetchone()[0]
    
    if typ == "opinion":
        new_type = "identification"
    elif typ == "identification":
        new_type = "opinion"

    with get_db_cursor() as cursor:
        cursor.execute("""UPDATE question SET type = %s WHERE id = %s""",
            (new_type, id_question))

def rename_document(id_document: int, new_name: str):
    with get_db_cursor() as cursor:
        cursor.execute("""UPDATE document SET name = %s WHERE id = %s""",
            (new_name, id_document))

def merge_questions(liste_id_questions: list[int], new_question: str):
    with get_db_cursor() as cursor:
        placeholders = ','.join(['%s'] * len(liste_id_questions))

        cursor.execute(
            f"SELECT DISTINCT type FROM question WHERE id IN ({placeholders})",
            (*liste_id_questions,) 
        )
        types = [row[0] for row in cursor.fetchall()]
        if "opinion" in types :
            new_type = "opinion"
        else:
            new_type = "identification"

        cursor.execute("""INSERT INTO question (question, type) 
            VALUES (%s, %s)""",
            (new_question, new_type)
            )
        id_question = cursor.lastrowid
        

        cursor.execute(
            f"UPDATE reponse SET id_question = %s WHERE id_question IN ({placeholders})",
            (id_question, *liste_id_questions)
        )
        
    for id_question in liste_id_questions:
        delete_one_question(id_question)

def rescorer_idee(id_idee: int, idee_score: float):
    with get_db_cursor() as cursor:
        cursor.execute("""UPDATE idee_embedded SET score = %s WHERE id = %s""",
            (idee_score, id_idee))
        cursor.execute("""SELECT id_cluster 
            FROM jointure_cluster_idees 
            WHERE id_idee = %s""",
            (id_idee,))
        id_clusters = [row[0] for row in cursor.fetchall()]

        
        for id_cluster in id_clusters:
            cursor.execute("""SELECT jci.occurrences, ie.score
                FROM cluster as c
                JOIN jointure_cluster_idees as jci ON c.id = jci.id_cluster
                Join idee_embedded as ie ON jci.id_idee = ie.id
                WHERE c.id = %s""",
                (id_cluster,))
            res = cursor.fetchall()
            total_occ = sum(row[0] for row in res)
            if total_occ == 0:
                new_score = 0
            else:
                new_score = sum(row[0] * row[1] for row in res) / total_occ
            cursor.execute("""UPDATE cluster SET score = %s WHERE id = %s""",
                (new_score, id_cluster)
            )

async def embed_all_answers(ai_manager):
    with get_db_cursor() as cursor:
        # Récupérer les textes qui n'ont pas encore d'idées embeddées
        cursor.execute("""
            SELECT DISTINCT tr.id, tr.texte 
            FROM texte_reponse tr
            LEFT JOIN jointure_idee_texte jit ON tr.id_texte_traite = jit.id_texte_traite
            WHERE jit.id_texte_traite IS NULL
        """)
        liste_tuples = cursor.fetchall()
        liste_ids_answers = [tuple[0] for tuple in liste_tuples]
        liste_answers = [tuple[1] for tuple in liste_tuples]

        liste_results = await embed_answers_with_ai_manager(liste_answers, ai_manager)
        #Une liste de triplets (indice_reponse, texte, embed)

        for indice_reponse, texte, embed in liste_results:
            # Insérer l'idée embeddée
            cursor.execute(
                """INSERT INTO idee_embedded (idee_texte, idee_embedded)
                VALUES (%s, %s)""",
                (texte, json.dumps(embed.tolist()))
            )
            id_idee = cursor.lastrowid
            
            # Créer la jointure avec le texte traité
            id_texte_traite = get_or_create_texte_traite(texte, cursor)
            cursor.execute(
                """INSERT INTO jointure_idee_texte (id_texte_traite, id_idee)
                VALUES (%s, %s)""",
                (id_texte_traite, id_idee)
            )

    return {"status": "embeded", "number_results": len(liste_results)}

def analyse_sentiment_all_ideas(ai_manager):


    with get_db_cursor() as cursor:
        cursor.execute("""SELECT id, idee_texte 
            FROM idee_embedded 
            WHERE score IS NULL""")
        liste_tuples = cursor.fetchall()
        liste_ids_ideas = [tuple[0] for tuple in liste_tuples]
        liste_texte_ideas = [tuple[1] for tuple in liste_tuples]

        scores = analyse_sentiment_with_ai_manager(liste_texte_ideas, ai_manager)

        data_to_insert = list(zip(scores, liste_ids_ideas))
        cursor.executemany(
            """UPDATE idee_embedded SET score = %s WHERE id = %s""",
            data_to_insert
        )
    return {"status": "analyse_sentiment_done", "number_analyses": len(liste_ids_ideas)}


def create_exigence(id_question: int, liste_id_answer: list[int]):
    with get_db_cursor() as cursor:
        
        cursor.execute("""INSERT 
                INTO exigence (id_question) 
                VALUES (%s)""", 
                (id_question,)
            )
        id_exigence = cursor.lastrowid

        data_to_insert = [
            (id_exigence, id_answer)
            for id_answer in liste_id_answer
        ]
        cursor.executemany(
            """INSERT INTO jointure_exigence_reponse (id_exigence, id_reponse) VALUES (%s, %s)""",
            data_to_insert)
        return id_exigence
        
def create_filtration(liste_id_document: list[int], liste_id_exigence: list[int]):
    with get_db_cursor() as cursor:
        cursor.execute("""INSERT INTO filtration VALUES ()""")
        id_filtration = cursor.lastrowid

        data_to_insert = [
            (id_filtration, id_exigence)
            for id_exigence in liste_id_exigence
        ]
        cursor.executemany(
            """INSERT INTO jointure_filtration_exigence (id_filtration, id_exigence) VALUES (%s, %s)""",
            data_to_insert
        )

        data_to_insert_2 = [
            (id_filtration, id_document)
            for id_document in liste_id_document
        ]
        cursor.executemany(
            """INSERT INTO jointure_filtration_document (id_filtration, id_document) VALUES (%s, %s)""",
            data_to_insert_2
        )

        return id_filtration




async def create_clusterisation(liste_id_question, id_filtration, ai_manager, nb_clusters=None, distance="cosine"):
    liste_idees=get_all_idees(liste_id_question, id_filtration)


    #On vérifie qu'il y a assez d'idées pour clusteriser
    if nb_clusters is None:
        seuil =20
    else:
        seuil = nb_clusters
    if len(liste_idees) < seuil:
        return -1


    ids, _, _, _,  = zip(*liste_idees)

    labels, centroids = clusterisation(liste_idees,n_clusters=nb_clusters, distance=distance)
    rep_idees = await find_representative_idea_with_ai_manager(liste_idees, labels, ai_manager)

    with get_db_cursor() as cursor:
        cursor.execute("""INSERT INTO clusterisation (auto_number, nb_clusters, distance, id_filtration)
            VALUES (%s, %s, %s, %s)
            """, (nb_clusters is None, len(rep_idees), distance, id_filtration))
        id_clusterisation = cursor.lastrowid
        

        for question in liste_id_question:
            cursor.execute("""
            INSERT INTO jointure_clusterisation_question (id_clusterisation, id_question)
            VALUES (%s, %s)
            """, (id_clusterisation, question))

        dico_num_cluster = {}
        for (num_cluster, (texte,taille,score)) in enumerate(rep_idees):
            cursor.execute("""
            INSERT INTO cluster (id_clusterisation, texte, taille, score)
            VALUES (%s, %s, %s, %s)
            """, (id_clusterisation, texte, taille, score))
            id_cluster = cursor.lastrowid
            dico_num_cluster[num_cluster] = id_cluster

        dico_idee_cluster = {}
        def ajouter_idee_cluster(id_idee, num_cluster):
            if id_idee not in dico_idee_cluster:
                dico_idee_cluster[id_idee] = {num_cluster: 1}
            elif num_cluster not in dico_idee_cluster[id_idee]:
                dico_idee_cluster[id_idee][num_cluster] = 1
            else:
                dico_idee_cluster[id_idee][num_cluster] += 1

        for i, id_idee in enumerate(ids):
            if labels[i] != -1:
                ajouter_idee_cluster(id_idee, dico_num_cluster[labels[i]])

        data = []
        for id_idee, dico_cluster in dico_idee_cluster.items():
            for num_cluster, occurrences in dico_cluster.items():
                data.append((num_cluster, id_idee, occurrences))

        cursor.executemany("""
            INSERT INTO jointure_cluster_idees (id_cluster, id_idee, occurrences)
            VALUES (%s, %s, %s)
        """, data)

    return id_clusterisation