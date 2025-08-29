import streamlit as st
import requests
from config import API_BASE  # Import depuis config.py
from tools import get_questions, get_documents

st.set_page_config(layout="wide")

def rename_document(doc_id, nouveau_nom):
    try:
        response = requests.post(
            f"{API_BASE}/document/rename_doc",
            params={"id": doc_id, "new_name": nouveau_nom}
        )
        if response.status_code == 200:
            st.success(f"Document {doc_id} renommé en '{nouveau_nom}'")
        else:
            st.error(f"Erreur {response.status_code}: {response.text}")
    except Exception as e:
        st.error(f"Erreur de connexion : {e}")

def delete_document(doc_id):
    try:
        response = requests.delete(f"{API_BASE}/document/delete_one_document", params={"id_document": doc_id})
        if response.status_code == 200:
            st.success(f"Document {doc_id} supprimé")
        else:
            st.error(f"Erreur {response.status_code}: {response.text}")
    except Exception as e:
        st.error(f"Erreur de connexion : {e}")


def fusionner_questions(liste_id_questions, new_question):
    url = f"{API_BASE}/document/merge_questions"
    payload = {
        "liste_id_questions": liste_id_questions,
        "new_question": new_question
    }
    
    headers = {
        "Content-Type": "application/json"
    }
    
    _ = requests.post(url, json=payload, headers=headers)

def supprimer_question(id_question):
    _ = requests.delete(f"{API_BASE}/document/delete_one_question", params={"id_question": id_question})
                

@st.dialog("Renommer le document")
def show_rename_dialog(doc_id, doc_name):
    st.write(f"Renommer le document **{doc_name}** :")
    
    with st.form(key=f"rename_form_{doc_id}"):
        nouveau_nom = st.text_input(
            "Nouveau nom :", 
            value=doc_name,
            key=f"input_{doc_id}"
        )
        
        col1, col2 = st.columns(2)
        
        with col1:
            submit_button = st.form_submit_button("✅ Valider", type="primary")
        
        with col2:
            cancel_button = st.form_submit_button("❌ Annuler")
        
        if submit_button:
            if nouveau_nom.strip() and nouveau_nom != doc_name:
                rename_document(doc_id, nouveau_nom)
                get_documents()
                st.rerun()  # Ferme le dialog et rafraîchit
            elif not nouveau_nom.strip():
                st.error("Le nom ne peut pas être vide")
            else:
                st.info("Aucun changement détecté")
        
        if cancel_button:
            st.rerun()  # Ferme le dialog

@st.dialog("Importer un document")
def show_import_dialog():
    uploaded_file = st.file_uploader("Choisissez un fichier Excel", type=["xlsx", "csv"])

    if uploaded_file is not None:
        if st.button("Importer le document"):
            try:
                # Préparer le fichier pour l'upload
                files = {"file": (uploaded_file.name, uploaded_file, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")}
                
                # Appel de l'API
                response = requests.post(f"{API_BASE}/document/import_excel_complete", files=files)
                
                if response.status_code == 200:
                    result = response.json()
                    st.success(f"Document {result['name']} importé avec succès !")
                    st.session_state["possible_answers"]={}
                    get_documents()
                    st.rerun()
                else:
                    st.error(f"Erreur {response.status_code} : {response.text}")
                    
            except Exception as e:
                st.error(f"Erreur lors de l'import : {e}")
                


@st.dialog("Fusionner des questions")
def show_fusionner_questions_dialog(liste_id_questions):
    st.write(f"Vous souhaitez fusionner {len(liste_id_questions)} questions.")
    with st.form(key=f"fusion_form_{liste_id_questions}"):
        st.write("Donnez un nom à la nouvelle question :")
        col1, col2 = st.columns([2,1])
        with col1:
            new_question = st.text_input(key=f"new_question_{liste_id_questions}", label="Nom", label_visibility="collapsed")
        with col2:
            submit_button = st.form_submit_button("Valider")
            if submit_button:
                fusionner_questions(liste_id_questions, new_question)
                get_questions()
                st.rerun()

        



def app():
    st.title("Gestion des ressources")
    st.divider()

    st.header("Liste des documents existants")

    if "documents" not in st.session_state:
        get_documents()

    documents = st.session_state["documents"]


    # Afficher la liste des documents
    for doc_id, doc_name in documents:
        col1, col2, col3 = st.columns([3, 1, 1])
        
        with col1:
            st.markdown(f"##### 📄 {doc_name}")
        
        with col2:
            # Bouton "Renommer" ouvre le dialog
            if st.button("✏️ Renommer", key=f"modal_{doc_id}"):
                show_rename_dialog(doc_id, doc_name)

        with col3:
            if st.button("❌ Supprimer", key=f"delete_document_{doc_id}"):
                delete_document(doc_id)
                st.session_state["possible_answers"]={}
                get_documents()
                st.rerun()

    if st.button("✨ Importer un nouveau document"):
        show_import_dialog()



    st.divider()
    st.header("Liste des questions")

    if "questions" not in st.session_state:
        get_questions()
    questions = st.session_state["questions"]

    col1, col2, col3, col4 = st.columns([4,2,1,1])
    with col1:
        st.markdown("#### Questions")
    with col2:
        st.markdown("#### Types")
    with col3:
        if st.button("Fusionner"):
            # Récupérer les checkboxes cochées
            questions_a_fusionner = [
                q_id for q_id, _, _ in questions
                if st.session_state.get(f"checkbox_{q_id}", False)
            ]
            if questions_a_fusionner:
                show_fusionner_questions_dialog(questions_a_fusionner)
            else:
                st.warning("Aucune question sélectionnée pour la fusion.")


    for q_id, q_name, q_type in questions:
        col1, col2, col3, col4 = st.columns([4,2,1,1])  
        with col1:
            st.markdown(f"##### {q_name}")
        with col2:
            if st.button(f"{q_type}", key=f"question_{q_id}"):
                url = f"{API_BASE}/document/switch_question_type"
                params = {
                    "id_question": q_id,
                }
                _ = requests.post(url, params=params)
                get_questions()
                st.rerun()
        with col3:
            if f"checkbox_{q_id}" not in st.session_state:
                st.session_state[f"checkbox_{q_id}"] = False
            st.checkbox(f"checkbox_{q_id}", value=st.session_state[f"checkbox_{q_id}"], key=f"checkbox_{q_id}", label_visibility="collapsed")
        with col4:
            if st.button("Supprimer", key=f"delete_question_{q_id}"):
                supprimer_question(q_id)
                get_questions()
                st.rerun()



    

if __name__ == "__main__":
    app()