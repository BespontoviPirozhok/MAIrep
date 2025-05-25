from dotenv import load_dotenv
import os
import sys

if not load_dotenv():
    print("Отсутствует необходимый .env файл")
    sys.exit(1)

TOKEN = os.getenv("TOKEN")
DB = os.getenv("DATABASE")
MAP_APIKEY = os.getenv("MAP_APIKEY")
YANDEX_GPT_API_KEY = os.getenv("YANDEX_GPT_API_KEY")
FOLDER_ID = os.getenv("FOLDER_ID")
