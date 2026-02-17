from abc import abstractmethod, ABC
from random import random
from datetime import datetime
from os import environ
from utils import convert_text_to_audio, perform_api_call
from constants import *
from models import *


class BotService(ABC):
    def __init__(self, api_base_url):
        super().__init__()
        self._api_base_url = api_base_url
        self._offset = 0


    def _get_chat(self, id):
        found_chat, _ = Chat.get_or_create(
            messenger_chat_id=id,
            defaults={
                'messenger_chat_id': id
            }
        )
        return found_chat


    def _get_model(self, name):
        found_model, _ = AIModel.get_or_create(
            name=name,
            defaults={
                'name': name
            }
        )
        return found_model


    def _get_chatbot_settings(self, chat, bot): 
        found_settings, is_created = ChatBotSettings.get_or_create(
            chat=chat,
            defaults={
                'chat': chat
            }
        )
        return found_settings, is_created

    def _update_chatbot_activity(self, settings, activity):
        settings.activity = activity
        settings.save()
    

    def _update_chatbot_model(self, settings, model):
        settings.model = model
        settings.save()
    

    def _save_message_from_chat(self, chat, sender, message, send_datetime):
        ChatMessage.create(
            chat=chat,
            sender=sender,
            text=message,
            send_datetime=send_datetime
        )
    

    # def _create_answer_for_chat(self, response_from_llm):
    #     response_text = response_from_llm
    #     voice_message_filename = None
    #     if random() % 2 != 0:
    #         voice_message_filename = f"{current_settings.chat.messenger_chat_id}.wav"
    #         convert_text_to_audio(response_text, 3, voice_message_filename)

    #     return response_text


    def _clear_chat_messages(self, chat):
        ChatMessage.delete() \
            .where(ChatMessage.chat == chat) \
            .execute()


    def _get_chat_messages(self, chat):
        ordered_messages_from_chat = ChatMessage.select() \
            .where(ChatMessage.chat == chat) \
            .order_by(ChatMessage.send_datetime)
        
        chat_members = []
        messages = []
        for message in ordered_messages_from_chat:
            chat_members.append(message.sender)
            messages.append(f"{message.sender}: {message.text}")
        
        chat_members_str = ','.join(chat_members)
        messages_str = '\n'.join(messages)

        return f"{BOT_PROMPT_DIALOG_MEMBERS}{chat_members_str}{BOT_PROMPT_DIALOG_HEADER}{messages_str}"


    def _get_list_models(self):
        ai_models_response = perform_api_call(
            f"{environ['OLLAMA_API_BASE_URL']}{environ['OLLAMA_API_LIST_MODELS']}",
            method='get',
            headers={
                'Authorization': f"Bearer {environ['OLLAMA_API_KEY']}"
            }
        )
        
        models = []
        if ai_models_response.is_ok:
            models = sorted(ai_models_response.data['models'], key=lambda model: model['name'])
        
        return models


    @abstractmethod
    def run(self):
        pass


    @abstractmethod
    def _process_messages(self):
        pass


    @abstractmethod
    def _generate_answer(self):
        pass


