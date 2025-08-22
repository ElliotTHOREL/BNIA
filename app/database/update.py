from app.connection import get_db_cursor
import pandas as pd
from app.domain.embed import embed_answers

def import_excel_to_bdd(file_path: str):
    name = file_path.split("/")[-1]
    with get_db_cursor() as cursor:
        cursor.execute("""SELECT COUNT(*) FROM document WHERE name = %s""", (name,))
        if cursor.fetchone()[0] > 0:
            return
        
    df = pd.read_excel(file_path)


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


        response_data = []
        for index, row in df.iterrows():
            id_repondant = repondants_dict[index]
            for id_ds_doc, id_question in question_ids.items():
                reponse = row[id_ds_doc]
                if pd.isna(reponse):
                    reponse = None

                response_data.append((id_question, id_repondant, reponse))

        cursor.executemany("""
            INSERT INTO reponse (id_question, id_repondant, reponse)
            VALUES (%s, %s, %s)
        """, response_data)

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
            cursor.execute("""INSERT INTO idee_embedded
                            (id_reponse, idee_texte, idee_embed)
                            VALUES (%s, %s, %s)""",
                            (liste_ids_answers[indice_reponse], texte, embed))

        cursor.execute("""UPDATE texte_reponse SET traite = TRUE""")   


