import streamlit as st
from streamlit_plotly_events import plotly_events

import requests
from config import API_BASE  # Import depuis config.py

import matplotlib.pyplot as plt
import plotly.graph_objects as go
import plotly.express as px

import numpy as np
import pandas as pd


st.set_page_config(layout="wide")

# Fonction pour créer des intervalles de scores
def create_score_bins(scores, num_bins):
    """Crée des intervalles pour regrouper les scores"""
    bins = np.linspace(1.0, 5.0, num_bins + 1)
    bin_centers = (bins[:-1] + bins[1:]) / 2
    bin_labels = [f"{bins[i]:.1f}-{bins[i+1]:.1f}" for i in range(len(bins)-1)]
    
    # Compter les scores dans chaque intervalle
    hist, _ = np.histogram(scores, bins=bins)
    
    return bin_centers, bin_labels, hist

def create_gradient_pie_chart(scores):
    st.title("Distribution des Scores")
    
    # Paramètres configurables
    num_bins = 50#st.slider("Nombre d'intervalles", 5, 20, 10)
    
    # Créer les intervalles
    bin_centers, bin_labels, counts = create_score_bins(scores, num_bins)
    
    # Filtrer les intervalles avec peu de données
    total_count = len(scores)
   
    
    # Créer le dégradé de couleurs (rouge à vert)
    # Normaliser les centres des intervalles entre 0 et 1
    norm_centers = (bin_centers - 1.0) / (5.0 - 1.0)
    
    colors = plt.cm.RdYlGn(norm_centers)
    
    fig, ax = plt.subplots(figsize=(12, 8))
    wedges, texts, autotexts = ax.pie(
        counts, 
        labels=bin_labels,
        colors=colors,
        autopct='%1.1f%%',
        startangle=90,
        textprops={'fontsize': 10}
    )

    # Améliorer l'apparence
    # for autotext in autotexts:
    #     autotext.set_color('white')
    #     autotext.set_fontweight('bold')
    #     autotext.set_fontsize(9)

    for txt in texts + autotexts:
        txt.set_visible(False)
    
    # Titre
    ax.set_title(f'Distribution des Scores (Total: {total_count:,} valeurs)', 
                 fontsize=16, fontweight='bold', pad=20)
    
    # Créer une colorbar pour montrer le dégradé
    sm = plt.cm.ScalarMappable(cmap='RdYlGn', norm=plt.Normalize(vmin=1.0, vmax=5.0))
    sm.set_array([])
    cbar = plt.colorbar(sm, ax=ax, shrink=0.6, aspect=20)
    cbar.set_label('Score', fontsize=12, fontweight='bold')
    
    plt.tight_layout()
    
    # Afficher le graphique dans Streamlit
    st.pyplot(fig)
    
    # Afficher quelques statistiques
    st.subheader("Statistiques")
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Nombre total", f"{total_count:,}")
    with col2:
        st.metric("Score moyen", f"{np.mean(scores):.2f}")
    with col3:
        st.metric("Score médian", f"{np.median(scores):.2f}")
    with col4:
        st.metric("Écart-type", f"{np.std(scores):.2f}")
    



def create_bubble_chart(clusters):
    """
    Créer un bubble chart interactif à partir des clusters
    
    Parameters:
    clusters: Liste de tuples (id_cluster, texte, poids, score)
    """
    np.random.seed(42)  # Pour la reproductibilité
    # Préparer les données

    data = []
    for cluster in clusters:
        id_cluster, texte, poids, score = cluster
        data.append({
            'id_cluster': id_cluster,
            'texte': texte,
            'poids': poids,
            'score': score
        })  
    df = pd.DataFrame(data)
    
    # Générer des positions aléatoires pour les bulles (simulation d'un layout)
    n_items = len(df)
    
    def find_x(n, taille_grille):
        if taille_grille % 2 ==1:
            return (2*n+1)%taille_grille
        else:
            interm = (2*n+1)%(2*taille_grille)
            if interm <taille_grille:
                return  interm
            else:
                return interm - taille_grille -1
    def find_y(n, taille_grille):
        return (2*n+1)//taille_grille

    v_find_x = np.vectorize(find_x)
    v_find_y = np.vectorize(find_y)
    
    taille_grille = int(np.ceil(np.sqrt(2*n_items)))
    df['x'] = v_find_x(np.arange(n_items),taille_grille) + np.random.normal(0, 0.2, n_items)
    df['y'] = v_find_y(np.arange(n_items),taille_grille) + np.random.normal(0, 0.2, n_items)-1
    
    
    def normalize_bubble_size(poids_series, size_range=(10, 100)):
        """
        Normalise les tailles de bulles avec différentes méthodes
        
        Args:
            poids_series: Série pandas avec les poids
            size_range: Tuple (taille_min, taille_max) pour les bulles
            method: 'minmax', 'zscore', 'sqrt', ou 'log'
        """
        min_size, max_size = size_range
        
        # Normalisation Min-Max classique
        min_poids = poids_series.min()
        max_poids = poids_series.max()
        if max_poids == min_poids:  # Éviter division par zéro
            return pd.Series([max_size] * len(poids_series))
        normalized = (poids_series - min_poids) / (max_poids - min_poids)
      
        # Appliquer la plage de tailles désirée
        return normalized * (max_size - min_size) + min_size
    
    df['taille_bulle'] = normalize_bubble_size(df['poids'], size_range=(50, 150))
    



    # Créer le bubble chart avec Plotly
    fig = go.Figure()

    # Ajouter les bulles
    fig.add_trace(go.Scatter(
        x=df['x'],
        y=df['y'],
        mode='markers+text',
        marker=dict(
            size=df['taille_bulle'],
            color=df['score'],
            colorscale='RdYlGn',
            cmin=1.0,
            cmax=5.0,
            showscale=True,
            colorbar=dict(
                title=dict(
                    text="Score",
                    side='right'
                )
            ),
            opacity=0.7,
            line=dict(width=2, color='white')
        ),
        text=df['texte'],
        textposition='middle center',
        textfont=dict(
            size=14,
            color='black',
            weight="bold"
        ),
        customdata=df[['id_cluster', 'poids', 'score']],
        hovertemplate=(
            '<b>%{text}</b><br>' +
            'Poids: %{customdata[1]:.2f}<br>' +
            'Score: %{customdata[2]:.2f}<br>' +
            '<extra></extra>'
        ),
        name='Clusters'
    ))

    # Personnaliser le layout
    fig.update_layout(
        xaxis=dict(
            showgrid=False,
            showticklabels=False,
            zeroline=False
        ),
        yaxis=dict(
            showgrid=False,
            showticklabels=False,
            zeroline=False
        ),
        plot_bgcolor='white',
        paper_bgcolor='white',
        width=1200,
        height=600,
        showlegend=False,
        margin=dict(l=20, r=20, t=0, b=20),
        clickmode="event+select"  # Activer les clics
    )

    # Afficher le graphique et capturer les clics
    st.title("Idées principales")

    st.plotly_chart(fig, use_container_width=True, key="bubble_chart")

