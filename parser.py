# parser.py
from bs4 import BeautifulSoup
import requests
import re
import json


def load_html_from_url(url):
    headers = {"User-Agent": "Mozilla/5.0"}
    response = requests.get(url, headers=headers, verify=False)
    response.raise_for_status()
    return response.text


def parse_itmo_master_program(html):
    soup = BeautifulSoup(html, "lxml")

    result = {}

    # Название программы
    header = soup.find("h1")
    result["name"] = header.text.strip() if header else None

    # Карточки с инфой: форма обучения, язык, стоимость и пр.
    cards = soup.select(".Information_card__rshys")
    for card in cards:
        key_el = card.find("p")
        value_el = card.find(class_="Information_card__text__txwcx")
        if key_el and value_el:
            key = key_el.text.strip().lower()
            value = value_el.text.strip()
            result[key] = value
    # === НОВЫЙ КОД ДЛЯ ИЗВЛЕЧЕНИЯ ПАРТНЕРОВ ===
    # Ищем раздел "партнеры программы" по ID или заголовку
    partners_header = soup.find('h2', id='partners')
    if not partners_header:
        # Альтернативный поиск по тексту
        partners_headers = soup.find_all('h2')
        for h in partners_headers:
            if 'партнеры программы' in h.get_text(strip=True).lower():
                partners_header = h
                break

    partners_list = []
    if partners_header:
        # Находим родительский контейнер с партнерами
        partners_section = partners_header.find_parent('div', class_=re.compile(r'Partners.*'))
        if partners_section:
            # Ищем все карточки партнеров
            partner_cards = partners_section.find_all('div', class_='Partners_partners__card__STOzK')
            for card in partner_cards:
                img = card.find('img', alt='partner image')
                if img:
                    alt_text = img.get('alt', '').strip()
                    src = img.get('src', '').strip()

                    # Пытаемся получить имя партнера из alt или src
                    partner_name = None
                    if alt_text and alt_text != 'partner image':
                        partner_name = alt_text
                    elif src:
                        # Извлекаем имя из пути к изображению
                        # Например, из "/file_storage/images/partners/development/napoleonit.png" -> "napoleonit"
                        match = re.search(r'/([^/]+)\.(?:png|jpg|jpeg|svg)$', src)
                        if match:
                            partner_name = match.group(1)
                            # Делаем имя более читаемым
                            partner_name = partner_name.replace('-', ' ').replace('_', ' ').title()

                    if partner_name:
                        partners_list.append(partner_name)

    # Если не нашли через структуру, ищем по классам напрямую
    if not partners_list:
        partner_images = soup.find_all('img', alt='partner image', src=re.compile(r'/file_storage/images/partners/'))
        for img in partner_images:
            src = img.get('src', '')
            match = re.search(r'/([^/]+)\.(?:png|jpg|jpeg|svg)$', src)
            if match:
                partner_name = match.group(1)
                partner_name = partner_name.replace('-', ' ').replace('_', ' ').title()
                partners_list.append(partner_name)

    # Убираем дубликаты, сохраняя порядок
    seen = set()
    unique_partners = []
    for partner in partners_list:
        if partner not in seen:
            seen.add(partner)
            unique_partners.append(partner)

    result["партнеры"] = unique_partners

    # Менеджер
    manager_block = soup.select_one(".Information_manager__name__ecPmn")
    if manager_block:
        name = manager_block.get_text(separator=" ").strip()
        result["менеджер"] = " ".join(name.split())

        # Соцсети
        socials = soup.select(".Information_socials__link___eN3E")
        result["ссылки"] = {s.text.strip(): s.get("href") for s in socials}

        # Учебный план или направления
        directions = soup.select(".Directions_table__item__206L0")
        result["направления"] = []

        for i, block in enumerate(directions):
            code = block.select_one("p").text.strip()
            name = block.select_one("h5").text.strip()

            # Ищем информацию о количестве мест
            budget_places = None
            contract_places = None
            target_places = None

            # Ищем элементы с информацией о местах
            # Предполагаем, что информация находится рядом с блоком направления
            parent = block.parent if block else None
            if parent:
                # Ищем текстовые узлы или элементы с ключевыми словами
                parent_text = parent.get_text()

                # Используем регулярные выражения для поиска чисел после ключевых слов

                # Ищем бюджетные места
                budget_match = re.search(r'бюджетных\s*(\d+)', parent_text)
                if budget_match:
                    budget_places = int(budget_match.group(1))

                # Ищем контрактные места
                contract_match = re.search(r'контрактных\s*(\d+)', parent_text)
                if contract_match:
                    contract_places = int(contract_match.group(1))

                # Ищем целевые места
                target_match = re.search(r'целевая\s*(\d+)', parent_text)
                if target_match:
                    target_places = int(target_match.group(1))

            direction_info = {
                "code": code,
                "name": name
            }

            # Добавляем информацию о местах, если она найдена
            if budget_places is not None:
                direction_info["бюджетных"] = budget_places
            if contract_places is not None:
                direction_info["контрактных"] = contract_places
            if target_places is not None:
                direction_info["целевая"] = target_places

            result["направления"].append(direction_info)

    planai = {'Обязательные дисциплины. 1 семестр ':
                  ['Воркшоп по созданию продукта на данных / Data Product Development Workshop '],
              'Пул выборных дисциплин. 1 семестр':
                  ['Практика применения машинного обучения', 'Алгоритмы и структуры данных',
                   'Математическая статистика',
                   'Разработка веб-приложений (Python Backend)',
                   'Программирование на С++', 'Введение в МО (Python) и Продвинутое МО (Python)',
                   'Технологии обработки естественного языка', 'Автоматическое машинное обучение ',
                   'Обработка и генерация изображений',
                   'Проектирование и разработка рекомендательных систем (продвинутый уровень)',
                   'Основы глубокого обучения , Продвинутое МО (Python) и Глубокое обучение',
                   'Введение в большие языковые модели (LLM)',
                   'Проектирование систем машинного обучения (ML System Design)', 'Проектирование микросервисов',
                   'Хранение больших данных и Введение в МО (Python)', 'Вычисления на графических процессорах (GPU)',
                   'UNIX/Linux системы', 'Инструменты разработки data-driven решений',
                   'Контейнеризация и оркестрация приложений',
                   'Продуктовые исследования', 'Графические интерфейсы', 'Создание интеллектуальных агентов',
                   'Прикладной анализ временных рядов', 'Процессы и методологии разработки решений на основе ИИ',
                   'Инжиниринг управления данными', 'Бизнес-аналитика для инженеров',
                   'Математика для машинного обучения и анализа данных',
                   'Языки программирования', 'Основы машинного обучения , Инженерные практики в ML и анализе данных',
                   'Дополнительные разделы машинного обучения', 'Базы данных Пул выборных'],
              'Пул выборных дисциплин. 2 семестр':
                  ['Глубокое обучение на практике ',
                   'Воркшоп по прикладному использованию языковых и генеративных моделей',
                   'Глубокие генеративные модели (Deep Generative Models)',
                   'Дополнительные разделы математики и алгоритмов',
                   'Программирование на Python (продвинутый уровень)',
                   'DevOps практики и инструменты',
                   'Технологии и практики MLOps',
                   'Продвинутое МО (Python) и Автоматическая обработка текстов',
                   'Продвинутое МО (Python) и Обработка изображений ',
                   'Прикладная математика и статистика / Applied Math and Statistics ',
                   'Автоматическая обработка текстов и Социальные сети ',
                   'Специальные главы геномики',
                   'Специальные главы биоинформатики ',
                   'Нейросети в химии / Neural Networks in Chemistry ',
                   'Обучение с подкреплением',
                   'Интеллектуальные агенты и большие языковые модели',
                   'Разработка приложений разговорного искусственного интеллекта',
                   'Распознавание и генерация речи',
                   'Технологии обработки естественного языка',
                   'Компьютерное зрение (продвинутый уровень)',
                   'Технологии компьютерного зрения',
                   'Обработка изображений и Компьютерное зрение',
                   'Автоматическая обработка текстов и Обработка изображений',
                   'А/В тестирование',
                   'Информационный поиск', 'Управление данными ', ' Сбор и разметка данных для машинного обучения ',
                   'Проектирование систем машинного обучения (ML System Design) ', ' Безопасность ИИ ',
                   'Управление проектами в Data Science ', ' Продуктовый дизайн и прототипирование AI-решений ',
                   'Бизнес-анализ',
                   'Практики менторства и развития в Data Science ',
                   'Основы построения рекомендательных систем',
                   'Инженерия данных ',
                   'Системы обработки и анализа больших массивов данных',
                   'Управление технологическим продуктом',
                   'Языки программирования для работы с данными',
                   'Машинное обучение ',
                   'Задачи машинного обучения ',
                   'Обработка естественного языка'],
              'Пул выборных дисциплин. 3 семестр': ['Алгоритмы и структуры данных ',
                                                    ' Математическая статистика ',
                                                    ' Прикладной анализ временных рядов ',
                                                    ' Разработка веб-приложений (Python Backend) ',
                                                    ' Программирование на С++ ',
                                                    ' Введение в МО (Python) и Продвинутое МО (Python) ',
                                                    ' Технологии обработки естественного языка ',
                                                    ' Автоматическое машинное обучение ',
                                                    ' Обработка и генерация изображений ',
                                                    ' Проектирование и разработка рекомендательных систем (продвинутый уровень) ',
                                                    ' Глубокое обучение ',
                                                    ' Продвинутое МО (Python) и Глубокое обучение ',
                                                    ' Введение в большие языковые модели (LLM) ',
                                                    ' Мультимодальные генеративные модели искусственного интеллекта ',
                                                    ' Проектирование систем машинного обучения (ML System Design) ',
                                                    ' Проектирование микросервисов ',
                                                    ' Хранение больших данных и Введение в МО (Python)']
              }

    result['учебный план'] = planai

    return result

if __name__ == "__main__":
    url = "https://abit.itmo.ru/program/master/ai"
    html = load_html_from_url(url)
    data = parse_itmo_master_program(html)

    with open("data.json", "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
