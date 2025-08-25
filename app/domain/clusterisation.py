from sklearn.cluster import KMeans
from hdbscan import HDBSCAN

import numpy as np

def compute_hdbscan_centroids(embeddings, labels):
    """
    Calcule les centroïdes pour chaque cluster HDBSCAN.
    - embeddings : array (n_samples, n_features)
    - labels : array (n_samples,) avec numéros de cluster ou -1 (bruit)
    """
    unique_clusters = [c for c in np.unique(labels) if c != -1]
    unique_clusters.sort()
    centroids = []

    for cluster_id in unique_clusters:
        # Sélectionner les points du cluster
        cluster_points = embeddings[labels == cluster_id]
        # Calculer la moyenne (centre de masse)
        centroid = cluster_points.mean(axis=0)
        centroids.append(centroid)

    return np.array(centroids)



def clusterisation(liste_idees_embed, n_clusters=None, distance="cosine"):
    """entrée : liste de triplets (textes, embed, score)"""

    embeddings = np.array([embed for _ , _ , embed, _ in liste_idees_embed])
    if distance == "cosine":
        norms = np.linalg.norm(embeddings, axis=1, keepdims=True)
        norms[norms == 0] = 1
        used_embeddings = embeddings / norms
    elif distance == "euclidean":
        used_embeddings = embeddings.copy()
    else:
        raise ValueError(f"Distance {distance} non supportée")

    if n_clusters is None:
        clusterer = HDBSCAN(min_cluster_size=5)
        labels = clusterer.fit_predict(used_embeddings)
        centroids = compute_hdbscan_centroids(used_embeddings, labels)
        return labels, centroids
    else:
        kmeans = KMeans(n_clusters=n_clusters, random_state=42)
        labels = kmeans.fit_predict(used_embeddings)
        centroids = kmeans.cluster_centers_
        return labels, centroids


def find_representative_idea(liste_idees_embed, labels, centroids, distance="cosine"):
    """
    Trouve l'idée la plus représentative pour chaque cluster.
    Entrée:
    - liste_idees_embed : liste de quadruplets (id, texte, embed, score)
    - labels : array (n_samples,) avec numéros de cluster ou -1 (bruit)
    - centroids : array (n_clusters, n_features)
    Sortie:
    - liste de triplets (theme, taille, score)
         - theme : le thème du cluster
         - taille : la taille du cluster
         - score : le score du cluster
    """
    _, textes, embeds, scores = zip(*liste_idees_embed)
    len_texte = np.array([len(t) for t in textes])
    embeddings = np.array(embeds)
    if distance == "cosine":
        norms_embeddings = np.linalg.norm(embeddings, axis=1, keepdims=True)
        norms_embeddings[norms_embeddings == 0] = 1
        norms_centroids = np.linalg.norm(centroids, axis=1, keepdims=True)
        norms_centroids[norms_centroids == 0] = 1
        used_embeddings = embeddings / norms_embeddings
        used_centroids = centroids / norms_centroids
    elif distance == "euclidean":
        used_embeddings = embeddings.copy()
        used_centroids = centroids.copy()
    else:
        raise ValueError(f"Distance {distance} non supportée")

    ordered_labels = [c for c in np.unique(labels) if c != -1] #extraction des labels
    ordered_labels.sort()# Ordonne les labels

    representative_ideas = []
    for cluster_id in ordered_labels:
        id_labels = np.where(labels == cluster_id)[0]
        best_metrique = np.inf
        best_id_label = None
        score = 0
        for id_label in id_labels:
            score += scores[id_label]
            distance_to_centroid = np.linalg.norm(used_embeddings[id_label] - used_centroids[cluster_id], ord=2)
            len_text = len_texte[id_label]
            metrique = distance_to_centroid * len_text
            if metrique < best_metrique:
                best_metrique = metrique
                best_id_label = id_label

        score /= len(id_labels)
        representative_ideas.append((textes[best_id_label]), len(id_labels), score)

    return representative_ideas