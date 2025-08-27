from app.connection import get_db_cursor
from app.database.create import init_bdd

def delete_document(id_document):
    with get_db_cursor() as cursor:
        cursor.execute("""DELETE FROM document WHERE id = %s""", (id_document,))

def reset_all():
    with get_db_cursor() as cursor:
        cursor.execute("""DROP TABLE IF EXISTS jointure_cluster_idees""")
        cursor.execute("""DROP TABLE IF EXISTS jointure_clusterisation_document""")
        cursor.execute("""DROP TABLE IF EXISTS jointure_clusterisation_question""")
        cursor.execute("""DROP TABLE IF EXISTS cluster""")
        cursor.execute("""DROP TABLE IF EXISTS clusterisation""")
        cursor.execute("""DROP TABLE IF EXISTS idee_embedded""")
        cursor.execute("""DROP TABLE IF EXISTS reponse""")
        cursor.execute("""DROP TABLE IF EXISTS repondant""")
        cursor.execute("""DROP TABLE IF EXISTS texte_reponse""")
        cursor.execute("""DROP TABLE IF EXISTS question""")
        cursor.execute("""DROP TABLE IF EXISTS document""")
    init_bdd()

def delete_one_document(id_document):
    with get_db_cursor() as cursor:
        cursor.execute("""
            DELETE c
            FROM clusterisation c
            INNER JOIN jointure_clusterisation_document j
                ON c.id = j.id_clusterisation
            WHERE j.id_document = %s
        """, (id_document,))
        # jointure_clusterisation_document, jointure_clusterisation_question, cluster 
        # et jointure_cluster_idees sont supprimés automatiquement par cascade

        cursor.execute("""DELETE FROM document WHERE id = %s""", (id_document,)) 
        # repondant, reponse et jointure_clusterisation_document sont supprimés automatiquement par cascade

    