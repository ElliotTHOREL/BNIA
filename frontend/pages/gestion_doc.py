import streamlit as st
import requests
from config import API_BASE  # Import depuis config.py


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



@st.dialog("Renommer le document")
def show_rename_dialog(doc_id, doc_name):
    st.write(f"Renommer le document **{doc_name}** :")
    
    # Utiliser un formulaire pour une meilleure gestion
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
                else:
                    st.error(f"Erreur {response.status_code} : {response.text}")
                    
            except Exception as e:
                st.error(f"Erreur lors de l'import : {e}")
                







def app():
    st.title("Gestion des documents")

    # --- SECTION 1 : Affichage des documents ---
    st.header("Liste des documents existants")

    try:
        response = requests.get(f"{API_BASE}/document/documents")
        documents = response.json()
    except Exception as e:
        st.error(f"Erreur lors de la récupération des documents : {e}")
        documents = []


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
            if st.button("❌ Supprimer", key=f"delete_{doc_id}"):
                delete_document(doc_id)
                st.rerun()

    if st.button("✨ Importer un nouveau document"):
        show_import_dialog()



    st.markdown("---")
    st.info("💡 Cliquez sur 'Renommer' pour ouvrir le dialog de renommage")

if __name__ == "__main__":
    app()