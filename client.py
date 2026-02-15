from abc import abstractmethod, ABC
from api import perform_api_call


class BotClient(ABC):
    def __init__(self):
        super().__init__()
        self._offset = 0
    
    def __update_offset(self, collection, update_id_key):
        response_sorted_by_update_id = sorted(
            collection,
            key=lambda update: update[update_id_key],
            reverse=True)   
                            
        if len(response_sorted_by_update_id) != 0:
            self._offset = response_sorted_by_update_id[0][update_id_key] + 1

    @abstractmethod
    def run(self):
        pass


class TgBotClient(BotClient):
    def __init__(self, bot_token):
        super().__init__()
        self.__api_base_url = f'https://api.telegram.org/bot{bot_token}'

    def run(self):
        while True:
            body = {
                'timeout': '10',
                'allowed_updates': '["message", "message_reaction]'
            }
            if self._offset > 0:
                body['offset'] = f'{self._offset}'

            response = perform_api_call(
                f"{self.__api_base_url}/getUpdates", 
                method='get', 
                body=body)
            
            if response.is_ok:
                self.__update_offset(response.data['result'], 'update_id')
                print(self._offset)
            else:
                print(response.data)


class VkBotClient(BotClient):
    def run():
        pass
