from dotenv import load_dotenv
import os

# ТОКЕНЫ, БД и APIKEYS
load_dotenv()
TOKEN = os.getenv("TOKEN")
DB = os.getenv("DATABASE")
MAP_APIKEY = os.getenv("MAP_APIKEY")
YANDEX_GPT_API_KEY = os.getenv("YANDEX_GPT_API_KEY")
FOLDER_ID = os.getenv("FOLDER_ID")
