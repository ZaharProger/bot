import pyttsx3
import librosa
import soundfile
from os import environ
from models import *


ODD_SYMBOLS = ['(', ')', '/',  '\\', '|', '{', '}', 
               '[', ']', ';', '"', '\'', ':', '~', 
               '`', '«', '»']


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
