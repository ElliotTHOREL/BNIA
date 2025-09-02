from app.connection import get_db_cursor
from app.domain.embed import embed_answers_with_ai_manager
from app.domain.analyse_sentiment import  analyse_sentiment_with_ai_manager
from app.database.delete import delete_one_question
from app.database.read import get_all_idees, get_all_textes_traites, get_all_textes
from app.domain.clusterisation import clusterisation, find_representative_idea_with_ai_manager
from app.domain.tools.text_processor import  traiter_texte

import pandas as pd
from io import BytesIO
from fastapi import UploadFile, File
import json


def insert_document(name: str):
    with get_db_cursor() as cursor:
        cursor.execute("""SELECT id FROM document WHERE name = %s""", (name,))
        result = cursor.fetchone()
        if result:
            id_document = result[0]
            return True, id_document
        else:
            cursor.execute("""INSERT INTO document (name) 
                VALUES (%s)""", 
                (name,))
            id_document = cursor.lastrowid
            return False, id_document

def insert_questions(questions: list[str]):
    with get_db_cursor() as cursor:
        id_question_dict = {}
        for i, question in enumerate(questions):
            cursor.execute("""INSERT INTO question
                (question, type) VALUES (%s, %s)
                ON DUPLICATE KEY UPDATE id=LAST_INSERT_ID(id)""",
                (question, "opinion"))
            id_question = cursor.lastrowid

            id_question_dict[i] = id_question

        return id_question_dict

def insert_repondants(id_document: int, indexes: list[int]):
    """Tous les répondants sont nouveaux. On crée juste n nouveaux répondants"""
    data = [(id_document, index) for index in indexes]
    with get_db_cursor() as cursor:
        cursor.executemany("""INSERT INTO repondant (id_document, num_ds_document) 
            VALUES (%s, %s)""",
            data)
        cursor.execute("""
            SELECT id, num_ds_document FROM repondant WHERE id_document = %s
            """, (id_document,))
        id_repondants_dict = {row[1]: row[0] for row in cursor.fetchall()}
        return id_repondants_dict

class ConteneurTextes:
    def __init__(self):
        self.textes_en_base =  None  #Set de textes
        self.textes_traites_en_base = None #Set de textes
        self.textes_traites_to_add=[] #Liste de textes
        self.textes_to_add=[] #Liste de (texte, texte_traite)
        self.reponses_to_add=[] #Liste de (id_q, id_rd, texte)
    
    def get_textes_en_base(self):
        if self.textes_en_base is None:
            self.textes_en_base = {row[1] for row in get_all_textes()}
        return self.textes_en_base
    
    def get_textes_traites_en_base(self):
        if self.textes_traites_en_base is None:
            self.textes_traites_en_base = {row[1] for row in get_all_textes_traites()}
        return self.textes_traites_en_base
    
    def add_all(self):
        with get_db_cursor() as cursor:
            cursor.executemany("""INSERT INTO texte_traite (texte_traite) 
                        VALUES (%s)""",
                        self.textes_traites_to_add)

        dico_textes_traites = {row[1]: row[0] for row in get_all_textes_traites()}

        with get_db_cursor() as cursor:
            cursor.executemany("""INSERT INTO texte_reponse (id_texte_traite, texte) 
                        VALUES (%s, %s)""", 
                        [(dico_textes_traites[texte_traite], texte) for texte, texte_traite in self.textes_to_add])
            
        dico_textes = {row[1]: row[0] for row in get_all_textes()}

        with get_db_cursor() as cursor:
            cursor.executemany("""INSERT INTO reponse (id_question, id_repondant, id_texte_reponse) 
                        VALUES (%s, %s, %s)""", 
                        [(id_question, id_repondant,dico_textes[texte]) for id_question, id_repondant, texte in self.reponses_to_add])
                
