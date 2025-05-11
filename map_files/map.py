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
    def __init__(
        self, name: str, address: str, category: str, pretty_result: str
    ) -> None:
        self.name = name
        self.address = address
        self.category = category
        self.pretty_result = pretty_result

    def __repr__(self):
        return self.pretty_result


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
            name = result["title"]["text"]
            address = (result["subtitle"]["text"]).split(" · ")[1]
            category = (result["subtitle"]["text"]).split(" · ")[0]
            pretty_result = f'{category} "{name}", {address}'

            place = Place(name, address, category, pretty_result)
            places_list.append(place)

        # Вывод каждого элемента в отдельной строке
        for place in places_list:
            print(place.pretty_result)
        return places_list

    except (KeyError, IndexError, aiohttp.ClientError):
        return []


asyncio.run(map_search("Общежитие МАИ Башня"))
