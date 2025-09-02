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
    texte = texte.rstrip(string.punctuation + string.whitespace).strip()
    
    return texte
