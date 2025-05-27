import aiohttp
import asyncio
import datetime


class Place_short:
    def __init__(
        self,
        kudago_id: int,
        event_name: str,
        event_time: str,
        description: str,
        place_id: str,
    ) -> None:
        self.kudago_id = kudago_id
        self.event_name = event_name
        self.event_time = event_time
        self.description = description
        self.place_id = place_id


class Place_full:
    def __init__(
        self,
        kudago_id: int,
        event_name: str,
        event_time: str,
        description: str,
        place_id: str,
        event_address: str,
    ) -> None:
        self.kudago_id = kudago_id
        self.event_name = event_name
        self.event_time = event_time
        self.description = description
        self.place_id = place_id
        self.event_address = event_address


def pretty_date(date_str: str) -> str:
    months_ru = [
        "января",
        "февраля",
        "марта",
        "апреля",
        "мая",
        "июня",
        "июля",
        "августа",
        "сентября",
        "октября",
        "ноября",
        "декабря",
    ]
    year, month, day = map(int, date_str.split("-"))

    return f"{day} {months_ru[month-1]} {year} г."


def parse_datetime(dataTime):
    try:
        moscow_tz = datetime.timezone(datetime.timedelta(hours=3))

        start_timestamp = dataTime.get("start")
        if start_timestamp and start_timestamp > 0:
            dt_utc = datetime.datetime.fromtimestamp(
                start_timestamp, tz=datetime.timezone.utc
            )
            dt_moscow = dt_utc.astimezone(moscow_tz)
            date = pretty_date(dt_moscow.strftime("%Y-%m-%d"))
            time = dt_moscow.strftime("%H:%M")
            return f"{date} {time}"

        # Приоритет 2: комбинировать start_date + start_time
        start_date = dataTime.get("start_date")
        start_time = dataTime.get("start_time", 0)

        if start_date and start_date > 0:
            total_timestamp = start_date + start_time
            dt_utc = datetime.datetime.fromtimestamp(
                total_timestamp, tz=datetime.timezone.utc
            )
            date = pretty_date(dt_moscow.strftime("%Y-%m-%d"))
            time = dt_moscow.strftime("%H:%M")
            return f"{date} {time}"
    except:
        return "Неизвестно"


def remove_html_tags(text: str) -> str:
    """Удаляет HTML-теги и символы новой строки через split"""
    cleaned = []
    for fragment in text.split("<"):
        if ">" in fragment:
            _, text_part = fragment.split(">", 1)
            cleaned.append(text_part)
        else:
            cleaned.append(fragment)
    return "".join(cleaned).replace("\n", "")


async def fetch_json(url):
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            return await response.json()


async def search_events_short_data(data):
    event_list = []
    for event_data in data["results"]:
        kudago_id = event_data["id"]
        event_raw_name = event_data["title"]
        event_name = event_raw_name[0].upper() + event_raw_name[1:]
        description = remove_html_tags(event_data["description"])
        dataTime = event_data["daterange"]
        event_time = parse_datetime(dataTime)
        place_id = event_data["place"]["id"] if event_data["place"] else None
        event_info_short = Place_short(
            kudago_id, event_name, event_time, description, place_id
        )
        event_list.append(event_info_short)
    return event_list


async def cities_kudago() -> dict:
    cities = {}
    try:
        data = await fetch_json("https://kudago.com/public-api/v1.4/locations/")
        for item in data:
            if item.get("name") == "Интересные материалы":
                continue
            cities[item.get("name")] = item.get("slug")
        return cities
    except (KeyError, IndexError, aiohttp.ClientError):
        return {}


async def search_kudago(request: str, city: str) -> list:
    BASE_URL = "https://kudago.com/public-api/v1.4/search/"
    lang = "ru"
    expand = ""
    page_size = 5
    full_request = f"{BASE_URL}?q={request}&lang={lang}&expand={expand}&location={city}&ctype=event&page_size={page_size}"

    try:
        data = await fetch_json(full_request)
        return await search_events_short_data(data)
    except (KeyError, IndexError, aiohttp.ClientError):
        return []


async def full_event_data(event_short_data: Place_short):
    place_id = None
    event_address = "Неизвестен"
    if event_short_data.place_id:
        place_id = event_short_data.place_id
        place_data = await fetch_json(
            f"https://kudago.com/public-api/v1.4/places/{place_id}"
        )
        place_name_raw = place_data["title"]
        place_name = place_name_raw[0].upper() + place_name_raw[1:]
        place_adress = place_data["address"]
        event_address = f"{place_name}, {place_adress}"
    return Place_full(
        event_short_data.kudago_id,
        event_short_data.event_name,
        event_short_data.event_time,
        event_short_data.description,
        place_id,
        event_address,
    )
