from app.connection import get_db_cursor
import pandas as pd

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

