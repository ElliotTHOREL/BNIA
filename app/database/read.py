from app.connection import get_db_cursor

import numpy as np
import json

def get_all_idees(liste_id_question: list[int], id_filtration: int):
    with get_db_cursor() as cursor:
        
        format_questions = ','.join(['%s'] * len(liste_id_question))

        params=[]
        params.extend(liste_id_question)
        

        cursor.execute(f"""SELECT COUNT(*) 
            FROM jointure_filtration_exigence 
            WHERE id_filtration = %s""",
             (id_filtration,)
             )
        nb_exigence = cursor.fetchone()[0]

        if nb_exigence > 0:
            params.extend([id_filtration, nb_exigence])    
            cursor.execute(f"""
                SELECT 
                    i.id,
                    i.idee_texte, 
                    i.idee_embedded, 
                    i.score

                FROM idee_embedded AS i
                JOIN jointure_idee_texte jit ON i.id = jit.id_idee
                JOIN texte_traite tt ON jit.id_texte_traite = tt.id
                JOIN texte_reponse AS tr ON tt.id = tr.id_texte_traite
                JOIN reponse AS r ON tr.id = r.id_texte_reponse
                JOIN repondant AS rd ON r.id_repondant = rd.id
                JOIN document AS d ON rd.id_document = d.id
                JOIN jointure_filtration_document AS jfd ON d.id = jfd.id_document


                LEFT JOIN jointure_filtration_exigence jfe ON jfe.id_filtration = jfd.id_filtration
                LEFT JOIN exigence e ON e.id = jfe.id_exigence
                LEFT JOIN jointure_exigence_reponse jer ON jer.id_exigence = e.id


                JOIN reponse AS r2 
                    ON r2.id_repondant = rd.id 
                    AND r2.id_texte_reponse = jer.id_reponse 
                    AND r2.id_question = e.id_question

                WHERE r.id_question IN ({format_questions}) AND jfd.id_filtration = %s
                GROUP BY rd.id,
                    i.id,
                    i.idee_texte, 
                    i.idee_embedded, 
                    i.score
                HAVING 
                    (COUNT(DISTINCT e.id) = %s)
            """, tuple(params))
        else:
            params.extend([id_filtration]) 
            cursor.execute(f"""
                SELECT 
                    i.id,
                    i.idee_texte, 
                    i.idee_embedded, 
                    i.score
                FROM idee_embedded AS i
                JOIN jointure_idee_texte jit ON i.id = jit.id_idee
                JOIN texte_traite tt ON jit.id_texte_traite = tt.id
                JOIN texte_reponse AS tr ON tt.id = tr.id_texte_traite
                JOIN reponse AS r ON tr.id = r.id_texte_reponse
                JOIN repondant AS rd ON r.id_repondant = rd.id
                JOIN document AS d ON rd.id_document = d.id
                JOIN jointure_filtration_document AS jfd ON d.id = jfd.id_document

                WHERE r.id_question IN ({format_questions}) AND jfd.id_filtration = %s
            """, tuple(params))
        rows = cursor.fetchall()

    # Conversion en numpy.ndarray pour le champ idee_embedded
    return [
        (
            row[0],                # id
            row[1],                # idee_texte
            np.array(json.loads(row[2])),  # idee_embedded
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



def get_scores(liste_id_question, id_filtration):
    _, _,_,scores = zip(*get_all_idees(liste_id_question, id_filtration))
    return scores

def get_all_documents():
    with get_db_cursor() as cursor:
        cursor.execute("""SELECT id, name FROM document""")
        return cursor.fetchall()

def get_all_questions():
    with get_db_cursor() as cursor:
        cursor.execute("""SELECT id, question, type FROM question""")
        return cursor.fetchall()

def get_possible_answers(id_question: int):
    with get_db_cursor() as cursor:
        cursor.execute("""SELECT DISTINCT t.id, t.texte 
            FROM texte_reponse as t
            JOIN reponse as r ON t.id = r.id_texte_reponse
            WHERE r.id_question = %s
            """, (id_question,)
        )
        return cursor.fetchall()

def get_exigence(id_question: int, liste_id_answer: list[int]):
    with get_db_cursor() as cursor:
        having_clauses = []
        params = [id_question]
        if liste_id_answer:
            placeholders_id = ','.join(['%s'] * len(liste_id_answer))
            having_clauses.append(f"SUM(j.id_reponse NOT IN ({placeholders_id})) = 0")
            having_clauses.append(f"COUNT(DISTINCT j.id_reponse) = %s")

            params.extend(liste_id_answer)
            params.append(len(liste_id_answer))

        having_clause_sql = " AND ".join(having_clauses)

        query=f"""
            SELECT e.id
            FROM exigence e
            JOIN jointure_exigence_reponse j ON j.id_exigence = e.id
            WHERE e.id_question = %s
            GROUP BY e.id
            HAVING {having_clause_sql}
        """
        cursor.execute(query, params)

        result = cursor.fetchone()
        
        return result[0] if result else None

def get_filtration(liste_id_document: list[int], liste_id_exigence: list[int]):
    with get_db_cursor() as cursor:
        having_clauses = []
        params = []

        if liste_id_document:
            placeholders_id = ','.join(['%s'] * len(liste_id_document))
            having_clauses.append(f"SUM(jd.id_document NOT IN ({placeholders_id})) = 0")
            having_clauses.append(f"COUNT(DISTINCT jd.id_document) = %s")
            params.extend(liste_id_document)
            params.append(len(liste_id_document))

        if liste_id_exigence:
            placeholders_id = ','.join(['%s'] * len(liste_id_exigence))
            having_clauses.append(f"SUM(je.id_exigence NOT IN ({placeholders_id})) = 0")
            params.extend(liste_id_exigence)


        having_clauses.append(f"COUNT(DISTINCT je.id_exigence) = %s")
        params.append(len(liste_id_exigence))

        having_clause_sql = " AND ".join(having_clauses)

        cursor.execute(f"""
        SELECT f.id
        FROM filtration f
        LEFT JOIN jointure_filtration_document jd ON jd.id_filtration = f.id
        LEFT JOIN jointure_filtration_exigence je ON je.id_filtration = f.id
        GROUP BY f.id
        HAVING {having_clause_sql}
        """, params)

        result = cursor.fetchone()
        return result[0] if result else None

def get_clusterisation(liste_id_question, id_filtration, nb_clusters, distance):
    format_questions = ','.join(['%s'] * len(liste_id_question))

    where_clauses = ["c.distance = %s", "c.id_filtration = %s"]
    params = [distance, id_filtration]

    # auto_number
    if nb_clusters is None:
        where_clauses.append("c.auto_number = TRUE")
    else:
        where_clauses.append("c.auto_number = FALSE")
        where_clauses.append("c.nb_clusters = %s")
        params.append(nb_clusters)

    # documents et questions restent dans HAVING
    having_clauses = []
    if liste_id_question:
        having_clauses.append(f"SUM(jcq.id_question NOT IN ({format_questions})) = 0")
        having_clauses.append(f"COUNT(DISTINCT jcq.id_question) = %s")
        params.extend(liste_id_question)
        params.append(len(liste_id_question))

    where_clause = " AND ".join(where_clauses)
    having_clause = " AND ".join(having_clauses)

    query = f"""
    SELECT c.id
    FROM clusterisation c
    JOIN jointure_clusterisation_question jcq ON jcq.id_clusterisation = c.id
    WHERE {where_clause}
    GROUP BY c.id
    HAVING {having_clause}
    """
    with get_db_cursor() as cursor:
        cursor.execute(query, params)
        result = cursor.fetchone()
    return result[0] if result else None

def get_clusters(id_clusterisation: int):
    with get_db_cursor() as cursor:
        cursor.execute("""
            SELECT id, texte, taille, score
            FROM cluster
            WHERE id_clusterisation = %s
        """, (id_clusterisation,))
        return cursor.fetchall()