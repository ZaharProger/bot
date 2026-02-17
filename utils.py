import pyttsx3
import librosa
import soundfile
import requests
from os import environ
from models import *
from constants import ODD_SYMBOLS


def create_db(db_conf: peewee.Database):
    db.initialize(db_conf)
    db_conf.create_tables([Chat, AIModel, ChatBotSettings, ChatMessage], safe=True)


def get_psql_db_conf():
    db_name = environ['POSTGRES_DB']
    db_user = environ['POSTGRES_USER']
    db_password = environ['POSTGRES_PASSWORD']
    db_host = environ['POSTGRES_HOST']
    db_port = environ['POSTGRES_PORT']

    return peewee.PostgresqlDatabase(db_name, user=db_user, 
                                     password=db_password, 
                                     host=db_host, port=db_port)


def convert_text_to_audio(text, pitch_shift_steps, output_filename):
    engine = pyttsx3.init(driverName='nsss')
    
    engine.setProperty('rate', 100)
    for voice in engine.getProperty('voices'):
        if 'ru' in voice.languages[0]:
            engine.setProperty('voice', voice.id)
    
    processed_response = "".join(char for char in text if char not in ODD_SYMBOLS)
    engine.save_to_file(processed_response, output_filename)
    engine.runAndWait()

    audio, sample_rate = librosa.load(output_filename)
    new_audio = librosa.effects.pitch_shift(audio, n_steps=pitch_shift_steps, sr=sample_rate)
    soundfile.write(output_filename, new_audio, samplerate=sample_rate)

def perform_api_call(api_url, method, headers=dict(), body=dict()):
    if method.lower() in ['get', 'delete']:
        api_url = f"{api_url}?" + '&'.join([f"{k}={v}" for k, v in body.items()])
        
    if method.lower() == 'get':  
        response = requests.get(api_url, headers=headers)
    elif method.lower() == 'post':
        response = requests.post(api_url, headers=headers, json=body)
    elif method.lower() == 'put':
        response = requests.put(api_url, headers=headers, json=body)
    elif method.lower() == 'delete':
        response = requests.delete(api_url, headers=headers)
    elif method.lower() == 'patch':
        response = requests.patch(api_url, headers=headers, json=body)
    else:
        response = None

    if response is None:
        api_call_result = ResponseResult(False, 405, dict())
    else:
        api_call_result = ResponseResult(response.ok, response.status_code, response.json())

    return api_call_result
