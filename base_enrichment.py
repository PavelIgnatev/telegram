import json
import aiohttp
from bs4 import BeautifulSoup
import logging
import os
import random
import asyncio
import time

json_files = [f for f in os.listdir("json") if f.endswith(".json")]
if not json_files:
    print("В папке 'json' нет файлов с расширением '.json'.")
    exit()
print("Доступные файлы:")
for i, file_name in enumerate(json_files, start=1):
    print(f"{i}. {file_name}")
selected_file_index = int(input("Введите номер файла из папки json: ")) - 1
file_path = os.path.join("json", json_files[selected_file_index])
proxy_login_password = input("Введите Логин:Пароль от прокси: ")
proxy_http_port = input("Введите HTTP:PORT от прокси: ")
proxy_change_proxy = input("Введите ссылку для смену прокси: ")

# Настройка логгирования
logging.basicConfig(level=logging.INFO, format='[%(asctime)s] [%(levelname)s] %(message)s')
logger = logging.getLogger(__name__)

file_handler = logging.FileHandler('base_enrichment.log')
file_handler.setLevel(logging.INFO)
file_handler.setFormatter(logging.Formatter('[%(asctime)s] [%(levelname)s] %(message)s'))

# Добавление обработчика к логгеру
logger.addHandler(file_handler)

async def enrich_account_description(session, account_name, data):
    try:
        async with session.get(f"https://t.me/{account_name}", proxy=f"http://{proxy_login_password}@{proxy_http_port}") as response:
            html = await response.text()

        soup = BeautifulSoup(html, "html.parser")

        description_element = soup.select_one(".tgme_page_description")
        description = description_element.get_text(strip=True) if description_element else None

        if description and "If you haveTelegram, you can" in description:
            return True, description
        else:
            return False, description

    except Exception as e:
        logger.error(f"Ошибка при выполнении запроса для {account_name}: {str(e)}")
        return True, None

async def process_account_batch(session, account_batch, data):
    tasks = []
    consecutive_count = 0  # Счетчик последовательных повторений фразы
    for account_name in account_batch:
        task = asyncio.create_task(enrich_account_description(session, account_name, data))
        tasks.append(task)

    results = await asyncio.gather(*tasks)

    for (has_telegram_description, description), account_name in zip(results, account_batch):
        data["accounts"][account_name]["description"] = description

        logger.info(f"Описание пользователя {account_name}: {description}")

        if has_telegram_description:
            logger.info(f"Найдено описание пользователя с фразой 'If you haveTelegram, you can': {account_name}")
            consecutive_count += 1
            if consecutive_count >= 10:
                return True  # Прерывание цикла итерации аккаунтов
        else:
            consecutive_count = 0  # Сброс счетчика при отсутствии фразы

    return False



async def main():
    with open(file_path, "r", encoding="utf-8") as file:
        data = json.load(file)

    # Получение массива аккаунтов
    accounts = list(data["accounts"].keys())

    num_accounts = len(accounts)
    batch_size = 50
    num_batches = (num_accounts + batch_size - 1) // batch_size

    batch_index = 0
    while batch_index < num_batches:
        start_index = batch_index * batch_size
        end_index = min(start_index + batch_size, num_accounts)
        account_batch = accounts[start_index:end_index]

        print(batch_index, num_batches)

        async with aiohttp.ClientSession() as session:
            has_telegram_description = await process_account_batch(session, account_batch, data)

            if has_telegram_description:
                logger.info("Одно или несколько описаний содержат фразу 'If you haveTelegram, you can'. "
                            "Выполняется GET-запрос на указанный сайт...")

                async with session.get(proxy_change_proxy) as response:
                    website_content = await response.text()

                logger.info(f"Ответ от сайта: {website_content}")

                time.sleep(10)  # Пауза в 5 секунд
            else:
                batch_index += 1

    with open(file_path, "w", encoding="utf-8") as file:
        json.dump(data, file, indent=2, ensure_ascii=False)

    logger.info("Скрипт успешно завершен.")

# Запуск асинхронной функции
loop = asyncio.get_event_loop()
loop.run_until_complete(main())
