from os import environ
from dotenv import load_dotenv, find_dotenv
from src.utils import get_psql_db_conf, create_db
from src.services import TgBotService


if __name__ == '__main__':
    load_dotenv(find_dotenv('db.env'))
    load_dotenv(find_dotenv('api.env'))

    db_conf = get_psql_db_conf()
    create_db(db_conf)

    bot = TgBotService(environ['BOT_TOKEN'])
    bot.run()
