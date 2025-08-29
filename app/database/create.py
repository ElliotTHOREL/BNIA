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

        # Nouvelle structure: table texte_traite
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS texte_traite(
            id INT AUTO_INCREMENT PRIMARY KEY,
            texte_traite TEXT NOT NULL,
            UNIQUE (texte_traite)
        )
        """)

        # Table texte_reponse avec référence vers texte_traite
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS texte_reponse(
            id INT AUTO_INCREMENT PRIMARY KEY,
            id_texte_traite INT,
            texte TEXT NOT NULL,
            FOREIGN KEY (id_texte_traite) REFERENCES texte_traite(id) ON DELETE CASCADE
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

        # Nouvelle structure: table idee_embedded sans id_reponse
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS idee_embedded(
            id INT AUTO_INCREMENT PRIMARY KEY,
            idee_texte TEXT NOT NULL,
            idee_embedded JSON NOT NULL,
            score FLOAT
        )
        """)

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS jointure_idee_texte(
            id_texte_traite INT,
            id_idee INT,
            FOREIGN KEY (id_texte_traite) REFERENCES texte_traite(id) ON DELETE CASCADE,
            FOREIGN KEY (id_idee) REFERENCES idee_embedded(id) ON DELETE CASCADE,
            UNIQUE KEY unique_jointure (id_texte_traite, id_idee)
        )
        """)

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS exigence(
            id INT AUTO_INCREMENT PRIMARY KEY,
            id_question INT,
            FOREIGN KEY (id_question) REFERENCES question(id) ON DELETE CASCADE
        )
        """)

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS jointure_exigence_reponse(
            id INT AUTO_INCREMENT PRIMARY KEY,
            id_exigence INT,
            id_reponse INT,
            FOREIGN KEY (id_exigence) REFERENCES exigence(id) ON DELETE CASCADE,
            FOREIGN KEY (id_reponse) REFERENCES texte_reponse(id) ON DELETE CASCADE
        )
        """)



        cursor.execute("""
        CREATE TABLE IF NOT EXISTS filtration(
            id INT AUTO_INCREMENT PRIMARY KEY
        )
        """)

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS jointure_filtration_exigence(
            id_filtration INT,
            id_exigence INT,
            FOREIGN KEY (id_filtration) REFERENCES filtration(id) ON DELETE CASCADE,
            FOREIGN KEY (id_exigence) REFERENCES exigence(id) ON DELETE CASCADE
        )
        """)

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS jointure_filtration_document(
            id_filtration INT,
            id_document INT,
            FOREIGN KEY (id_filtration) REFERENCES filtration(id) ON DELETE CASCADE,
            FOREIGN KEY (id_document) REFERENCES document(id) ON DELETE CASCADE
        )
        """)





        cursor.execute("""
        CREATE TABLE IF NOT EXISTS clusterisation(
            id INT AUTO_INCREMENT PRIMARY KEY,
            auto_number BOOLEAN,
            nb_clusters INT,
            distance VARCHAR(255),
            id_filtration INT,
            FOREIGN KEY (id_filtration) REFERENCES filtration(id) ON DELETE CASCADE
        )
        """)

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS jointure_clusterisation_question(
            id_clusterisation INT,
            id_question INT,
            FOREIGN KEY (id_clusterisation) REFERENCES clusterisation(id) ON DELETE CASCADE,
            FOREIGN KEY (id_question) REFERENCES question(id) ON DELETE CASCADE
        )
        """)


        cursor.execute("""
        CREATE TABLE IF NOT EXISTS cluster(
            id INT AUTO_INCREMENT PRIMARY KEY,
            id_clusterisation INT,
            texte TEXT,
            taille INT,
            score FLOAT,
            FOREIGN KEY (id_clusterisation) REFERENCES clusterisation(id) ON DELETE CASCADE
        )
        """)

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS jointure_cluster_idees(
            id_cluster INT,
            id_idee INT,
            occurrences INT,
            FOREIGN KEY (id_cluster) REFERENCES cluster(id) ON DELETE CASCADE,
            FOREIGN KEY (id_idee) REFERENCES idee_embedded(id) ON DELETE CASCADE
        )
        """)




        cursor.execute("""CREATE INDEX IF NOT EXISTS idx_reponse_id_question ON reponse (id_question)""")
        cursor.execute("""CREATE INDEX IF NOT EXISTS idx_texte_reponse_id_texte_traite ON texte_reponse (id_texte_traite)""")
        cursor.execute("""CREATE INDEX IF NOT EXISTS idx_jointure_idee_texte_id_texte_traite ON jointure_idee_texte (id_texte_traite)""")
        cursor.execute("""CREATE INDEX IF NOT EXISTS idx_jointure_idee_texte_id_idee ON jointure_idee_texte (id_idee)""")