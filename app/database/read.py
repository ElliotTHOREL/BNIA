from app.connection import get_db_cursor

import numpy as np
import json

def get_all_idees(id_document: int, id_question: int):
    with get_db_cursor() as cursor:
        cursor.execute("""
            SELECT 
                idee_embedded.id,
                idee_embedded.idee_texte, 
                idee_embedded.idee_embed, 
                idee_embedded.score 
            FROM reponse
            JOIN texte_reponse ON reponse.id_texte_reponse = texte_reponse.id
            JOIN repondant ON reponse.id_repondant = repondant.id
            JOIN idee_embedded ON idee_embedded.id_reponse = texte_reponse.id
            WHERE repondant.id_document = %s 
              AND reponse.id_question = %s
        """, (id_document, id_question))
        rows = cursor.fetchall()
    
    # Conversion en numpy.ndarray pour le champ idee_embed
    return [
        (
            row[0],                # id
            row[1],                # idee_texte
            np.array(json.loads(row[2])),  # idee_embed
            row[3]                 # score
        )
        for row in rows
    ]

def get_all_idees_in_cluster(id_cluster: int):
    with get_db_cursor() as cursor:
        cursor.execute("""
            SELECT idee_embedded.id, idee_embedded.idee_texte,  idee_embedded.score, jci.occurrences
            FROM jointure_cluster_idees as jci
            JOIN idee_embedded ON jci.id_idee = idee_embedded.id
            WHERE jci.id_cluster = %s
            ORDER BY jci.occurrences DESC
        """, (id_cluster,))
        return cursor.fetchall()



def get_scores(liste_id_document: list[int], liste_id_question: list[int]):
        # Génération dynamique des placeholders
    placeholders_docs = ','.join(['%s'] * len(liste_id_document))
    placeholders_ques = ','.join(['%s'] * len(liste_id_question))

    query = f"""
        SELECT AVG(i.score) AS score_moyen
        FROM reponse r
        JOIN idee_embedded i ON r.id_texte_reponse = i.id_reponse
        JOIN repondant ON r.id_repondant = repondant.id
        WHERE repondant.id_document IN ({placeholders_docs})
        AND r.id_question IN ({placeholders_ques})
        GROUP BY r.id
        ORDER BY score_moyen ASC
    """
    params = liste_id_document + liste_id_question
    with get_db_cursor() as cursor:
        cursor.execute(query, params)
        return [result[0] for result in cursor.fetchall()]

def get_all_documents():
    with get_db_cursor() as cursor:
        cursor.execute("""SELECT id, name FROM document""")
        return cursor.fetchall()

def get_all_questions():
    with get_db_cursor() as cursor:
        cursor.execute("""SELECT id, question, type FROM question""")
        return cursor.fetchall()

def get_clusterisation(liste_id_doc, liste_id_question, nb_clusters, distance):
    with get_db_cursor() as cursor:
        format_docs = ','.join(['%s'] * len(liste_id_doc)) if liste_id_doc else 'NULL'
        format_questions = ','.join(['%s'] * len(liste_id_question)) if liste_id_question else 'NULL'

        where_clauses = ["c.distance = %s"]
        params = [distance]

        # auto_number
        if nb_clusters is None:
            where_clauses.append("c.auto_number = TRUE")
        else:
            where_clauses.append("c.auto_number = FALSE")
            where_clauses.append("c.nb_clusters = %s")
            params.append(nb_clusters)

        # documents et questions restent dans HAVING
        having_clauses = []
        if liste_id_doc:
            having_clauses.append(f"SUM(jcd.id_document NOT IN ({format_docs})) = 0")
            params.extend(liste_id_doc)
        if liste_id_question:
            having_clauses.append(f"SUM(jcq.id_question NOT IN ({format_questions})) = 0")
            params.extend(liste_id_question)

        where_clause = " AND ".join(where_clauses)
        having_clause = " AND ".join(having_clauses)

        query = f"""
        SELECT c.id
        FROM clusterisation c
        JOIN jointure_clusterisation_document jcd ON jcd.id_clusterisation = c.id
        JOIN jointure_clusterisation_question jcq ON jcq.id_clusterisation = c.id
        WHERE {where_clause}
        GROUP BY c.id
        HAVING {having_clause}
        """

        cursor.execute(query, params)
        result = cursor.fetchone()
        if result is None:
            return None
        else:
            id_clusterisation = result[0]
            return id_clusterisation

def get_clusters(id_clusterisation: int):
    with get_db_cursor() as cursor:
        cursor.execute("""
            SELECT id, texte, taille, score
            FROM cluster
            WHERE id_clusterisation = %s
        """, (id_clusterisation,))
        return cursor.fetchall()