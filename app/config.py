import os
from dotenv import load_dotenv

load_dotenv()

API_ID = int(os.environ.get('API_ID', '12345'))
API_HASH = os.environ.get('API_HASH', 'dummy_hash')
SESSION_NAME = os.environ.get('SESSION_NAME', 'presence_test')

BOT_TOKEN = os.environ.get('BOT_TOKEN', '')
ADMIN_CHAT_ID = int(os.environ.get('ADMIN_CHAT_ID', '0'))

TIMEZONE = os.environ.get('TIMEZONE', 'Asia/Kolkata')
DATABASE_PATH = os.environ.get('DATABASE_PATH', 'presence_test.db')
