import re
from fastapi import FastAPI, HTTPException, Query
from bs4 import BeautifulSoup
import httpx
from pydantic import BaseModel
from loguru import logger


class Film(BaseModel):
    title: str
    url: str
    year: str
    genre: str
    description: str


app = FastAPI()

PROXIES = {
    "all://": "socks5://user128948:ukb1ec@185.236.77.18:17732",
    # "all://": "http://user128948:ukb1ec@185.236.77.18:7732",
}


def extract_number(text: str) -> str:
    return re.search(r'\d+', text).group()


async def fetch_movies(query: str, page: int = 1) -> dict | None:
    search_url = f"https://kinogo.at/index.php?do=search"
    async with httpx.AsyncClient(proxies=PROXIES) as client:
        data = {
            "do": "search",
            "subaction": "search",
            "story": query,
            "search_start": page
        }
        response = await client.post(search_url, data=data)
        soup = BeautifulSoup(response.content, 'lxml')

        try:
            total_found = soup.find("div", id="content").find_all("div")[3].text
            total_found = int(extract_number(total_found))
        except IndexError:
            logger.error("Error extracting total found from response")
            return

        films = []
        film_containers = soup.find_all("div", class_="short-container")
        for film_container in film_containers:
            header = film_container.find("div", class_="shortstorytitle").find("h2")
            title = header.text.strip()
            url = header.a["href"]

            body = film_container.find("div", class_="shortimg").find("div", id=True)
            description = body.find_all(string=True, recursive=False)
            description = "".join(description).strip()
            quote = body.find("div", class_="quote").find_all("div", class_="main-item")

            year = extract_number(quote[0].text)

            genre = quote[3].find_all("a")
            genre = [i.text for i in genre]
            genre = ",".join(genre)

            films.append(Film(
                title=title,
                url=url,
                year=year,
                genre=genre,
                description=description
            ))
        return {
            "total_found": total_found,
            "films": films
        }


@app.get("/search", response_model=dict)
async def main(query: str = Query(..., title="Search Query"), page: int = Query(1, ge=1)):
    try:
        movies = await fetch_movies(query, page)
        if not movies:
            logger.info(f"No movies found for query: '{query}', page: {page}")
            raise HTTPException(status_code=404, detail="No movies found.")
        logger.info(f"Search successful for query: {query}, page: {page}")
        return movies
    except httpx.HTTPError as e:
        logger.error("HTTP error occurred: %s", str(e))
        raise HTTPException(status_code=500, detail="Error communicating with the website.")
