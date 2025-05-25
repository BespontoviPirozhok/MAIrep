import aiohttp
import asyncio
from typing import List, Dict, Optional
import json
import os

from loaded_dotenv import YANDEX_GPT_API_KEY, FOLDER_ID

YANDEX_GPT_API_URL = "https://llm.api.cloud.yandex.net/foundationModels/v1/completion"

PROMPTS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "promts")


def load_prompt(filename: str) -> Dict[str, str]:
    """Загружает промпт из JSON-файла"""
    path = os.path.join(PROMPTS_DIR, filename)
    if not os.path.exists(path):
        raise FileNotFoundError(f"Prompt file not found: {path}")

    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


async def send_gpt_request(
    messages: List[Dict[str, str]], temperature: float = 0.7
) -> Optional[Dict]:
    """Основная функция отправки запроса к Yandex GPT API"""
    headers = {
        "Authorization": f"Api-Key {YANDEX_GPT_API_KEY}",
        "Content-Type": "application/json",
    }

    payload = {
        "modelUri": f"gpt://{FOLDER_ID}/yandexgpt-lite",
        "completionOptions": {"temperature": temperature, "maxTokens": 2000},
        "messages": messages,
    }

    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                YANDEX_GPT_API_URL, headers=headers, json=payload
            ) as response:

                if response.status != 200:
                    error_text = await response.text()
                    print(f"Ошибка API ({response.status}): {error_text}")
                    return None

                return await response.json()

    except aiohttp.ClientError as e:
        print(f"Ошибка соединения: {str(e)}")
    except Exception as e:
        print(f"Неожиданная ошибка: {str(e)}")

    return None


# Основные функции
async def chat(
    messages_list: list[str],
    temperature: float = 0.7,
) -> Optional[str]:
    """Общий чат с GPT для списка сообщений"""
    chat_promt = load_prompt("chat_promt.json")
    messages = [chat_promt]
    messages.append({"role": "user", "text": "\n".join(messages_list)})

    response = await send_gpt_request(messages, temperature)

    try:
        if response and "result" in response:
            return response["result"]["alternatives"][0]["message"]["text"]
    except (KeyError, IndexError) as e:
        print(f"Ошибка разбора ответа: {e}")

    return None


async def av_comment(
    comments: list[str] = None,
    temperature: float = 0.3,
) -> Optional[str]:
    """Суммаризация текста"""
    summary_prompt = load_prompt("summary.json")
    messages = [summary_prompt]
    messages.append(
        {
            "role": "user",
            "text": f"Суммируй следующие комментарии: {"\n".join(comments)}",
        }
    )

    response = await send_gpt_request(messages, temperature)

    try:
        if response and "result" in response:
            return response["result"]["alternatives"][0]["message"]["text"]
    except (KeyError, IndexError) as e:
        print(f"Ошибка разбора ответа: {e}")

    return None


async def recom(visited_places: List[str]) -> Optional[str]:
    """Рекомендации новых мест на основе посещенных"""

    recommendation_prompt = load_prompt("recommendation.json")

    messages = [
        recommendation_prompt,
        {
            "role": "user",
            "text": f"Я посетил: {', '.join(visited_places)}. Что еще посетить?",
        },
    ]

    response = await send_gpt_request(messages, 0.5)

    try:
        if response and "result" in response:
            return response["result"]["alternatives"][0]["message"]["text"]
    except (KeyError, IndexError) as e:
        print(f"Ошибка разбора: {e}")

    return None


async def describe_places(places_list_txt: str) -> Optional[str]:
    """Рекомендации новых мест на основе посещенных"""

    describe_places_promt = load_prompt("describe_places_promt.json")
    messages = [describe_places_promt, {"role": "user", "text": places_list_txt}]

    response = await send_gpt_request(messages, 0.6)

    try:
        if response and "result" in response:
            return response["result"]["alternatives"][0]["message"]["text"]
    except (KeyError, IndexError) as e:
        print(f"Ошибка разбора: {e}")

    return None


async def you_mean(message: str) -> str:
    """Определяет намерение через LLM классификатор"""
    commands = load_prompt("commands.json")
    messages = [commands, {"role": "user", "text": message}]

    # Отправляем в LLM
    response = await send_gpt_request(messages, temperature=0.2)
    try:
        command = response["result"]["alternatives"][0]["message"]["text"].strip()
        return command
    except:
        return "/chat"
