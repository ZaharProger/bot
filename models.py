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
    single_activity = peewee.FloatField(null=False, default=0.5)
    dialog_activity = peewee.FloatField(null=False, default=0.5)
    model = peewee.ForeignKeyField(AIModel, related_name='chatbot_settings', null=True)
    class Meta:
        table_name = 'ChatBotSettings'


@dataclass
class ResponseResult:
    is_ok: bool
    code: int
    data: dict
