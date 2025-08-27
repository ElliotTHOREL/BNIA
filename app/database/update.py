from app.connection import get_db_cursor
from app.domain.embed import embed_answers
from app.domain.analyse_sentiment import analyse_sentiment

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
                    new_texts.append((reponse,))
                    existing_texts.append(reponse)
                response_data.append((id_question, id_repondant, reponse))

        # Insérer les nouveaux textes
        if new_texts:
            cursor.executemany(
                "INSERT INTO texte_reponse (texte) VALUES (%s)",
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

async def embed_all_answers(client, modele_embedding, modele_llm):
    with get_db_cursor() as cursor:
        cursor.execute("""SELECT id, texte 
                            FROM texte_reponse 
                            WHERE traite = FALSE""")
        liste_tuples = cursor.fetchall()
        liste_ids_answers = [tuple[0] for tuple in liste_tuples]
        liste_answers = [tuple[1] for tuple in liste_tuples]

        liste_results = await embed_answers(liste_answers, client, modele_embedding, modele_llm)
        #Une liste de triplets (indice_reponse, texte, embed)

        for indice_reponse, texte, embed in liste_results:
            data = (
                liste_ids_answers[indice_reponse],
                texte,
                json.dumps(embed.tolist())
            )
            cursor.execute(
                """INSERT INTO idee_embedded (id_reponse, idee_texte, idee_embed)
                VALUES (%s, %s, %s)""",
                data
            )

        cursor.execute("""UPDATE texte_reponse SET traite = TRUE""")

    return {"status": "embeded", "number_results": len(liste_results)}

def analyse_sentiment_all_ideas(sentiment_analyzer):

    with get_db_cursor() as cursor:
        cursor.execute("""SELECT id, idee_texte 
            FROM idee_embedded 
            WHERE score IS NULL""")
        liste_tuples = cursor.fetchall()
        liste_ids_ideas = [tuple[0] for tuple in liste_tuples]
        liste_texte_ideas = [tuple[1] for tuple in liste_tuples]

        scores = analyse_sentiment(liste_texte_ideas, sentiment_analyzer)

        data_to_insert = list(zip(scores, liste_ids_ideas))
        cursor.executemany(
            """UPDATE idee_embedded SET score = %s WHERE id = %s""",
            data_to_insert
        )
    return {"status": "analyse_sentiment_done", "number_analyses": len(liste_ids_ideas)}