from app.connection import get_db_cursor


def init_bdd():
    with get_db_cursor() as cursor:
        cursor.execute("""CREATE TABLE IF NOT EXISTS document(
            id INT AUTO_INCREMENT PRIMARY KEY,
            name VARCHAR(255) NOT NULL,
            UNIQUE (name)
        )
        """)


        # Création de la table question
        cursor.execute("""CREATE TABLE IF NOT EXISTS question(
            id INT AUTO_INCREMENT PRIMARY KEY,
            question TEXT NOT NULL,
            type ENUM('opinion','identification') NOT NULL,
            UNIQUE (question)
        )
        """)
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS repondant(
            id INT AUTO_INCREMENT PRIMARY KEY,
            id_document INT,
            num_ds_document INT,
            FOREIGN KEY (id_document) REFERENCES document(id) ON DELETE CASCADE
        )
        """)

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS texte_reponse(
            id INT AUTO_INCREMENT PRIMARY KEY,
            texte TEXT,
        )
        """)

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS reponse(
            id INT AUTO_INCREMENT PRIMARY KEY,
            id_question INT,
            id_repondant INT,
            id_texte_reponse int,
            FOREIGN KEY (id_question) REFERENCES question(id) ON DELETE CASCADE,
            FOREIGN KEY (id_repondant) REFERENCES repondant(id) ON DELETE CASCADE,
            FOREIGN KEY (id_texte_reponse) REFERENCES texte_reponse(id) ON DELETE CASCADE
        )
        """)


        cursor.execute("""
        CREATE TABLE IF NOT EXISTS idee_embedded(
            id INT AUTO_INCREMENT PRIMARY KEY,
            id_reponse INT,
            idee_texte TEXT,
            idee_embed JSON,
            FOREIGN KEY (id_reponse) REFERENCES reponse(id) ON DELETE CASCADE
        )
        """)