# скрипт для парсингов чатов (пользователей и сообщений)
import logging
import asyncio
import json
from telethon import TelegramClient
import datetime
from telethon.tl.types import User, Chat, Channel
from telethon.errors import ChatAdminRequiredError

queryKey = ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j', 'k', 'l', 'm', 'n', 'o', 'p', 'q', 'r', 's', 't', 'u', 'v', 'w', 'x', 'y', 'z']

logging.basicConfig(level=logging.INFO, format='[%(asctime)s] [%(levelname)s] %(message)s')
logger = logging.getLogger(__name__)

file_handler = logging.FileHandler('chat_parser.log')
file_handler.setLevel(logging.INFO)
file_handler.setFormatter(logging.Formatter('[%(asctime)s] [%(levelname)s] %(message)s'))

# Добавление обработчика к логгеру
logger.addHandler(file_handler)

def get_username(entity):
    if hasattr(entity, 'username') and entity.username is not None:
        return entity.username
    else:
        return None

def serialize_participant(participant):
    return {
        "user_id": participant.id,
        "first_name": participant.first_name,
        "last_name": participant.last_name if hasattr(participant, 'last_name') else None,
        "last_online": participant.status.was_online.strftime('%Y-%m-%d %H:%M:%S')
        if participant.status and hasattr(participant.status, 'was_online') else None,
        "scam": participant.scam,
        "fake": participant.fake,
        "premium": participant.premium,
        "lang_code": participant.lang_code,
        "is_self": participant.is_self,
        "deleted": participant.deleted,
        "phone": participant.phone,
        "bot": participant.bot,
        "verified": participant.verified,
        "image": hasattr(participant, 'photo') and participant.photo is not None
    }

def save_user_data(user_data, file_path):
    with open(file_path, 'w') as file:
        json.dump(user_data, file, ensure_ascii=False, indent=4)
    logger.info("Данные успешно сохранены в файл.")
    logger.info("-------------------------------------------------------------------------------")


async def main(api_id, api_hash, session_name, chat_urls_or_usernames, file_path):
    user_data = {"chats": {}, "accounts": {}}
    async with TelegramClient(session_name, api_id, api_hash) as client:
        for chat_url_or_username in chat_urls_or_usernames:
            try:
                chat = await client.get_entity(chat_url_or_username)
                if not chat.megagroup:
                    logger.error(f"Чат {chat_url_or_username} не распаршен, он не является мегагруппой")
                    continue
            except Exception as e:
                logger.error(f"Чат {chat_url_or_username} не распаршен, произошла ошибка. {e}")
                continue

            logger.info(f"Обработка чата: {chat.title}")
            chat_data = {
                "chat_id": chat.id,
                "title": chat.title if hasattr(chat, 'title') else None,
                "last_online": chat.date.strftime('%Y-%m-%d %H:%M:%S') if chat.date and hasattr(chat, 'date') else None
            }
            user_data["chats"][chat_url_or_username] = chat_data

            try:
                total_messages = (await client.get_messages(chat, 1)).total
            except Exception as e:
                logger.error(f"Произошла ошибка при получении сообщений в чате: {chat.title}, {e}")
                continue

            processed_participants = 0
            total_participants = 0

            for letter in queryKey:
                participants = await client.get_participants(chat, search=letter)
                total_participants += len(participants)

                for participant in participants:
                    processed_participants += 1
                    logger.info(f"[{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Обработка участника {processed_participants}/{total_participants}")

                    if not isinstance(participant, Channel) and not getattr(participant, 'bot', False):
                        username = get_username(participant)
                        if username is not None:
                            if username not in user_data["accounts"]:
                                user_data["accounts"][username] = {
                                    "user_id": participant.id,
                                    "first_name": participant.first_name,
                                    "last_name": participant.last_name if hasattr(participant, 'last_name') else None,
                                    "last_online": participant.status.was_online.strftime('%Y-%m-%d %H:%M:%S')
                                    if participant.status and hasattr(participant.status, 'was_online') else None,
                                    "date_updated": datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                                    "chats": {
                                        chat_url_or_username: []
                                    }
                                }
                            else:
                                if chat_url_or_username not in user_data["accounts"][username]["chats"]:
                                    user_data["accounts"][username]["chats"][chat_url_or_username] = []

                            full_user_info = serialize_participant(participant)
                            user_data["accounts"][username]["full_user_info"] = full_user_info

            processed_messages = 0

            async for message in client.iter_messages(chat, limit=10000):
                sender = message.sender
                if sender is not None and not isinstance(sender, Channel) and not getattr(sender, 'bot', False):
                    username = get_username(sender)
                    if username is not None:
                        if username not in user_data["accounts"]:
                            user_data["accounts"][username] = {
                                "user_id": sender.id,
                                "first_name": sender.first_name,
                                "last_name": sender.last_name if hasattr(sender, 'last_name') else None,
                                "last_online": sender.status.was_online.strftime('%Y-%m-%d %H:%M:%S')
                                if sender.status and hasattr(sender.status, 'was_online') else None,
                                "date_updated": datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                                "chats": {
                                    chat_url_or_username: []
                                }
                            }
                        else:
                            if chat_url_or_username not in user_data["accounts"][username]["chats"]:
                                user_data["accounts"][username]["chats"][chat_url_or_username] = []

                        full_user_info = serialize_participant(sender)
                        user_data["accounts"][username]["full_user_info"] = full_user_info

                        processed_messages += 1
                        progress = processed_messages / total_messages * 100
                        logger.info(f"[{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Обработка сообщений: {processed_messages}/{total_messages} ({progress:.2f}%)")

                        if message.text and message.text.strip() != "":
                            user_data["accounts"][username]["chats"][chat_url_or_username].append(message.text)

    save_user_data(user_data, file_path)

api_id = input("Введите api_id: ")
api_hash = input("Введите api_hash: ")
session_name = input("Введите значение сессии: ")
chat_urls_file = input("Введите путь до файла, откуда будут выгружены ссылки на чаты: ")
file_path = input("Введите путь до файла, куда записаны полученные значения после парсинга чатов: ")
chat_urls_or_usernames = []

with open(chat_urls_file, "r") as file:
    for line in file:
        value = line.strip()

        if value and value != "":
            chat_urls_or_usernames.append(value)

logger.info("-------------------------------------------------------------------------------")
logger.info(f"ВВЕДЕННЫЕ ДАННЫЕ ДЛЯ ЗАПУСКА СКРИПТА")
logger.info(f"api_id :{api_id}")
logger.info(f"api_hash :{api_hash}")
logger.info(f"session_name :{session_name}")
logger.info(f"chat_urls_or_usernames :{chat_urls_or_usernames}")
logger.info(f"file_path :{file_path}")


asyncio.run(main(api_id, api_hash, session_name, chat_urls_or_usernames, file_path))
