import pyttsx3
import requests
import librosa
import soundfile
from dotenv import load_dotenv, find_dotenv
from utils import get_psql_db_conf, create_db




if __name__ == '__main__':
    load_dotenv(find_dotenv('db.env'))
    # load_dotenv(find_dotenv('api.env'))

    db_conf = get_psql_db_conf()
    create_db(db_conf)
