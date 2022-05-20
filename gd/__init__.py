import os
import pickle

from gd.config import Config
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from sqlalchemy import create_engine, exc
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, scoped_session

BOT_TOKEN = Config.BOT_TOKEN
def_chat_id = int(Config.chat_id)
chat_url = Config.chat_url
app_url = Config.app_url
OWNER = Config.owner_id
owner_alias = Config.owner_alias
DB_URL = Config.DB_URL

# Postgresql
def mulaisql() -> scoped_session:
	global DB_AVAIABLE
	engine = create_engine(DB_URL, client_encoding="utf8")
	BASE.metadata.bind = engine
	try:
		BASE.metadata.create_all(engine)
	except exc.OperationalError:
		DB_AVAIABLE = False
		return False
	DB_AVAIABLE = True
	return scoped_session(sessionmaker(bind=engine, autoflush=False))

BASE = declarative_base()
SESSION = mulaisql()

# If modifying these scopes, delete the file token.pickle.
SCOPES = [
    "https://www.googleapis.com/auth/drive",
    "https://www.googleapis.com/auth/drive.metadata"
]

"""Shows basic usage of the Drive v3 API.
Prints the names and ids of the first 10 files the user has access to.
"""
creds = None
# The file token.pickle stores the user's access and refresh tokens, and is
# created automatically when the authorization flow completes for the first
# time.
if os.path.exists('token.pickle'):
	with open('token.pickle', 'rb') as token:
		creds = pickle.load(token)
# If there are no (valid) credentials available, let the user log in.
if not creds or not creds.valid:
	if creds and creds.expired and creds.refresh_token:
		creds.refresh(Request())
	else:
		flow = InstalledAppFlow.from_client_secrets_file(
			'credentials.json', SCOPES)
		creds = flow.run_local_server(port=0)
	# Save the credentials for the next run
	with open('token.pickle', 'wb') as token:
		pickle.dump(creds, token)

gd_service = build('drive', 'v3', credentials=creds)
