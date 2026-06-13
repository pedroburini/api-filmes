import httpx
import os
from dotenv import load_dotenv
from app.schemas import MovieResponse, SearchResult, StreamingProvider

load_dotenv()

TMDB_API_KEY = os.getenv("TMDB_API_KEY")
OMDB_API_KEY = os.getenv("OMDB_API_KEY")
TMDB_BASE = "https://api.themoviedb.org/3"
OMDB_BASE = "http://www.omdbapi.com"
POSTER_BASE = "https://image.tmdb.org/t/p/w500"
LOGO_BASE = "https://image.tmdb.org/t/p/w92"

async def get_genres() -> dict:
    async with httpx.AsyncClient() as client:
        movie = await client.get(f"{TMDB_BASE}/genre/movie/list", params={"api_key": TMDB_API_KEY, "language": "pt-BR"})
        tv = await client.get(f"{TMDB_BASE}/genre/tv/list", params={"api_key": TMDB_API_KEY, "language": "pt-BR"})
        all_genres = {g["id"]: g["name"] for g in movie.json().get("genres", [])}
        all_genres.update({g["id"]: g["name"] for g in tv.json().get("genres", [])})
        return all_genres

async def get_popular(media_type: str, genre_id: int, year_min: int, year_max: int, min_rating: float, page: int) -> list[SearchResult]:
    async with httpx.AsyncClient() as client:
        results = []
        types = ["movie", "tv"] if media_type == "all" else [media_type]

        for t in types:
            params = {
                "api_key": TMDB_API_KEY,
                "language": "pt-BR",
                "sort_by": "popularity.desc",
                "page": page,
            }
            if genre_id:
                params["with_genres"] = genre_id
            if year_min:
                params["primary_release_date.gte" if t == "movie" else "first_air_date.gte"] = f"{year_min}-01-01"
            if year_max:
                params["primary_release_date.lte" if t == "movie" else "first_air_date.lte"] = f"{year_max}-12-31"
            if min_rating:
                params["vote_average.gte"] = min_rating
                params["vote_count.gte"] = 100

            resp = await client.get(f"{TMDB_BASE}/discover/{t}", params=params)
            data = resp.json()

            for item in data.get("results", []):
                title = item.get("title") or item.get("name")
                date = item.get("release_date") or item.get("first_air_date", "")
                year_val = date[:4] if date else None
                poster = f"{POSTER_BASE}{item['poster_path']}" if item.get("poster_path") else None
                rating = str(round(item.get("vote_average", 0), 1))
                results.append(SearchResult(
                    tmdb_id=item["id"],
                    title=title,
                    year=year_val,
                    poster=poster,
                    media_type=t,
                    tmdb_rating=rating
                ))

        results.sort(key=lambda x: float(x.tmdb_rating or 0), reverse=True)
        return results

async def search_titles(query: str) -> list[SearchResult]:
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{TMDB_BASE}/search/multi",
            params={"api_key": TMDB_API_KEY, "query": query, "language": "pt-BR"}
        )
        data = response.json()
        results = []
        for item in data.get("results", [])[:10]:
            if item.get("media_type") not in ["movie", "tv"]:
                continue
            title = item.get("title") or item.get("name")
            date = item.get("release_date") or item.get("first_air_date", "")
            year = date[:4] if date else None
            poster = f"{POSTER_BASE}{item['poster_path']}" if item.get("poster_path") else None
            rating = str(round(item.get("vote_average", 0), 1))
            results.append(SearchResult(
                tmdb_id=item["id"],
                title=title,
                year=year,
                poster=poster,
                media_type=item["media_type"],
                tmdb_rating=rating
            ))
        return results

async def get_title_details(tmdb_id: int, media_type: str) -> MovieResponse:
    async with httpx.AsyncClient() as client:
        tmdb_resp = await client.get(
            f"{TMDB_BASE}/{media_type}/{tmdb_id}",
            params={
                "api_key": TMDB_API_KEY,
                "language": "pt-BR",
                "append_to_response": "credits,watch/providers,external_ids"
            }
        )
        tmdb = tmdb_resp.json()

        title = tmdb.get("title") or tmdb.get("name")
        date = tmdb.get("release_date") or tmdb.get("first_air_date", "")
        year = date[:4] if date else None
        synopsis = tmdb.get("overview")
        poster = f"{POSTER_BASE}{tmdb['poster_path']}" if tmdb.get("poster_path") else None
        genres = ", ".join([g["name"] for g in tmdb.get("genres", [])])
        tmdb_rating = str(round(tmdb.get("vote_average", 0), 1))

        credits = tmdb.get("credits", {})
        cast_list = [m["name"] for m in credits.get("cast", [])[:5]]
        cast = ", ".join(cast_list)
        director = next(
            (m["name"] for m in credits.get("crew", []) if m["job"] == "Director"), None
        )

        runtime = tmdb.get("runtime")
        runtime_str = f"{runtime} min" if runtime else None

        providers_data = tmdb.get("watch/providers", {}).get("results", {}).get("BR", {})
        streaming = []
        for p in providers_data.get("flatrate", []):
            logo = f"{LOGO_BASE}{p['logo_path']}" if p.get("logo_path") else None
            streaming.append(StreamingProvider(provider_name=p["provider_name"], logo_path=logo))

        imdb_id = tmdb.get("external_ids", {}).get("imdb_id") or tmdb.get("imdb_id")
        imdb_rating = rotten_tomatoes = metacritic = None

        if imdb_id:
            omdb_resp = await client.get(OMDB_BASE, params={"apikey": OMDB_API_KEY, "i": imdb_id})
            omdb = omdb_resp.json()
            imdb_rating = omdb.get("imdbRating")
            for rating in omdb.get("Ratings", []):
                if rating["Source"] == "Rotten Tomatoes":
                    rotten_tomatoes = rating["Value"]
                if rating["Source"] == "Metacritic":
                    metacritic = rating["Value"]

        scores = []
        if imdb_rating and imdb_rating != "N/A":
            scores.append(float(imdb_rating) * 10)
        if rotten_tomatoes and rotten_tomatoes != "N/A":
            scores.append(float(rotten_tomatoes.replace("%", "")))
        if metacritic and metacritic != "N/A":
            scores.append(float(metacritic.split("/")[0]))
        if tmdb_rating and tmdb_rating != "0.0":
            scores.append(float(tmdb_rating) * 10)
        average = round(sum(scores) / len(scores), 1) if scores else None

        return MovieResponse(
            title=title, year=year, synopsis=synopsis, director=director,
            cast=cast, genres=genres, poster=poster, runtime=runtime_str,
            imdb_rating=imdb_rating, rotten_tomatoes=rotten_tomatoes,
            metacritic=metacritic, tmdb_rating=tmdb_rating,
            average_rating=average, streaming=streaming
        )
    