import os
import json
import httpx
from dotenv import load_dotenv

load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"

SYSTEM_PROMPT = """
Você é um assistente especializado em filmes e séries.
O usuário vai descrever em linguagem natural o que quer assistir.
Sua tarefa é extrair parâmetros estruturados para uma busca no TMDB.

Retorne APENAS um JSON válido, sem markdown, sem explicações, com esta estrutura:
{
  "media_type": "movie" | "tv" | "all",
  "genre_id": <int ou null>,
  "year_min": <int ou null>,
  "year_max": <int ou null>,
  "min_rating": <float entre 0-10 ou null>,
  "sort_by": "popularity" | "rating" | "year_desc" | "year_asc"
}

Mapeamento de gêneros TMDB mais comuns:
- Ação: 28 (filme) / 10759 (série)
- Aventura: 12
- Animação: 16
- Comédia: 35
- Crime: 80
- Documentário: 99
- Drama: 18
- Fantasia: 14
- Terror/Horror: 27
- Mistério: 9648
- Romance: 10749
- Ficção científica: 878
- Thriller: 53
- Guerra: 10752
- Western: 37

Regras:
- Se o usuário mencionar "filme" ou "filmes", use media_type "movie".
- Se mencionar "série", "séries" ou "show", use media_type "tv".
- Se for ambíguo, use "all".
- Para décadas (ex: "anos 90"), defina year_min e year_max (ex: 1990 e 1999).
- Se mencionar "bem avaliado", "aclamado" ou similar, use min_rating 7.5.
- Padrão de sort_by: use "rating" salvo se o usuário pedir por popularidade ou ano.
- Se não conseguir inferir um campo, use null.
"""


async def extract_search_params(user_query: str) -> dict:
    payload = {
        "model": "llama-3.1-8b-instant",
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": f"Descrição do usuário: {user_query}"}
        ],
        "temperature": 0.2,
        "max_tokens": 256
    }

    async with httpx.AsyncClient() as client:
        response = await client.post(
            GROQ_URL,
            headers={
                "Authorization": f"Bearer {GROQ_API_KEY}",
                "Content-Type": "application/json"
            },
            json=payload,
            timeout=15.0
        )
        response.raise_for_status()
        data = response.json()

    raw_text = data["choices"][0]["message"]["content"].strip()

    # Remove possíveis blocos de markdown se o modelo retornar mesmo assim
    raw_text = raw_text.removeprefix("```json").removeprefix("```").removesuffix("```").strip()

    params = json.loads(raw_text)
    return params
