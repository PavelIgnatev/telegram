import json
import aiohttp
from bs4 import BeautifulSoup
import logging
import os
import random
import asyncio
import time

file_path = input("Введите путь до файла базы (json): ")

# Настройка логгирования
logging.basicConfig(level=logging.INFO, format='[%(asctime)s] [%(levelname)s] %(message)s')
logger = logging.getLogger(__name__)

file_handler = logging.FileHandler('base_enrichment.log')
file_handler.setLevel(logging.INFO)
file_handler.setFormatter(logging.Formatter('[%(asctime)s] [%(levelname)s] %(message)s'))

# Добавление обработчика к логгеру
logger.addHandler(file_handler)

proxies = [
    {
        "proxy": "http://868bAA:3bLxT6@217.29.62.244:11750",
        "status": "active",
        "rest_time": None
    },
    {
        "proxy": "http://868bAA:3bLxT6@217.29.62.244:11749",
        "status": "active",
        "rest_time": None
    },
    {
        "proxy": "http://868bAA:3bLxT6@217.29.62.244:11748",
        "status": "active",
        "rest_time": None
    },
    {
        "proxy": "http://868bAA:3bLxT6@217.29.62.244:11747",
        "status": "active",
        "rest_time": None
    },
    {
        "proxy": "http://868bAA:3bLxT6@217.29.62.244:11746",
        "status": "active",
        "rest_time": None
    },
    {
        "proxy": "http://868bAA:3bLxT6@217.29.62.244:11745",
        "status": "active",
        "rest_time": None
    },
    {
        "proxy": "http://868bAA:3bLxT6@217.29.62.244:11744",
        "status": "active",
        "rest_time": None
    },
    {
        "proxy": "http://868bAA:3bLxT6@217.29.62.244:11743",
        "status": "active",
        "rest_time": None
    },
    {
        "proxy": "http://868bAA:3bLxT6@217.29.62.244:11742",
        "status": "active",
        "rest_time": None
    },
    {
        "proxy": "http://868bAA:3bLxT6@217.29.62.244:11741",
        "status": "active",
        "rest_time": None
    },
    {
        "proxy": "http://868bAA:3bLxT6@217.29.62.244:11740",
        "status": "active",
        "rest_time": None
    },
    {
        "proxy": "http://868bAA:3bLxT6@217.29.62.244:11739",
        "status": "active",
        "rest_time": None
    },
    {
        "proxy": "http://868bAA:3bLxT6@217.29.62.244:11738",
        "status": "active",
        "rest_time": None
    },
    {
        "proxy": "http://868bAA:3bLxT6@217.29.62.244:11737",
        "status": "active",
        "rest_time": None
    },
    {
        "proxy": "http://868bAA:3bLxT6@217.29.62.244:11736",
        "status": "active",
        "rest_time": None
    },
    {
        "proxy": "http://868bAA:3bLxT6@217.29.62.244:11735",
        "status": "active",
        "rest_time": None
    },
    {
        "proxy": "http://868bAA:3bLxT6@217.29.62.244:11734",
        "status": "active",
        "rest_time": None
    },
    {
        "proxy": "http://868bAA:3bLxT6@217.29.62.244:11733",
        "status": "active",
        "rest_time": None
    },
    {
        "proxy": "http://868bAA:3bLxT6@217.29.53.105:10579",
        "status": "active",
        "rest_time": None
    },
    {
        "proxy": "http://868bAA:3bLxT6@217.29.63.159:10605",
        "status": "active",
        "rest_time": None
    },
    {
        "proxy": "http://X27uf7:D80Azj@217.29.62.244:11730",
        "status": "active",
        "rest_time": None
    }
]

async def enrich_account_description(session, account_name, data, proxy):
    try:
        async with session.get(f"https://t.me/{account_name}", proxy=proxy["proxy"]) as response:
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
        return False, None

async def process_account_batch(session, account_batch, data, proxy):
    tasks = []
    for account_name in account_batch:
        task = asyncio.create_task(enrich_account_description(session, account_name, data, proxy))
        tasks.append(task)

    results = await asyncio.gather(*tasks)

    for (has_telegram_description, description), account_name in zip(results, account_batch):
        data["accounts"][account_name]["description"] = description

        logger.info(f"Описание пользователя {account_name}: {description}")

        if has_telegram_description:
            return True

    return False

def proxy_sleep(proxy):
    proxy["status"] = "rest"
    proxy["rest_time"] = time.time() + 15

def get_active_proxy():
    now = time.time()
    for proxy in proxies:
        if proxy["status"] == "active":
            return proxy
        elif proxy["status"] == "rest" and proxy["rest_time"] <= now:
            proxy["status"] = "active"
            proxy["rest_time"] = None
            return proxy
    return None

async def main():
    with open(file_path, "r", encoding="utf-8") as file:
        data = json.load(file)

    # Получение массива аккаунтов
    accounts = list(data["accounts"].keys())

    num_accounts = len(accounts)
    batch_size = 5
    num_batches = (num_accounts + batch_size - 1) // batch_size

    batch_index = 0
    while batch_index < num_batches:
        start_index = batch_index * batch_size
        end_index = min(start_index + batch_size, num_accounts)
        account_batch = accounts[start_index:end_index]

        proxy = get_active_proxy()
        print(batch_index, num_batches, proxy)
        if proxy is None:
            logger.info("Все прокси отдыхают. Ожидание восстановления прокси...")
            await asyncio.sleep(5)
            continue

        async with aiohttp.ClientSession() as session:
            has_telegram_description = await process_account_batch(session, account_batch, data, proxy)

        if has_telegram_description:
            logger.info("Одно или несколько описаний содержат фразу 'If you haveTelegram, you can'. "
                        "Повторная итерация с новой пачкой...")
            proxy_sleep(proxy)
        else:
            batch_index += 1

    with open(file_path, "w", encoding="utf-8") as file:
        json.dump(data, file, indent=2, ensure_ascii=False)

    logger.info("Скрипт успешно завершен.")

# Запуск асинхронной функции
loop = asyncio.get_event_loop()
loop.run_until_complete(main())
