import aiohttp
from main import MAP_APIKEY


async def fetch_json(url):
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            return await response.json()


class Place:
    def __init__(self, name: str, address: str, category: str) -> None:
        self.name = name
        self.address = address
        self.category = category


async def map_search(request):
    BASE_URL = "https://suggest-maps.yandex.ru/v1/suggest"
    apikey = MAP_APIKEY
    lang = "ru"
    results = 4

    try:
        data = await fetch_json(
            f"{BASE_URL}?apikey={apikey}&highlight=0&types=biz&text={request}&results={results}&lang={lang}"
        )
        places_list = []

        for result in data.get("results", []):
            name = result["title"]["text"]
            if " · " in (result["subtitle"]["text"]):
                address = (result["subtitle"]["text"]).split(" · ")[1]
                category = (result["subtitle"]["text"]).split(" · ")[0]
            else:
                address = result["subtitle"]["text"]
                category = ""
            places_list.append(Place(name, address, category))

        return places_list

    except (KeyError, IndexError, aiohttp.ClientError):
        return []