@st.dialog("Changer le score de l'idée")
def show_rename_dialog(id_idee, idee_texte, idee_score):
    col1, col2 = st.columns(2)
    with col1:
        st.write(idee_texte)
    with col2:
        new_score = st.slider(
            "Score",
            min_value=1.0,
            max_value=5.0,
            value=idee_score,
            step=0.1,
            format="%.1f"
        )
    if st.button("Valider"):
        url = f"{API_BASE}/document/rescorer_idee"
        params = {
            "id_idee": id_idee,
            "idee_score": new_score
        }
        _ = requests.post(url, params=params)
        for idee in st.session_state["idees_in_cluster"]:
            if idee[0] == id_idee:
                idee[2] = new_score
                break
        for cluster in st.session_state["clusters"]:
            if cluster[0] == st.session_state["id_cluster"]:
                s=0
                poids = 0
                for idee in st.session_state["idees_in_cluster"]:
                    s += idee[2] * idee[3]
                    poids += idee[3]
                assert poids == cluster[2]
                cluster[3] = s/poids
                break
        st.success("Score modifié avec succès")
        st.rerun()




        
def app():
    st.title("Visualisation des documents")

    try:
        response = requests.get(f"{API_BASE}/document/documents")
        documents = response.json()
    except Exception as e:
        st.error(f"Erreur lors de la récupération des documents : {e}")
        documents = []

    try:
        response = requests.get(f"{API_BASE}/document/questions")
        questions = response.json()
    except Exception as e:
        st.error(f"Erreur lors de la récupération des questions : {e}")
        questions = []


    with st.form("visualisation"):
        col1, col2, col3, col4, col5 = st.columns([3,3,1,1,1])
        with col1:
            document = st.selectbox("Document", options=[doc[1] for doc in documents])
        with col2:
            question = st.selectbox("Question", options=[question[1] for question in questions])
        with col3:
            nb_clusters = st.number_input("Nombre de clusters", min_value=0, value=10)
        with col4:
            distance = st.selectbox("Distance", options=["cosine", "euclidean"])
        with col5:
            submitted = st.form_submit_button("Générer les visuels")

    if submitted:
        # Récupérer les ID correspondants aux selections
        liste_id_doc = [doc[0] for doc in documents if doc[1] == document]
        liste_id_question = [q[0] for q in questions if q[1] == question]
        url = f"{API_BASE}/analyse/create_clusterisation"
        params = {
            "nb_clusters": nb_clusters,
            "distance": distance
        }
        payload = {
            "liste_id_doc": liste_id_doc,
            "liste_id_question": liste_id_question
        }
        headers = {
            "accept": "application/json",
            "Content-Type": "application/json"
        }

        response = requests.post(url, params=params, json=payload, headers=headers)
        st.session_state["scores"] = np.array(response.json()["scores"])
        st.session_state["clusters"] = response.json()["clusters"]

    if 'scores' in st.session_state:
        col1, col2= st.columns([2,3])
        with col1:
            create_gradient_pie_chart( st.session_state["scores"])
        with col2:
            #create_word_cloud(clusters)
            create_bubble_chart(st.session_state["clusters"])


    if 'clusters' in st.session_state:
        clusters = sorted(st.session_state["clusters"], key=lambda x: -x[2])
        with st.form("visualisation_cluster"):
            col1, col2 = st.columns(2)
            with col1:
                name_cluster = st.selectbox("Cluster", options=[cluster[1] for cluster in clusters])
            with col2:
                submitted_cluster = st.form_submit_button("Observer le cluster")
            
        if submitted_cluster:
            for cluster in clusters:
                if cluster[1] == name_cluster:
                    id_cluster = cluster[0]
                    break
            url = f"{API_BASE}/document/idees_in_cluster"
            params = {
                "id_cluster": id_cluster
            }
            response = requests.get(url, params=params)
            st.session_state["id_cluster"] = id_cluster
            st.session_state["idees_in_cluster"] = response.json()

    if 'idees_in_cluster' in st.session_state:
        for idee in st.session_state["idees_in_cluster"]:
            col1, col2, col3, col4 = st.columns([7,1,1,2])
            with col1:
                st.write(idee[1]) 
            with col2:
                st.write(idee[3])
            with col3:
                st.write(round(idee[2], 1))
            with col4:
                if st.button("Modifier", key=f"modifier_{idee[0]}"):
                    show_rename_dialog(idee[0], idee[1], idee[2])




            


            

if __name__ == "__main__":
    app()