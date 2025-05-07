import requests
#from .search_menu import Step

BASE_URL = 'https://suggest-maps.yandex.ru/v1/suggest' 

apikey = '03366a1f-b153-4a39-a9ae-e110d49be220' #ключ от яндекс.саджест
text = 'москва' # = Step.search_input  ??
lang = 'ru'

try:
    response = requests.get(f"{BASE_URL}?apikey={apikey}&text={text}&lang={lang}")
except requests.ConnectionError as e:
    print("Ошибка подключения:", e)
except requests.Timeout as e:
    print("Ошибка тайм-аута:", e)
except requests.RequestException as e:
    print("Ошибка запроса:", e)

answer = response.json() 
dict = answer['results'] #для удобства работы с объектом result

print(dict[1]['title']['text'])
print('площадь вашего города составляет ')
print(dict[1]['distance']['text'])

