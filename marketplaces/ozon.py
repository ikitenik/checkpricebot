from selenium import webdriver
from selenium.webdriver.common.by import By
import re
import asyncio
from typing import Tuple

# Открытие браузером странички и считывание данных
async def get_data(url: str) -> Tuple[str]:
    options = webdriver.ChromeOptions()
    options.add_argument(
        "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/105.0.0.0 Safari/537.36")
    options.add_argument("--disable-blink-features=AutomationControlled")
    # options.add_argument("--headless")
    driver = webdriver.Chrome(options=options)
    try:
        driver.get(url)
        await asyncio.sleep(5)
        # html-код страницы
        html_content = driver.page_source
        result = await find_description(html_content)
        return result
    except:
        return ("Нет", "", "")



# Поиск цен и названия в html-коде по регулярным выражениям
async def find_description(html_content: str) -> Tuple:
    # Стирание лишних тегов
    html_content = html_content.replace("&quot;", "")
    html_content = html_content.replace(" ", "")
    # Паттерны для поиска по регулярным выражениям
    patterns = [
        # Цена с картой
        r'data-state\=\"\{isAvailable\:true\,cardPrice\:(.*?)₽',
        # Поиск данных в json-формате
        r'<script type="application/ld\+json">(.*?)</script>',
        # Название продукта
        r'"name":"(.*?)"',
        # Цена на озоне без карты
        r'"price":"(.*?)"'
                ]
    data = html_content
    result: List[str, str, str] = []
    for i in range(4):
        # Для имени и цены без карты мы отдельную берем вырезку из html-кода
        if i > 1:
            data = result[1]
        temp = await regular_expressions(data, patterns[i])
        if temp == "Ошибка":
            return ("Нет", "", "")
        result.append(temp)

    result.pop(1)
    return (result[2], result[0], result[1])


# Универсальный поиск по регулярным выражениям
async def regular_expressions(data, pattern):
    match = re.search(pattern, data)
    if match:
        return match.group(1)
    else:
        return "Ошибка"
