from app.database.read import get_all_idees
from app.domain.clusterisation import clusterisation, find_representative_idea
from app.connection import get_db_cursor

def create_clusterisation(liste_id_doc, liste_id_question, nb_clusters=None, distance="cosine"):
    liste_idees=[]
    for doc in liste_id_doc:
        for question in liste_id_question:
            liste_idees.extend(get_all_idees(doc, question))

    ids, _, _, _,  = zip(*liste_idees)

    labels, centroids = clusterisation(liste_idees,n_clusters=nb_clusters, distance=distance)
    rep_idees = find_representative_idea(liste_idees, labels, centroids, distance=distance)

    with get_db_cursor() as cursor:
        cursor.execute("""INSERT INTO clusterisation (auto_number, nb_clusters, distance)
            VALUES (%s, %s, %s)
            """, (nb_clusters is None, len(rep_idees), distance))
        id_clusterisation = cursor.lastrowid

        for doc in liste_id_doc:
            cursor.execute("""
            INSERT INTO jointure_clusterisation_document (id_clusterisation, id_document)
            VALUES (%s, %s)
            """, (id_clusterisation, doc))
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
        

