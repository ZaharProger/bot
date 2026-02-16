from os import environ
from dotenv import load_dotenv, find_dotenv
from utils import get_psql_db_conf, create_db
from client import TgBotClient


if __name__ == '__main__':
    load_dotenv(find_dotenv('db.env'))
    load_dotenv(find_dotenv('api.env'))

    db_conf = get_psql_db_conf()
    create_db(db_conf)

    bot = TgBotClient(environ['BOT_TOKEN'])
    bot.run()
