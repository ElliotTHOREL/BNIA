import requests
import streamlit as st
from config import API_BASE
import numpy as np

def get_possible_answers(id_question):
    url = f"{API_BASE}/document/possible_answers"
    params = {
        "id_question": id_question
    }
    response = requests.get(url, params=params)
    if "possible_answers" not in st.session_state:
        st.session_state["possible_answers"] = {}

    dico_answers={}
    for row in response.json():
        dico_answers[row[1]] = row[0]
    st.session_state["possible_answers"][id_question] = dico_answers


def get_documents():
    try:
        response = requests.get(f"{API_BASE}/document/documents")
        documents = response.json()
    except Exception as e:
        st.error(f"Erreur lors de la récupération des documents : {e}")
        documents = []

    st.session_state["documents"] = documents

def get_questions():
    try:
        response = requests.get(f"{API_BASE}/document/questions")
        questions = response.json()
    except Exception as e:
        st.error(f"Erreur lors de la récupération des questions : {e}")
        questions = []
    st.session_state["questions"] = questions


def get_idees_in_cluster():
    cluster = st.session_state["cluster"]
    id_cluster = cluster[0]
    url = f"{API_BASE}/document/idees_in_cluster"
    params = {
        "id_cluster": id_cluster
    }
    response = requests.get(url, params=params)
    st.session_state["idees_in_cluster"] = response.json()


def get_clusterisation(liste_id_doc, liste_id_question, questions_filtrees, filtres, nb_clusters, distance):
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
    st.session_state["id_clusterisation"] = response.json()["id_clusterisation"]
    st.session_state["id_cluster"] = None