from app.domain.tools.parser import parse_llm_list_response

import numpy as np
import openai
import os
import asyncio
from dotenv import load_dotenv
import logging
load_dotenv()

async def embed(ma_liste: list[str], client, modele):
    return await client.embeddings.create(
        input=ma_liste,
        model=modele
    )

async def preprocess_with_llm(text: str, client, modele_llm):
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


    response = await client.chat.completions.create(
        model=modele_llm,
        messages=[
            {"role": "system", "content": prompt_system},
            {"role": "user", "content": prompt_user}
        ],
    )

    return parse_llm_list_response(response.choices[0].message.content)


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

    async def embed(self, client, modele_embedding):
        self.batches.append(self.current_batch)
        self.current_batch = []
        self.current_batch_size = 0

        brute_results = []
        for i, batch in enumerate(self.batches):
            if len(batch) == 0:
                logging.warning("Essai d'embed sur une liste vide")
                print(f"batch {i} est vide")
                continue
            result = await embed(batch, client, modele_embedding)
            brute_results.append(result)
        embed_results = [
            np.array(item.embedding)
            for res in brute_results
            for item in res.data
        ]
        return embed_results #liste d'embeddings "à plat"






async def embed_answers(answers: list[str], client, modele_embedding, modele_llm, limit_batch_size=1300):
    """prend en entrée une liste de réponses texte) 
     renvoie une liste de tuples (indice_segment, texte, embed)"""

    to_embed = To_embed(limit_batch_size)
    liste_segments = []
    for i, answer in enumerate(answers):
        if answer == "" or answer is None:
            segments = []
        elif len(answer) < limit_batch_size: #si la réponse est courte, on la considère comme une seule idée
            segments = [answer]
        else:   #si la réponse est longue, on la découpe en idées
            segments = await preprocess_with_llm(answer, client, modele_llm)

        liste_segments.append(segments)
        to_embed.add_segment(segments) #liste de toutes les idées à embedder

    embed_results = await to_embed.embed(client, modele_embedding)
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

if __name__ == "__main__":
    client = openai.AsyncOpenAI(
        api_key=os.getenv("OPENAI_API_KEY"),
        base_url=os.getenv("OPENAI_API_BASE")
    )
    import asyncio

    async def main():
        to_embed = ["test", "test2", "test3"]
        brute_results = []
        for idee in to_embed:
            brute_results.append((await embed([idee], client, os.getenv("EMBEDDING_MODEL"))))
        embed_results = [np.array(res.data[0].embedding) for res in brute_results]
        print(embed_results)


    asyncio.run(main())