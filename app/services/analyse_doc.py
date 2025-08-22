from app.database.read import get_all_answers
from tools.parser import parse_llm_list_response

async def embed(ma_liste: list[str], client, modele):
    return await client.embeddings.create(
        input=ma_liste,
        model=modele
    )

async def preprocess(text: str, client, modele_llm):
    """On preprocess le texte par LLM pour saisir les informations importantes"""

    prompt_system = """
    Tu es un expert en analyse de documents.
    Ton rôle est d'extraire les informations importantes d'un texte
    pour qu'il soit traité par un système NLP.

    FORMAT ATTENDU :
    - Une liste Python contenant les idées principales du texte,
    résumées en quelques mots chacune.
    - Exemple :
    ["idée 1", "idée 2", "idée 3"]
    """

    prompt_user = f"""
    Texte à traiter :
    {text}"""

    response = await client.chat.completions.create(
        model=modele_llm,
        messages=[
            {"role": "system", "content": prompt_system},
            {"role": "user", "content": prompt_user}
        ],
    )

    return parse_llm_list_response(response.choices[0].message.content)


async def embed_answers(answers: list[str], client, modele_embedding, modele_llm):
    to_embed = []
    for answer in answers:
        if len(answer) < 100:
            to_embed.append(answer)
        else:
            to_embed += await preprocess(answer, client, modele_llm)

    embed_result = await embed(to_embed, client, modele_embedding)
    return embed_result


async def analyse_question(id_document: int, id_question: int, client, modele_llm, modele_embedding):
    answers = get_all_answers(id_document, id_question)
    await embed_answers(answers, client, modele_embedding, modele_llm)