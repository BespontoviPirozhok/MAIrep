import aiohttp
import asyncio
import os
from dotenv import load_dotenv

load_dotenv()
MAP_APIKEY = os.getenv("MAP_APIKEY")


async def fetch_json(url):
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            return await response.json()


class Place:
    def __init__(self, name: str, address: str, category: str, code: str) -> None:
        self.name = name
        self.address = address
        self.category = category
        self.code = code

    def __repr__(self):
        return self.code


async def map_search(request):
    BASE_URL = "https://suggest-maps.yandex.ru/v1/suggest"
    apikey = MAP_APIKEY
    lang = "ru"
    results = 5

    try:
        data = await fetch_json(
            f"{BASE_URL}?apikey={apikey}&text={request}&results={results}&lang={lang}"
        )

        places_list = []
        for result in data.get("results", []):
            name = f"'{result["title"]["text"]}'"
            address = result["subtitle"]["text"]
            category = result["tags"]
            code = name + " " + address

            place = Place(name, address, category, code)
            places_list.append(place)

        # Вывод каждого элемента в отдельной строке
        for place in places_list:
            print(place.code)
        return places_list

    except (KeyError, IndexError, aiohttp.ClientError):
        return []


asyncio.run(map_search("Верный волоколамское шоссе"))
