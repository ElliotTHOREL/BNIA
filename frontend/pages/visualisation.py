import streamlit as st
from streamlit_plotly_events import plotly_events

import requests
from config import API_BASE  # Import depuis config.py
from tools import get_questions, get_documents, get_possible_answers

import matplotlib.pyplot as plt
import plotly.graph_objects as go
import plotly.express as px

import numpy as np
import pandas as pd


st.set_page_config(layout="wide")



st.markdown("""
<style>
    /* Tags qui s'adaptent au contenu sans tronquer */
    .stMultiSelect span[data-baseweb="tag"] {
        /* Taille adaptative */
        width: auto !important;
        min-width: auto !important;
        max-width: none !important;
        height: auto !important;
        min-height: 40px !important;
        
        /* Espacement généreux */
        padding: 12px 20px !important;
        margin: 6px !important;
        
        /* Texte non tronqué */
        white-space: normal !important;
        overflow: visible !important;
        text-overflow: unset !important;
        word-wrap: break-word !important;
        
        /* Apparence */
        background-color: #4a90e2 !important;
        color: white !important;
        border-radius: 20px !important;
        
        /* Flexbox pour bon alignement */
        display: inline-flex !important;
        align-items: center !important;
        justify-content: flex-start !important;
        flex-wrap: wrap !important;
        
        /* Taille de police */
        font-size: 14px !important;
        line-height: 1.4 !important;
        font-weight: 500 !important;
    }
    
    /* Texte du tag - s'étend pour tout afficher */
    .stMultiSelect span[data-baseweb="tag"] span:first-child {
        flex: 1 1 auto !important;
        white-space: normal !important;
        word-break: break-word !important;
        overflow: visible !important;
        text-align: left !important;
        max-width: none !important;
    }
    
    /* Bouton de suppression */
    .stMultiSelect span[data-baseweb="tag"] span[role="presentation"] {
        flex-shrink: 0 !important;
        margin-left: 10px !important;
        font-size: 16px !important;
    }
    
    /* Conteneur principal pour éviter les conflits */
    .stMultiSelect > div > div > div {
        flex-wrap: wrap !important;
        gap: 6px !important;
    }
</style>
""", unsafe_allow_html=True)



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
    
    
    return (fig, total_count, np.mean(scores), np.median(scores), np.std(scores))



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
    return fig


def rename(id_idee, new_score):
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
      
