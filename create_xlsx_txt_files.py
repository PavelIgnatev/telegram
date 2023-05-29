import json
from datetime import datetime, timedelta
from openpyxl import Workbook
import logging
import re


class User:
    def __init__(self, user_id, first_name, last_name, status, description, full):
        self.user_id = user_id
        self.first_name = first_name
        self.last_name = last_name
        self.status = status
        self.description = description
        self.full = full


def get_user_status(last_online, date_updated):
    if last_online is None:
        return "Неизвестно"

    last_online_datetime = datetime.strptime(last_online, "%Y-%m-%d %H:%M:%S")
    date_updated_datetime = datetime.strptime(date_updated, "%Y-%m-%d %H:%M:%S")

    time_difference = date_updated_datetime - last_online_datetime

    if time_difference <= timedelta(days=1):
        return "Активный"
    elif time_difference <= timedelta(days=3):
        return "Средне активный"
    else:
        return "Неактивный"


def analyze_users(data):
    user_chat_count = {}
    user_message_count = {}

    for user, user_data in data["accounts"].items():
        chats = user_data.get("chats", {})
        user_chat_count[user] = len(chats)
        user_message_count[user] = sum([len(messages) for messages in chats.values()])

    real_users = []

    for user, count in user_chat_count.items():
        if (
            count >= 0
            and user_message_count.get(user, 0) >= 0
            and not has_duplicate_messages(data, user)
        ):
            user_info = User(
                user_id=user,
                first_name=data["accounts"][user].get("first_name"),
                last_name=data["accounts"][user].get("last_name"),
                status=get_user_status(
                    data["accounts"][user].get("last_online"),
                    data["accounts"][user].get("date_updated"),
                ),
                description=data["accounts"][user].get("description"),
                full=data["accounts"][user].get("full_user_info"),
            )

            real_users.append(user_info)

    # Сортировка списка пользователей по статусу
    real_users = sorted(
        real_users,
        key=lambda x: (
            x.status == "Активный",
            x.status == "Средне активный",
            x.status == "Неактивный",
            x.status == "Неизвестно",
        ),
        reverse=True,
    )

    return real_users, user_chat_count, user_message_count


def preprocess_message(message):
    # Удаление пробелов и символов, оставление только кириллицы
    processed_message = re.sub(r"[^\wа-яА-Я]", "", message)
    return processed_message.lower()


def has_duplicate_messages(data, user_id):
    chats = data["accounts"][user_id].get("chats", {})
    messages = []

    for chat_id, chat_messages in chats.items():
        messages.extend(chat_messages)

    unique_messages = set()

    for message in messages:
        processed_message = preprocess_message(message)
        if len(processed_message) >= 20:
            if processed_message not in unique_messages:
                unique_messages.add(processed_message)
            else:
                return True

    return False


def write_to_excel(filename, users, chat_count, message_count):
    workbook = Workbook()
    sheet = workbook.active

    sheet["A1"] = "Идентификатор пользователя"
    sheet["B1"] = "Имя"
    sheet["C1"] = "Фамилия"
    sheet["D1"] = "Статус"
    sheet["E1"] = "Чаты"
    sheet["F1"] = "Сообщения"
    sheet["G1"] = "Описание"
    sheet["K1"] = "Полная информация о пользователе"

    row = 2
    for user in users:
        sheet[f"A{row}"] = user.user_id
        sheet[f"B{row}"] = user.first_name
        sheet[f"C{row}"] = user.last_name
        sheet[f"D{row}"] = user.status
        sheet[f"E{row}"] = chat_count.get(user.user_id, 0)
        sheet[f"F{row}"] = message_count.get(user.user_id, 0)
        sheet[f"G{row}"] = user.description
        sheet[f"K{row}"] = json.dumps(user.full)
        row += 1

    workbook.save(filename)


def write_to_txt(filename, users):
    with open(filename, "w") as file:
        for user in users:
            if user.user_id is not None:
                file.write(user.user_id + "\n")


def main():
    json_filename = input("Введите имя файла JSON, откуда будем получать данные: ")
    txt_filename = input("Введите имя файла для сохранения списка идентификаторов пользователей (txt): ")
    excel_filename = input("Введите имя файла для сохранения информации о пользователях (xlsx): ")

    logging.basicConfig(level=logging.INFO, format='[%(asctime)s] [%(levelname)s] %(message)s')
    logger = logging.getLogger(__name__)

    file_handler = logging.FileHandler('create_xlsx_txt_files.log')
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(logging.Formatter('[%(asctime)s] [%(levelname)s] %(message)s'))

    # Добавление обработчика к логгеру
    logger.addHandler(file_handler)

    logger.info("Начало анализа чата...")

    try:
        with open(json_filename, "r") as file:
            json_data = json.load(file)

        real_users, user_chat_count, user_message_count = analyze_users(json_data)

        write_to_excel(excel_filename, real_users, user_chat_count, user_message_count)
        write_to_txt(txt_filename, real_users)

        logger.info("Информация о пользователях сохранена в файле: %s", excel_filename)
        logger.info("Идентификаторы пользователей сохранены в файле: %s", txt_filename)

    except FileNotFoundError:
        logger.error("Файл не найден: %s", json_filename)
    except Exception as e:
        logger.exception("Возникла ошибка во время анализа чата")

    logger.info("Анализ чата завершен.")


if __name__ == "__main__":
    main()
