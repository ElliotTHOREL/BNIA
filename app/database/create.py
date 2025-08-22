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
            FOREIGN KEY (id_document) REFERENCES document(id) ON DELETE CASCADE,
        )
        """)
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS reponse(
            id INT AUTO_INCREMENT PRIMARY KEY,
            id_question INT,
            id_repondant INT,
            reponse TEXT,
            FOREIGN KEY (id_question) REFERENCES question(id) ON DELETE CASCADE,
            FOREIGN KEY (id_repondant) REFERENCES repondant(id) ON DELETE CASCADE
        )
        """)