import peewee
from dataclasses import dataclass


db = peewee.DatabaseProxy()


class BaseModel(peewee.Model):
    id = peewee.BigAutoField()
    class Meta:
        database = db


class Chat(BaseModel):
    messenger_chat_id = peewee.BigIntegerField(null=False)
    class Meta:
        table_name = 'Chats'


class Bot(BaseModel):
    messenger_bot_id = peewee.BigIntegerField(null=False)
    class Meta:
        table_name = 'Bots'


class AIModel(BaseModel):
    name = peewee.CharField(max_length=50, null=False)
    class Meta:
        table_name = 'AIModels'


class ChatMessage(BaseModel):
    chat = peewee.ForeignKeyField(Chat, related_name='messages')
    sender = peewee.CharField(max_length=100, null=False)
    text = peewee.CharField(max_length=10000, null=False)
    send_datetime = peewee.DateTimeField()
    class Meta:
        table_name = 'ChatMessages'


class ChatBotSettings(BaseModel):
    chat = peewee.ForeignKeyField(Chat, related_name='chats')
    bot = peewee.ForeignKeyField(Bot, related_name='bots')
    activity = peewee.FloatField(null=False)
    model = peewee.ForeignKeyField(AIModel, related_name='chatbot_settings')
    class Meta:
        table_name = 'ChatBotSettings'


@dataclass
class ResponseResult:
    is_ok: bool
    code: int
    data: dict
