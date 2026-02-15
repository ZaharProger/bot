from abc import abstractmethod, ABC
from random import random
from os import environ
from api import perform_api_call
from utils import convert_text_to_audio
from models import *


class BotClient(ABC):
    def __init__(self, api_base_url):
        super().__init__()
        self._api_base_url = api_base_url
        self._offset = 0
    

    def _update_offset(self, collection, update_id_key):
        response_sorted_by_update_id = sorted(
            collection,
            key=lambda update: update[update_id_key],
            reverse=True
        )   
                            
        if len(response_sorted_by_update_id) != 0:
            self._offset = response_sorted_by_update_id[0][update_id_key] + 1
    

    @db.atomic
    def _attach_chat_to_bot(self, chat_id, bot_id, settings):
        found_chat, is_chat_created = Chat.get_or_create(
            messenger_chat_id=chat_id,
            defaults={
                'messenger_chat_id': chat_id
            }
        )
        if not is_chat_created:
            found_bot, _ = Bot.get_or_create(
                messenger_bot_id=bot_id,
                defaults={
                    'messenger_bot_id': bot_id
                }
            )
            found_model, _ = AIModel.get_or_create(
                name=settings['model'],
                defaults={
                    'name': settings['model']
                }
            )
            ChatBotSettings.create(
                chat=found_chat,
                bot=found_bot,
                activity=settings['activity'],
                model=found_model
            )

        return found_chat
    

    def _save_message_from_chat(self, chat, sender, message, send_datetime):
        ChatMessage.create(
            chat=chat,
            sender=sender,
            text=message,
            send_datetime=send_datetime
        )
    

    def _create_answer_to_chat(self, response_from_llm, chat):
        response_text = response_from_llm
        if random() % 2 != 0:
            voice_message_filename = f"{chat.messenger_chat_id}.wav"
            convert_text_to_audio(response_text, 3, voice_message_filename)

        return response_text


    def _clear_chat_messages(self, chat):
        ChatMessage.delete() \
            .where(ChatMessage.chat == chat) \
            .execute()


    @abstractmethod
    def run(self):
        pass


class TgBotClient(BotClient):
    def __init__(self, bot_token):
        super().__init__(f'{environ['TG_API_BASE_URL']}{bot_token}')


    def run(self):
        while True:
            body = {
                'timeout': '10',
                'allowed_updates': '["message", "message_reaction]'
            }
            if self._offset > 0:
                body['offset'] = f'{self._offset}'

            response = perform_api_call(
                f"{self.__api_base_url}{environ['TG_API_GET_UPDATES']}", 
                method='get', 
                body=body
            )
            
            if response.is_ok:
                self._update_offset(response.data['result'], 'update_id')

                current_chat = self._attach_chat_to_bot('', '', {
                    'model': '',
                    'activity': 0.0
                })
                self._save_message_from_chat(current_chat, '', '', '')
                
                if random() > 0.0:
                    response = perform_api_call(
                        f"{environ['OLLAMA_API_BASE_URL']}{environ['OLLAMA_API_GENERATE']}",
                        method='post',
                        headers={
                            'Authorization': f"Bearer {environ['OLLAMA_API_KEY']}"
                        },
                        body={
                            'model': '',
                            'promt': '',
                            'stream': False
                        }
                    )
                    if response.is_ok:
                        response_from_llm = response.json()['response']
                        self._create_answer_to_chat(response_from_llm, current_chat)
                        self._clear_chat_messages(current_chat)
            else:
                print(response.data)


class VkBotClient(BotClient):
    def run():
        pass
