from app.connection import get_db_cursor


def get_all_idees(id_document: int, id_question: int):
    with get_db_cursor() as cursor:
        cursor.execute("""SELECT idee_embedded.id,idee_embedded.idee_texte, idee_embedded.idee_embed, idee_embedded.score 
        FROM reponse
        JOIN texte_reponse ON  reponse.id_texte = texte_reponse.id
        JOIN repondant ON reponse.id_repondant = repondant.id
        JOIN idee_embedded ON idee_embedded.id_reponse = texte_reponse.id
        WHERE repondant.id_document = %s AND reponse.id_question = %s
        """, (id_document, id_question))
        return cursor.fetchall()

def get_all_documents():
    with get_db_cursor() as cursor:
        cursor.execute("""SELECT id, name FROM document""")
        return cursor.fetchall()

def check_clusterisation(liste_id_doc, liste_id_question, nb_clusters, distance):
    with get_db_cursor() as cursor:
        format_docs = ','.join(['%s'] * len(liste_id_doc)) if liste_id_doc else 'NULL'
        format_questions = ','.join(['%s'] * len(liste_id_question)) if liste_id_question else 'NULL'

        having_clauses = []
        params = []

        # auto_number
        if nb_clusters is None:
            having_clauses.append("c.auto_number = TRUE")
        else:
            having_clauses.append("c.auto_number = FALSE")
            having_clauses.append("c.nb_clusters = %s")
            params.append(nb_clusters)

        # documents
        if liste_id_doc:
            having_clauses.append(f"SUM(jcd.id_document NOT IN ({format_docs})) = 0")

        # questions
        if liste_id_question:
            having_clauses.append(f"SUM(jcq.id_question NOT IN ({format_questions})) = 0")

        having_clause = " AND ".join(having_clauses)

        query = f"""
        SELECT c.id
        FROM clusterisation c
        JOIN jointure_clusterisation_document jcd ON jcd.id_clusterisation = c.id
        JOIN jointure_clusterisation_question jcq ON jcq.id_clusterisation = c.id
        WHERE c.distance = %s
        GROUP BY c.id
        HAVING {having_clause}
        """
        # distance en premier
        params = [distance] + params
        # ajouter les ids des docs/questions
        if liste_id_doc:
            params += liste_id_doc
        if liste_id_question:
            params += liste_id_question

        cursor.execute(query, params)
        result = cursor.fetchone()
        return result[0] if result else None