async def import_excel_to_bdd(file: UploadFile = File(...)):
    name = file.filename

    already_exists, id_document = insert_document(name)
    if already_exists:
            return {"status": "already_exists", "name": name}

    # On lit le doc Excel
    content = await file.read()
    df = pd.read_excel(BytesIO(content))

    # On récupère les questions
    questions = list(df.columns[:])
    id_question_dict = insert_questions(questions)

    # On insert les repondants
    id_repondants_dict = insert_repondants(id_document, df.index)

    #Objet qui permet l'ajout des réponses
    conteneur_textes = ConteneurTextes()
    #On sélectionne ce qui faut ajouter
    for index, row in df.iterrows():
        id_repondant = id_repondants_dict[index]
        for index_col, col in enumerate(df.columns):
            id_question = id_question_dict[index_col]

            val = row.iloc[index_col]
            if pd.isna(val):
                continue
            texte = str(val)

            if texte not in conteneur_textes.get_textes_en_base():
                texte_traite = traiter_texte(texte)
                if texte_traite not in conteneur_textes.get_textes_traites_en_base():
                    conteneur_textes.textes_traites_to_add.append((texte_traite,))
                    conteneur_textes.get_textes_traites_en_base().add(texte_traite)
                
                conteneur_textes.textes_to_add.append((texte, texte_traite))
                conteneur_textes.get_textes_en_base().add(texte)
            
            conteneur_textes.reponses_to_add.append((id_question,id_repondant,texte))
    #On ajoute tout en 1 fois pour optimiser les opérations
    conteneur_textes.add_all()
    return {"status": "import_done", "name": name}

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

def de_masquer_cluster(id_cluster: int):
    with get_db_cursor() as cursor:
        cursor.execute("""UPDATE cluster SET masque = NOT masque WHERE id = %s""",
            (id_cluster,)
        )

async def embed_all_answers(ai_manager):
    with get_db_cursor() as cursor:
        # Récupérer les textes qui n'ont pas encore d'idées embeddées
        cursor.execute("""
            SELECT tt.id, tt.texte_traite
            FROM texte_traite tt
            WHERE tt.idees_extraites = FALSE
        """)
        res = cursor.fetchall()
        liste_ids, liste_textes = zip(*res)

        liste_results = await embed_answers_with_ai_manager(liste_textes, ai_manager)
        #Une liste de triplets (indice_reponse, texte, embed)

        for indice_reponse, texte, embed in liste_results:
            # Insérer l'idée embeddée
            cursor.execute(
                """INSERT INTO idee_embedded (idee_texte, idee_embedded)
                VALUES (%s, %s)""",
                (texte, json.dumps(embed.tolist()))
            )
            id_idee = cursor.lastrowid
            
            cursor.execute(
                """INSERT INTO jointure_idee_texte (id_texte_traite, id_idee)
                VALUES (%s, %s)""",
                (liste_ids[indice_reponse], id_idee)
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

    _calculer_repondants(id_filtration)

    return id_filtration

def _calculer_repondants(id_filtration: int):
    with get_db_cursor() as cursor:
        cursor.execute(f"""SELECT COUNT(*) 
            FROM jointure_filtration_exigence 
            WHERE id_filtration = %s""",
             (id_filtration,)
             )
        nb_exigence = cursor.fetchone()[0]

        if nb_exigence == 0:
            cursor.execute(f"""SELECT rd.id 
                FROM repondant as rd
                JOIN document as doc ON rd.id_document = doc.id
                JOIN jointure_filtration_document as jfd ON doc.id = jfd.id_document
                WHERE jfd.id_filtration = %s""",
                 (id_filtration,)
                 )
            liste_id_repondant = [row[0] for row in cursor.fetchall()]
        else:
            cursor.execute(f"""SELECT rd.id 
                FROM repondant as rd
                JOIN document as doc ON rd.id_document = doc.id
                JOIN jointure_filtration_document as jfd ON doc.id = jfd.id_document
                JOIN jointure_filtration_exigence as jfe ON jfd.id_filtration = jfe.id_filtration
                JOIN exigence as e ON jfe.id_exigence = e.id
                JOIN jointure_exigence_reponse as jer ON e.id = jer.id_exigence

                JOIN reponse as r2 ON  r2.id_repondant = rd.id AND r2.id_texte_reponse = jer.id_reponse 
                                   AND r2.id_question = e.id_question
                                   AND r2.id_texte_reponse = jer.id_reponse
                WHERE jfd.id_filtration = %s
                
                GROUP BY rd.id
                HAVING COUNT(DISTINCT e.id) = %s
                """,
                 (id_filtration, nb_exigence)
                 )
            liste_id_repondant = [row[0] for row in cursor.fetchall()]

        cursor.executemany(
            """INSERT INTO jointure_filtration_repondant (id_filtration, id_repondant) VALUES (%s, %s)""",
            [(id_filtration, id_repondant) for id_repondant in liste_id_repondant]
        )

async def create_clusterisation(liste_id_question, id_filtration, ai_manager, nb_clusters=None, distance="cosine"):
    liste_idees=get_all_idees(liste_id_question, id_filtration)


    #On vérifie qu'il y a assez d'idées pour clusteriser
    if nb_clusters is None:
        seuil =20
    else:
        seuil = nb_clusters
    if len(liste_idees) < seuil:
        return -1


    ids, _, _, _  = zip(*liste_idees)

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