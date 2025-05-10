import aiohttp
import asyncio


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
    apikey = "03366a1f-b153-4a39-a9ae-e110d49be220"
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
