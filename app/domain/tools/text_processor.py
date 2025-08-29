import unicodedata
import re
import string

def traiter_texte(texte: str) -> str:
    """
    Traite le texte selon les spécifications:
    - Supprime les accents
    - Met en minuscules
    - Supprime la ponctuation finale
    
    Args:
        texte (str): Le texte à traiter
        
    Returns:
        str: Le texte traité
    """
    if not texte:
        return ""
    
    # Conversion en minuscules
    texte = texte.lower()
    
    # Suppression des accents
    texte = unicodedata.normalize('NFD', texte)
    texte = ''.join(c for c in texte if not unicodedata.combining(c))
    
    # Suppression de la ponctuation finale
    texte = texte.rstrip(string.punctuation + string.whitespace)
    
    return texte

def get_or_create_texte_traite(texte: str, cursor) -> int:
    """
    Récupère l'ID d'un texte traité existant ou en crée un nouveau
    
    Args:
        texte (str): Le texte original
        cursor: Curseur de base de données
        
    Returns:
        int: L'ID du texte traité
    """
    texte_traite_value = traiter_texte(texte)
    
    # Vérifier si le texte traité existe déjà
    cursor.execute(
        "SELECT id FROM texte_traite WHERE texte_traite = %s",
        (texte_traite_value,)
    )
    result = cursor.fetchone()
    
    if result:
        return result[0]
    else:
        # Créer un nouveau texte traité
        cursor.execute(
            "INSERT INTO texte_traite (texte_traite) VALUES (%s)",
            (texte_traite_value,)
        )
        return cursor.lastrowid
