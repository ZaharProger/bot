from os import environ
from dotenv import load_dotenv, find_dotenv
from argparse import ArgumentParser, BooleanOptionalAction
from utils import get_psql_db_conf, create_db, perform_api_call
from client import TgBotClient


if __name__ == '__main__':
    load_dotenv(find_dotenv('db.env'))
    load_dotenv(find_dotenv('api.env'))

    parser = ArgumentParser()
    parser.add_argument(
        '--model', 
        default='deepseek-v3.1:671b',
        type=str, 
        help="""Provide a generative AI model for bot.\nFull list of available models
        you can get by providing --list attribute"""
    )
    parser.add_argument(
        '--activity', 
        default=0.5,
        type=float, 
        help="Setup the frequency (from 0.0 to 1.0) of bot answers' generation"
    )
    parser.add_argument(
        '--list',
        action=BooleanOptionalAction,
        help='Provide the list of available AI models for bot.'
    )
    args = parser.parse_args()

    if args.list:
        response = perform_api_call(
            f"{environ['OLLAMA_API_BASE_URL']}{environ['OLLAMA_API_LIST_MODELS']}",
            method='get',
            headers={
                'Authorization': f"Bearer {environ['OLLAMA_API_KEY']}"
            }
        )
        if response.is_ok:
            print('\n*--------AVAILABLE MODELS--------*\n')
            response.data['models'].sort(key=lambda model: model['name'])
            for model in response.data['models']:
                print(model['name'])
        else:
            print(response.data)
    else:
        db_conf = get_psql_db_conf()
        create_db(db_conf)

        bot = TgBotClient(environ['BOT_TOKEN'], args.model, args.activity)
        bot.run()