def app():
    st.title("Visualisation des documents")


    if "documents" not in st.session_state:
        get_documents()
    documents = st.session_state["documents"]

    if "questions" not in st.session_state:
        get_questions()
    questions = st.session_state["questions"]


    with st.form("visualisation"):
        col1, col2, col3, col4, col5 = st.columns([3,3,1,1,1])
        with col1:
            selected_documents = st.multiselect("Document", options=[doc[1] for doc in documents])
        with col2:
            selected_questions = st.multiselect("Question", options=[question[1] for question in questions if question[2] == "opinion"])
        with col3:
            nb_clusters = st.number_input("Nombre de clusters", min_value=0, value=10)
        with col4:
            distance = st.selectbox("Distance", options=["cosine", "euclidean"])
        with col5:
            submitted = st.form_submit_button("Générer les visuels")

        q_ident = [q for q in questions if q[2] == "identification"]
        nb_ident=len(q_ident)
        
        selected_ident_questions=[]
        if nb_ident > 0:
            for i in range(nb_ident):
                if "possible_answers" not in st.session_state or q_ident[i][0] not in st.session_state["possible_answers"]:
                    get_possible_answers(q_ident[i][0])
                
                possible_answers = list( st.session_state["possible_answers"][q_ident[i][0]].keys() )
                selected_ident_questions.append(st.multiselect(q_ident[i][1], options=possible_answers))


    if submitted:
        # Récupérer les ID correspondants aux selections
        if selected_documents:
            liste_id_doc = [doc[0] for doc in documents if doc[1] in selected_documents]
        else:
            liste_id_doc = [doc[0] for doc in documents]

        if selected_questions:
            liste_id_question = [q[0] for q in questions if q[1] in selected_questions]
        else:
            liste_id_question = [q[0] for q in questions if q[2] == "opinion"]

        questions_filtrees =[]
        filtres=[]
        for i in range(nb_ident):
            if len(selected_ident_questions[i]) > 0:
                questions_filtrees.append(q_ident[i][0])

                dico=st.session_state["possible_answers"][q_ident[i][0]]
                text_selected_answers= selected_ident_questions[i]
                id_selected_answers = [dico[answer] for answer in text_selected_answers]
                filtres.append(id_selected_answers)
        
        url = f"{API_BASE}/analyse/create_clusterisation"
        payload = {
            "liste_id_doc": liste_id_doc,
            "liste_id_question": liste_id_question,
            "questions_filtrees": questions_filtrees,
            "filtres": filtres,
            "nb_clusters": nb_clusters,
            "distance": distance
        }

        headers = {"accept": "application/json", "Content-Type": "application/json"}

        response = requests.post(url, json=payload, headers=headers)
        if response.json()["status"] == "failure pas assez d'idées":
            st.error("Il n'y a pas assez d'idées qui correspondent aux filtres")
            st.stop()

        st.session_state["scores"] = np.array(response.json()["scores"])
        st.session_state["clusters"] = response.json()["clusters"]
        st.session_state["scores_chart"] = create_gradient_pie_chart( st.session_state["scores"])
        st.session_state["bubble_chart"] = create_bubble_chart(st.session_state["clusters"])
        st.session_state["id_cluster"] = None

    if 'scores' in st.session_state:
        col1, col2= st.columns([2,3])
        with col1:
            fig, total_count, score_moyen, score_median, score_std = st.session_state["scores_chart"]

            st.pyplot(fig)
            st.subheader("Statistiques")
            col11, col12, col13, col14 = st.columns(4)  
            with col11:
                st.metric("Nombre total", f"{total_count:,}")
            with col12:
                st.metric("Score moyen", f"{score_moyen:.2f}")
            with col13:
                st.metric("Score médian", f"{score_median:.2f}")
            with col14:
                st.metric("Écart-type", f"{score_std:.2f}")


        with col2:
            fig2 = st.session_state["bubble_chart"]
            st.plotly_chart(fig2, use_container_width=True, key="scores_chart")


    if 'clusters' in st.session_state:
        clusters = sorted(st.session_state["clusters"], key=lambda x: -x[2])
        with st.form("visualisation_cluster"):
            col1, col2 = st.columns(2)
            with col1:
                name_cluster = st.selectbox("Thème", options=[cluster[1] for cluster in clusters])
            with col2:
                submitted_cluster = st.form_submit_button("Voir les détails du thème")
            
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

    if 'id_cluster' in st.session_state and st.session_state['id_cluster'] is not None:
        col1, col2, col3, col4 = st.columns([7,1,1,5])
        with col1:
            st.markdown("**Idées**") 
        with col2:
            st.markdown("**Occurences**")
        with col3:
            st.markdown("**Scores**")
        with col4:
            if st.button("**Modifier tout**", key=f"modifier_tout"):
                for idee in st.session_state["idees_in_cluster"]:
                    slider_key = f"slider_{idee[0]}"  # génère la clé comme dans la boucle
                    new_score = st.session_state[slider_key]
                    if abs(new_score - idee[2]) > 0.05:
                        rename(idee[0], new_score)
                st.rerun()

    
        for idee in st.session_state["idees_in_cluster"]:

            slider_key = f"slider_{idee[0]}"
            col1, col2, col3, col4,col5 = st.columns([7,1,1,2,3])
            with col1:
                st.write(idee[1]) 
            with col2:
                st.write(idee[3])
            with col3:
                st.write(round(idee[2], 1))
            with col4:
                if st.button("Modifier", key=f"modifier_{idee[0]}"):
                    rename(idee[0], st.session_state[slider_key])
                    st.rerun()
            with col5:
                st.slider(
                    "Score",
                    min_value=1.0,
                    max_value=5.0,
                    value=float(idee[2]),
                    step=0.1,
                    format="%.1f",
                    key=slider_key,
                    label_visibility="collapsed"
                )
                #idee[2] = st.session_state[slider_key]





            


            

if __name__ == "__main__":
    app()