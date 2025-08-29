from app.domain.tools.parser import parse_llm_list_response

import numpy as np
import openai
import os
import asyncio
from dotenv import load_dotenv
import logging
load_dotenv()



async def embed_with_ai_manager(ma_liste: list[str], ai_manager):
    return await ai_manager.embedding(ma_liste)



async def preprocess_with_ai_manager(text: str, ai_manager):
    """On preprocess le texte par LLM pour saisir les informations importantes"""

    prompt_system = """
    Tu es un expert en analyse de documents.
    Ton rôle est d'extraire les informations importantes d'un texte
    pour qu'il soit traité par un système NLP.

    FORMAT STRICT REQUIS :
    - Retourne uniquement une liste Python valide, rien d'autre.
    - Chaque élément doit être une idée principale résumée en quelques mots.
    - Exemple exact de sortie attendue :
    ["idée 1", "idée 2", "idée 3"]

    Même si le texte ne contient pas d'idée claire, retourne une liste vide : []
    Aucune autre explication ne doit être ajoutée.
    """

    prompt_user = f"""
    Texte à traiter :
    {text}
    """

    messages = [
        {"role": "system", "content": prompt_system},
        {"role": "user", "content": prompt_user}
    ]

    response_content = await ai_manager.LLM_treatment(messages)
    return parse_llm_list_response(response_content)


class To_embed:
    def __init__(self, limit_batch_size: int):
        self.limit_batch_size = limit_batch_size
        self.batches =[]
        self.current_batch = []
        self.current_batch_size = 0

    def add_segment(self, segment: list[str]):
        for answer in segment:
            self.add_answer(answer)
    
    def add_answer(self, answer: str):
        if self.current_batch_size + len(answer) > self.limit_batch_size:
            self.batches.append(self.current_batch)
            self.current_batch = [answer]
            self.current_batch_size = len(answer)
        else:
            self.current_batch.append(answer)
            self.current_batch_size += len(answer)



    async def embed_with_ai_manager(self, ai_manager):
        self.batches.append(self.current_batch)
        self.current_batch = []
        self.current_batch_size = 0

        brute_results = []
        for i, batch in enumerate(self.batches):
            if len(batch) == 0:
                logging.warning("Essai d'embed sur une liste vide")
                print(f"batch {i} est vide")
                continue
            result = await ai_manager.embedding(batch)
            brute_results.append(result)
        embed_results = [
            np.array(item.embedding)
            for res in brute_results
            for item in res.data
        ]
        return embed_results #liste d'embeddings "à plat"



async def process_answer_with_semaphore(answer: str, ai_manager, semaphore):
    async with semaphore:
        return await process_answer(answer, ai_manager)


async def process_answer(answer: str, ai_manager):
    if answer == "" or answer is None:
        return []
    elif len(answer) < 40 :#limit_batch_size: #si la réponse est courte, on la considère comme une seule idée
        return [answer]
    else:   #si la réponse est longue, on la découpe en idées
        return await preprocess_with_ai_manager(answer, ai_manager)

async def embed_answers_with_ai_manager(answers: list[str], ai_manager, limit_batch_size=1300):
    """prend en entrée une liste de réponses texte) 
     renvoie une liste de tuples (indice_segment, texte, embed)"""

    to_embed = To_embed(limit_batch_size)

    print("FEU!")
    semaphore = asyncio.Semaphore(5)
    tasks = [process_answer_with_semaphore(answer, ai_manager, semaphore) for answer in answers]
    liste_segments = await asyncio.gather(*tasks)

    for segments in liste_segments:
        to_embed.add_segment(segments)

    embed_results = await to_embed.embed_with_ai_manager(ai_manager)
    n = len(embed_results)

    indice_idee=0 #indice de l'idée
    
    liste_results=[]
    for indice_reponse, segment in enumerate(liste_segments):
        for text in segment:
            liste_results.append((indice_reponse, text, embed_results[indice_idee]))
            indice_idee += 1

    assert indice_idee == n, "indice_idee != n"

    return liste_results # permet de dire : l'answer k contient :
                        #                       - idée 1 -> embed
                        #                       - idée 2 -> embed
                        #                          ......
                        #                       - idée n -> embed

