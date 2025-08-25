from app.connection import get_db_cursor
from app.database.create import init_bdd

def delete_document(id_document):
    with get_db_cursor() as cursor:
        cursor.execute("""DELETE FROM document WHERE id = %s""", (id_document,))

def reset_all():
    with get_db_cursor() as cursor:
        cursor.execute("""DROP TABLE IF EXISTS idee_embedded""")
        cursor.execute("""DROP TABLE IF EXISTS texte_reponse""")
        cursor.execute("""DROP TABLE IF EXISTS reponse""")
        cursor.execute("""DROP TABLE IF EXISTS repondant""")
        cursor.execute("""DROP TABLE IF EXISTS question""")
        cursor.execute("""DROP TABLE IF EXISTS document""")
    init_bdd()

