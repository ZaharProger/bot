from models import *
from os import environ


def create_db(db_conf: peewee.Database):
    db.initialize(db_conf)
    db_conf.create_tables([Chat, Bot, AIModel, ChatBotSettings, ChatMessage], safe=True)


def get_psql_db_conf():
    db_name = environ['POSTGRES_DB']
    db_user = environ['POSTGRES_USER']
    db_password = environ['POSTGRES_PASSWORD']
    db_host = environ['POSTGRES_HOST']
    db_port = environ['POSTGRES_PORT']

    return peewee.PostgresqlDatabase(db_name, user=db_user, 
                                     password=db_password, 
                                     host=db_host, port=db_port)