class TgBotService(BotService):
    def __init__(self, bot_token):
        super().__init__(f'{environ['TG_API_BASE_URL']}{bot_token}')


    def _process_messages(self):
        body = {
            'timeout': '10',
            'allowed_updates': '["message", "message_reaction]'
        }
        if self._offset > 0:
            body['offset'] = f'{self._offset}'

        messages_response = perform_api_call(
            f"{self._api_base_url}{environ['TG_API_GET_UPDATES']}", 
            method='get', 
            body=body
        )
            
        if messages_response.is_ok:
            if len(messages_response.data['result']) != 0:
                last_update = messages_response.data['result'][-1]
                self._offset = last_update['update_id'] + 1

            current_settings = None 
            for response_item in messages_response.data['result']:
                available_for_processing = 'message' in response_item.keys() and \
                    "text" in response_item['message'].keys() and \
                    response_item['message']['chat']['type'] != 'private'

                if available_for_processing:
                    if current_settings is None:
                        current_chat = self._get_chat(response_item['message']['chat']['id'])
                        current_settings, is_init = self._get_chatbot_settings(current_chat)

                        if is_init:
                            perform_api_call(
                                f"{self._api_base_url}{environ['TG_API_SEND_MESSAGE']}", 
                                method='post', 
                                body={
                                    'chat_id': current_settings.chat.messenger_chat_id,
                                    'text': BOT_HELP
                                }
                            )

                    if current_settings is not None:
                        message_user = response_item['message']['from']
                        message_user_id = message_user['id']
                        message_text = response_item['message']['text']

                        is_sender_admin = False
                        chat_admins_response = perform_api_call(
                            f"{self._api_base_url}{environ['TG_API_GET_CHAT_ADMINS']}", 
                            method='get', 
                            body={
                                'chat_id': current_settings.chat.messenger_chat_id,
                            }
                        )
                        if chat_admins_response.is_ok:
                            chat_admins_ids = [admin['user']['id'] for admin in \
                                               chat_admins_response.data['result']]
                            is_sender_admin = message_user_id in chat_admins_ids
                        
                        if message_text.startswith('/help'):
                            answer_text = BOT_HELP
                        elif message_text.startswith('/models'):
                            models = [model['name'] for model in self._get_list_models()]
                            answer_text = f"{BOT_MODELS_HEADER}{'\n'.join(models)}"
                        elif message_text.startswith('/model') and is_sender_admin:
                            model_name = message_text.split(' ')
                            if len(model_name) > 1:
                                models = [model['name'] for model in self._get_list_models()]
                                if model_name[1] not in models:
                                    answer_text = BOT_UNKNOWN_MODEL
                                else:
                                    self._update_chatbot_model(current_settings, self._get_model(model_name[1]))
                                    answer_text = BOT_MODEL_UPDATED
                            else:
                                answer_text = BOT_ERROR
                        elif message_text.startswith('/activity') and is_sender_admin:
                            activity = message_text.split(' ')
                            try:
                                float_activity = float(activity[1])
                                if float_activity >= 0 and float_activity <= 1.0:
                                    self._update_chatbot_activity(current_settings, float_activity)
                                    answer_text = BOT_ACTIVITY_UPDATED
                                else:
                                    answer_text = BOT_ERROR
                            except:
                                answer_text = BOT_ERROR 
                        elif message_text.startswith('/'):
                            if is_sender_admin:
                                answer_text = BOT_UNKNOWN_COMMAND
                            else:
                                answer_text = BOT_ACCESS_DENIED
                        else:
                            answer_text = None

                        if answer_text is not None:
                            send_message_response = perform_api_call(
                                f"{self._api_base_url}{environ['TG_API_SEND_MESSAGE']}", 
                                method='post', 
                                body={
                                    'chat_id': current_settings.chat.messenger_chat_id,
                                    'text': answer_text
                                }
                            )
                            if send_message_response.is_ok:
                                send_message_item = send_message_response.data['result']
                                message_send_datetime = datetime.fromtimestamp(send_message_item['date'])
                                sent_message_text = send_message_item['text']
                                message_sender = send_message_item['from']['first_name']
                                if 'last_name' in send_message_item['from'].keys():
                                    message_sender += f" {send_message_item['from']['last_name']}"
                                self._save_message_from_chat(
                                    current_settings.chat, 
                                    message_sender, 
                                    sent_message_text,
                                    message_send_datetime
                                )
                        else:
                            message_send_datetime = datetime.fromtimestamp(response_item['message']['date'])
                            message_sender = message_user['first_name']
                            if 'last_name' in message_user.keys():
                                message_sender += f" {message_user['last_name']}"
                            self._save_message_from_chat(
                                current_settings.chat, 
                                message_sender, 
                                message_text,
                                message_send_datetime
                            )
            
            self._generate_answer(current_settings)
        else:
            print(messages_response.data)
                

    def _generate_answer(self, settings):
        if settings is not None and settings.model is not None and random() < settings.activity:
            llm_response = perform_api_call(
                f"{environ['OLLAMA_API_BASE_URL']}{environ['OLLAMA_API_GENERATE']}",
                method='post',
                headers={
                    'Authorization': f"Bearer {environ['OLLAMA_API_KEY']}"
                },
                body={
                    'model': settings.model.name,
                    'prompt': f"{BOT_PROMPT_TEXT}\n{self._get_chat_messages(settings.chat)}",
                    'stream': False
                }
            )
            if llm_response.is_ok:
                send_message_response = perform_api_call(
                    f"{self._api_base_url}{environ['TG_API_SEND_MESSAGE']}", 
                    method='post', 
                    body={
                        'chat_id': settings.chat.messenger_chat_id,
                        'text': llm_response.data['response']
                    }
                )
                # self._create_answer_for_chat(llm_response.data['response'])
                if send_message_response.is_ok:
                    send_message_item = send_message_response.data['result']
                    message_send_datetime = datetime.fromtimestamp(send_message_item['date'])
                    sent_message_text = send_message_item['text']
                    message_sender = send_message_item['from']['first_name']
                    if 'last_name' in send_message_item['from'].keys():
                        message_sender += f" {send_message_item['from']['last_name']}"
                    self._save_message_from_chat(
                        settings.chat, 
                        message_sender, 
                        sent_message_text,
                        message_send_datetime
                    )
                    self._clear_chat_messages(settings.chat)


    def run(self):
        while True:
            self._process_messages()


class VkBotService(BotService):
    def run():
        ...
