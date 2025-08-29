import requests
import streamlit as st
from config import API_BASE

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


