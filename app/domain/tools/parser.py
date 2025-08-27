import ast
import re
import logging

def parse_llm_list_response(response_text: str) -> list[str]:
    """
    Transforme une réponse LLM contenant une liste Python encadrée par des backticks en vraie liste Python.
    """

    # Supprime les backticks et les espaces superflus
    cleaned = re.sub(r"```(?:python)?", "", response_text, flags=re.IGNORECASE).strip()

    # Couper tout après la première parenthèse fermante ']'
    match = re.search(r"(.*?\])", cleaned, flags=re.DOTALL)
    if match:
        cleaned = match.group(1)

    try:
        # Transformer la chaîne en objet Python
        parsed_list = ast.literal_eval(cleaned)
        if isinstance(parsed_list, list):
            return parsed_list
        else:
            raise ValueError("Le contenu n'est pas une liste")
    except Exception as e:         
        logging.error("--------------------------------")
        logging.error("Erreur lors du parsing :", e)
        logging.error(response_text)
        logging.error(cleaned)

        return []
