import requests
import logging
from bs4 import BeautifulSoup

# Конфигурация логгеров
logging.basicConfig(level=logging.INFO, format='[%(asctime)s] [%(levelname)s] %(message)s')
logger = logging.getLogger(__name__)

file_handler = logging.FileHandler('get_telegram_links.log')
file_handler.setLevel(logging.INFO)
file_handler.setFormatter(logging.Formatter('[%(asctime)s] [%(levelname)s] %(message)s'))

# Добавление обработчика к логгеру
logger.addHandler(file_handler)

def write_links_to_file(links, file_path):
    with open(file_path, 'w') as file:
        for link in links:
            file.write(link + '\n')

def clear_file(file_path):
    with open(file_path, 'w') as file:
        file.write('')

def get_telegram_links(url, search_word):
    try:
        response = requests.get(url)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, 'html.parser')

        telegram_links = []
        for link in soup.find_all('a'):
            href = link.get('href')
            if href and search_word in href:
                telegram_links.append(href)

        return telegram_links
    except Exception as e:
        logger.error("Произошла ошибка: %s", str(e), exc_info=True)

def main():
    url = input("Введите ссылку на сайт для парсинга ссылок: ")
    search_word = input("Введите часть ссылки, которая обязательно должна присутствовать (рекомендуется t.me): ")
    file_path = input("Введите путь к txt файлу, куда будет произведена выгрузка ссылок: ")

    clear_file(file_path)

    try:
        telegram_links = get_telegram_links(url, search_word)
        write_links_to_file(telegram_links, file_path)
        logger.info("Ссылки успешно записаны в файл: %s", file_path)
    except Exception as e:
        logger.error("Произошла ошибка: %s", str(e), exc_info=True)

if __name__ == '__main__':
    main()
