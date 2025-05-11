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


async def map(request):
    BASE_URL = "https://suggest-maps.yandex.ru/v1/suggest"
    apikey = MAP_APIKEY
    lang = "ru"
    results = 5

    data = await fetch_json(
        f"{BASE_URL}?apikey={apikey}&text={request}&results={results}&lang={lang}"
    )

    list = []
    for i in range(5):
        name = data["results"][i]["title"]["text"]
        address = data["results"][i]["subtitle"]["text"]
        category = data["results"][i]["tags"]
        code = name + " " + address

        place = Place(name, address, category, code)
        list.append(place)

    print(repr(list))

    return list


asyncio.run(map("Метрополис"))
