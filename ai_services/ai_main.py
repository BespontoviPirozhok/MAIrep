import aiohttp
import asyncio
from typing import List, Dict, Optional, Union

# Настройки API Yandex GPT
YANDEX_GPT_API_URL = (
    "https://llm.api.cloud.yps.yandex.net/foundationModels/v1/completion"
)
YANDEX_GPT_API_KEY = "ajenld0cb0jtmdvgnkf"
FOLDER_ID = "ajesrbf61a18r6htp4mg"

# System prompts
TRAVEL_SYSTEM_PROMPT = {
    "role": "system",
    "text": (
        "Ты персональный помощник по составлению маршрутов и выбору мест для досуга. "
        "Отвечай профессионально, но дружелюбно. Предлагай четкие маршруты и конкретные "
        "места. Учитывай интересы пользователя, если он их указал."
    ),
}

SUMMARY_SYSTEM_PROMPT = {
    "role": "system",
    "text": (
        "Ты профессиональный помощник для анализа и суммаризации текстов. "
        "Кратко выделяй основные моменты, сохраняя ключевую информацию. "
        "Избегай субъективных оценок и лишних деталей."
    ),
}


async def send_gpt_request(
    messages: List[Dict[str, str]], temperature: float = 0.7
) -> Optional[Union[str, Dict]]:
    """
    Базовый асинхронный запрос к Yandex GPT API

    Args:
        messages: Список сообщений в формате [{"role": "user", "text": "сообщение"}]
        temperature: Параметр креативности ответа (0-1)

    Returns:
        Ответ от API или None при ошибке
    """
    headers = {
        "Authorization": f"Api-Key {YANDEX_GPT_API_KEY}",
        "Content-Type": "application/json",
    }

    payload = {
        "modelUri": f"gpt://{FOLDER_ID}/yandexgpt-latest",
        "completionOptions": {"temperature": temperature, "maxTokens": 2000},
        "messages": messages,
    }

    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                YANDEX_GPT_API_URL, headers=headers, json=payload
            ) as response:
                response.raise_for_status()
                data = await response.json()
                return data
    except Exception as e:
        print(f"Ошибка запроса к Yandex GPT: {e}")
        return None


async def chat(
    message: str,
    context: Optional[List[Dict[str, str]]] = None,
    temperature: float = 0.7,
) -> Optional[str]:
    """
    Общий чат с Yandex GPT

    Args:
        message: Сообщение пользователя
        context: История диалога
        temperature: Креативность ответа (0-1)
    """
    messages = []
    if context:
        messages.extend(context)
    messages.append({"role": "user", "text": message})

    response = await send_gpt_request(messages, temperature)
    if response and "result" in response:
        return response["result"]["alternatives"][0]["message"]["text"]
    return None


async def travel_assistant(
    message: str,
    context: Optional[List[Dict[str, str]]] = None,
    temperature: float = 0.7,
) -> Optional[str]:
    """
    Помощник по маршрутам и досугу

    Args:
        message: Запрос пользователя
        context: История диалога
        temperature: Креативность ответа
    """
    messages = [TRAVEL_SYSTEM_PROMPT]
    if context:
        messages.extend(context)
    messages.append({"role": "user", "text": message})

    response = await send_gpt_request(messages, temperature)
    if response and "result" in response:
        return response["result"]["alternatives"][0]["message"]["text"]
    return None


async def av_comment(
    sum_comms: str,
    context: Optional[List[Dict[str, str]]] = None,
    temperature: float = 0.3,
) -> Optional[str]:
    """
    Суммаризация комментариев

    Args:
        sum_comms: Текст для суммаризации
        context: История диалога
        temperature: Рекомендуется низкий для точности
    """
    messages = [SUMMARY_SYSTEM_PROMPT]
    if context:
        messages.extend(context)
    messages.append(
        {"role": "user", "text": f"Суммируй следующие комментарии:\n{sum_comms}"}
    )

    response = await send_gpt_request(messages, temperature)
    if response and "result" in response:
        return response["result"]["alternatives"][0]["message"]["text"]
    return None


if __name__ == "__main__":
    asyncio.run(chat(input("Введите запрос: ")))
