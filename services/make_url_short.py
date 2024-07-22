import requests
import re
def shorten_url(long_url):
    api_url = "https://api.gclnk.com/links"
    params = {
        'url': long_url
    }
    response = requests.post(api_url, params=params)
    response.raise_for_status()  # Проверка на ошибки HTTP
    # Обработка ответа
    shortened_url = response.text  # Предполагается, что сокращенная ссылка возвращается как текст
    match = re.search(r'"url":"(.*?)"}', shortened_url)
    shortened_url = match.group(1)
    return shortened_url.replace("\\", "")


# Пример использования
long_url = "https://mastergroosha.github.io/aiogram-3-guide/filters-and-middlewares/"
shortened_url = shorten_url(long_url)
print(shortened_url)