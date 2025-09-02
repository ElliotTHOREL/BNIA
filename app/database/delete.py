from app.connection import get_db_cursor
from app.database.create import init_bdd

def reset_all():
    with get_db_cursor() as cursor:
        cursor.execute("""DROP TABLE IF EXISTS jointure_filtration_repondant""")
        cursor.execute("""DROP TABLE IF EXISTS jointure_cluster_idees""")
        cursor.execute("""DROP TABLE IF EXISTS jointure_clusterisation_question""")
        cursor.execute("""DROP TABLE IF EXISTS cluster""")
        cursor.execute("""DROP TABLE IF EXISTS jointure_filtration_document""")
        cursor.execute("""DROP TABLE IF EXISTS jointure_filtration_exigence""")
        cursor.execute("""DROP TABLE IF EXISTS jointure_exigence_reponse""")
        cursor.execute("""DROP TABLE IF EXISTS clusterisation""")
        cursor.execute("""DROP TABLE IF EXISTS filtration""")
        cursor.execute("""DROP TABLE IF EXISTS exigence""")
        
        cursor.execute("""DROP TABLE IF EXISTS jointure_idee_texte""") 
        cursor.execute("""DROP TABLE IF EXISTS idee_embedded""")
        cursor.execute("""DROP TABLE IF EXISTS reponse""")
        cursor.execute("""DROP TABLE IF EXISTS texte_reponse""")
        cursor.execute("""DROP TABLE IF EXISTS texte_traite""")
        cursor.execute("""DROP TABLE IF EXISTS repondant""")
        cursor.execute("""DROP TABLE IF EXISTS question""")
        cursor.execute("""DROP TABLE IF EXISTS document""")
    init_bdd()

def reset_all_clusterisation():
    with get_db_cursor() as cursor:
        cursor.execute("""DROP TABLE IF EXISTS jointure_filtration_repondant""")
        cursor.execute("""DROP TABLE IF EXISTS jointure_cluster_idees""")
        cursor.execute("""DROP TABLE IF EXISTS jointure_clusterisation_question""")
        cursor.execute("""DROP TABLE IF EXISTS cluster""")
        cursor.execute("""DROP TABLE IF EXISTS jointure_filtration_document""")
        cursor.execute("""DROP TABLE IF EXISTS jointure_filtration_exigence""")
        cursor.execute("""DROP TABLE IF EXISTS jointure_exigence_reponse""")
        cursor.execute("""DROP TABLE IF EXISTS clusterisation""")
        cursor.execute("""DROP TABLE IF EXISTS filtration""")
        cursor.execute("""DROP TABLE IF EXISTS exigence""")
    init_bdd()



def delete_one_document(id_document):
    with get_db_cursor() as cursor:


        cursor.execute("""
            DELETE f
            FROM filtration f
            INNER JOIN jointure_filtration_document j
                ON f.id = j.id_filtration
            WHERE j.id_document = %s
        """, (id_document,))


        cursor.execute("""DELETE FROM document WHERE id = %s""", (id_document,)) 


def delete_one_question(id_question):
    with get_db_cursor() as cursor:
        cursor.execute("""
            DELETE c
            FROM clusterisation c
            INNER JOIN jointure_clusterisation_question j
                ON c.id = j.id_clusterisation
            WHERE j.id_question = %s
        """, (id_question,))



        cursor.execute("""
            DELETE f
            FROM filtration AS f
            INNER JOIN jointure_filtration_exigence AS j
                ON f.id = j.id_filtration
            INNER JOIN exigence AS c
                ON j.id_exigence = c.id
            WHERE j.id_question = %s
        """, (id_question,))
        cursor.execute("""DELETE FROM question WHERE id = %s""", (id_question,)) 

        
